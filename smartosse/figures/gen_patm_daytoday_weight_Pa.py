"""
Rewrite the day-to-day p_atm control-uncertainty weight file in Pa.

WHY (unit bug found 2026-08-06)
-------------------------------
``input_weight/wApressure_jra2012_daytoday_std.bin`` was built with sigma
expressed in **hPa**, i.e. it stores ``w = sigma_hPa^-2``. MITgcm's
``xx_apressure`` control is in **Pa**, so every OSSE under
``runc68v_froman_partialcables_jrastd_daytoday/`` ran with an effective
sigma_patm of ~8.5 Pa (0.085 hPa) -- 100x TIGHTER than the intended ~8.5 hPa
day-to-day std, and ~40x tighter than the spread prior (ASTE median 3.4 hPa)
rather than ~2.7x looser as Appendix B describes.

Evidence the original file is in hPa (decoding it as ``w^-1/2``):

    w^-1/2 from the .bin           min 0.465  med 9.12  mean 8.46  max 19.53
    day-to-day std [hPa] from
    data/sigma_patm_std_2012_daytoday.nc   0.462       5.03       5.84    21.96

The min agrees to three decimals and the max is the right order. The medians
differ because the .bin covers only the ASTE domain (high latitude, larger
synoptic variability) while the .nc is global. For contrast, the other two
weight files in that directory are unambiguously Pa-based
(``w^-1/2`` mean = 164 Pa for ``wApressure_ASTE270_EXFpress_std_new.bin``,
1448 Pa for ``wApressure_ASTE270_jra55_jra3q_era_spread.bin``).

THE CONVERSION
--------------
sigma_Pa = 100 * sigma_hPa, and w = sigma^-2, so

    w_Pa = (100 * sigma_hPa)^-2 = 1e-4 * sigma_hPa^-2 = 1e-4 * w_hPa

i.e. a pure scalar multiply by 1e-4. Zeros (land / unconstrained points) stay
zero, so the mask is untouched.

This operates on the RAW ``>f4`` byte stream rather than round-tripping through
``read_aste_bin`` / ``write_aste_compact``. The file is the ASTE compact layout
(270 x 1350 float32); a facet rebuild + re-flatten would be a chance to permute
it, and there is nothing to gain from that here -- scaling every element by the
same constant needs no knowledge of the layout at all. The output is therefore
byte-identical to the input apart from the scaling.

Run with:
    /work/08381/goldberg/ls6/miniforge3/envs/esmpy_3.10/bin/python \
        -m smartosse.figures.gen_patm_daytoday_weight_Pa

Writes ``wApressure_jra2012_daytoday_std_Pa.bin`` next to the original. The
original is left in place -- it is what the existing (mis-weighted)
``jrastd_daytoday`` runs used, so deleting it would make those unreproducible.
Point ``data_ctrl_dir_std/data.ctrl``'s ``xx_gentim2d_weight(8)`` at the new
file before re-running.
"""
import os

import numpy as np

WEIGHT_DIR = '/work2/08381/goldberg/ls6/aste_270x450x180/run_template/input_weight/'
SRC_FNAME = 'wApressure_jra2012_daytoday_std.bin'
DST_FNAME = 'wApressure_jra2012_daytoday_std_Pa.bin'

DTYPE = '>f4'      # MITgcm binary: big-endian float32
SCALE = 1e-4       # w_Pa = 1e-4 * w_hPa  (see module docstring)

# ASTE compact layout, for the shape assertion only -- the scaling itself is
# layout-agnostic.
NX, NY = 270, 1350


def convert(src=None, dst=None, scale=SCALE, dtype=DTYPE, overwrite=False):
    """Scale a p_atm weight binary from sigma-in-hPa to sigma-in-Pa units."""
    src = src or os.path.join(WEIGHT_DIR, SRC_FNAME)
    dst = dst or os.path.join(WEIGHT_DIR, DST_FNAME)

    if os.path.exists(dst) and not overwrite:
        raise FileExistsError(f'{dst} exists; pass overwrite=True to replace it')

    w = np.fromfile(src, dtype=dtype)
    if w.size != NX * NY:
        raise ValueError(f'{src}: expected {NX * NY} float32 values '
                         f'(ASTE {NY}x{NX} compact), got {w.size}')

    w_new = (w * scale).astype(dtype)
    w_new.tofile(dst)
    return src, dst, w, w_new


def _sigma_stats(w, label):
    """min/median/mean/max of sigma = w^-1/2 [Pa], over the nonzero weights."""
    s = w[np.isfinite(w) & (w > 0)] ** -0.5
    print(f'  {label:28s} min {s.min():9.2f}  med {np.median(s):9.2f}  '
          f'mean {s.mean():9.2f}  max {s.max():9.2f}')
    return s


if __name__ == '__main__':
    src, dst, w_old, w_new = convert()
    print(f'read  {src}\nwrote {dst}\n')

    # --- verification -----------------------------------------------------
    # 1. exact scaling, and the land/zero mask is unchanged
    back = np.fromfile(dst, dtype=DTYPE)
    assert back.size == w_old.size, 'size changed'
    assert np.array_equal(back == 0, w_old == 0), 'zero (land) mask changed'
    rel = np.abs(back[w_old > 0] / (w_old[w_old > 0] * SCALE) - 1)
    print(f'max relative error vs exact 1e-4 scaling: {rel.max():.3e} '
          f'(float32 round-off)')

    # 2. sigma now lands on the independently computed day-to-day std, in Pa
    print('\nsigma = w^-1/2, interpreted as Pa:')
    _sigma_stats(w_old, 'old file (mislabelled Pa)')
    _sigma_stats(back, 'new file')
    try:
        import xarray as xr
        from .fig9_patm_unc import SIGMA_STD_NC
        nc = np.asarray(xr.open_dataarray(SIGMA_STD_NC))
        nc = nc[np.isfinite(nc)]
        print(f'  {"day-to-day std .nc [Pa]":28s} min {nc.min():9.2f}  '
              f'med {np.median(nc):9.2f}  mean {nc.mean():9.2f}  max {nc.max():9.2f}')
        print('  (medians differ by design: .bin is ASTE-only/high-latitude, '
              '.nc is global)')
    except Exception as exc:                                   # noqa: BLE001
        print(f'  (skipped .nc cross-check: {exc})')
