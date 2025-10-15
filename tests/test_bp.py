import os
import tempfile
import numpy as np
import pytest
import xarray as xr
from unittest import mock
from smartosse.bp import BPReader


# === Helper to create temporary binary data ===
def generate_temp_bp_files(run_dir_root, iternums, nx, dtype=np.dtype('>f4')):
    """
    Creates fake BP binary data files and a mock data.ecco file.
    Files are structured as: run_dir_root/iterXXXX/var.data
    """
    vars_to_create = [
        "bpdatanom_raw",
        "bpdatanom_smooth",
        "bpdifanom_raw",
        "bpdifanom_smooth",
        "m_bpday",
    ]
    data_shape = (2, nx, nx, 5)  # as per your note: 2*30*30*5
    nbytes = np.prod(data_shape) * dtype.itemsize

    for iternum in iternums:
        iter_dir = os.path.join(run_dir_root, f"iter{iternum:04d}")
        os.makedirs(iter_dir, exist_ok=True)

        # Create each variable file
        for var in vars_to_create:
            if var.startswith("m_bp"):
                filename = f"{var}.{iternum:010d}.data"
            else:
                filename = f"{var}.data"

            path = os.path.join(iter_dir, filename)
            arr = np.random.rand(*data_shape).astype(dtype)
            arr.tofile(path)

        # Write a mock data.ecco file
        with open(os.path.join(iter_dir, "data.ecco"), "w") as f:
            f.write(" &GENCOST_NML\n")
            f.write(" gencost_name(1) = 'bpv4-grace'\n")
            f.write(" gencost_errfile(1) = 'sigma.data'\n")
            f.write(" /\n")

        # Create corresponding sigma.data
        sigma = np.ones((nx, nx), dtype=dtype)
        sigma.tofile(os.path.join(iter_dir, "sigma.data"))


@pytest.fixture
def mock_environment(tmp_path):
    """Creates a temporary fake BP directory structure for testing."""
    run_dir = tmp_path / "run"
    iternums = [0, 2]
    nx = 30
    generate_temp_bp_files(run_dir, iternums, nx)
    return run_dir, iternums, nx


# === Mocked read_aste_bin ===
def mock_read_aste_bin(filepath, var_name):
    """Return a small deterministic xarray.DataArray to avoid real binary I/O."""
    data = np.ones((2, 30, 30, 5))
    da = xr.DataArray(data, dims=('k', 'j', 'i', 'dim_0'), name=var_name)
    return da


@mock.patch("smartosse.bp.xu.get_extra_metadata", return_value={"meta": "mocked"})
@mock.patch("smartosse.bp.read_aste_bin", side_effect=mock_read_aste_bin)
def test_bpread_initialization(mock_read, mock_meta, mock_environment):
    run_dir, iternums, nx = mock_environment

    # Instantiate BPReader
    bpr = BPReader(str(run_dir), iternums=iternums, nx=nx)

    # === Verify discovered variables ===
    expected_vars = [
        "bpdatanom_raw",
        "bpdatanom_smooth",
        "bpdifanom_raw",
        "bpdifanom_smooth",
        "m_bpday",
    ]
    assert sorted(bpr.var_names) == sorted(expected_vars)

    # === Verify dataset structure ===
    assert isinstance(bpr.ds, xr.Dataset)
    for v in expected_vars:
        assert v in bpr.ds

    # === Verify metadata was loaded ===
    mock_meta.assert_called_once()

    # === Verify compute_model_anom added variable ===
    assert "m_bpday_anom" in bpr.ds

    # === Check weight and sigma ===
    assert "sigma" in bpr.ds
    assert "weight" in bpr.ds

    # === Ensure __repr__ returns a string ===
    repr_str = repr(bpr)
    assert "BPReader" in repr_str
    assert "run_dir_root" in repr_str

