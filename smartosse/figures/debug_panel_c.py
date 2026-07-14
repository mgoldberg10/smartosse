# Paste-able Jupyter snippet for iterating on Fig. 9 panel (c) ONLY --
# skips make_fig9() entirely (maps + panel (d) + relcon loads), so each
# styling tweak is a cheap re-plot, not a full-figure rebuild.
#
# Usage: paste CELL 1 once per kernel session (it's the only part that
# touches disk). Then paste CELL 2 as its own cell and re-run *that one*
# after every edit to fig9_patm_unc.py -- %autoreload picks up the change,
# nothing above needs to re-run.

# ============================== CELL 1 (run once) ==============================
from smartosse import *
from smartosse.figures.fig9_patm_unc import *
import matplotlib.pyplot as plt

%load_ext autoreload
%autoreload 2

ds = open_astedataset()
sigma_spread = load_sigma_patm_spread()           # ASTE grid -- the only sigma panel (c) needs
row2_data = load_row2_data(ds, sigma_spread)       # the actual disk reads (2 runs x 4 cables)

# ============================== CELL 2 (re-run this after every edit) ==========
# figsize approximates ax_c's real footprint inside make_fig9()'s (16,13) 2x2
# gridspec (height_ratios=[1.5,1], row2 wspace=0.3) -- close enough that font
# sizes/legend proportions read the same as they will in the full figure.
fig, ax_c = plt.subplots(figsize=(7.5, 5.2))

plot_patm_adjustment_combined(ax_c, row2_data, ylim=(-1, 3), label_fontsize=18, min_label_gap=0.3,
                               label_y_offsets={'labsea': -0.2})
add_panel_label(ax_c, 'c', fontsize=26, x=0.02, y=0.95)
ax_c.legend(handles=_row2_legend_handles(), fontsize=13, frameon=False,
            loc='upper left', bbox_to_anchor=(0.13, 1.0), ncol=4, columnspacing=1.2, handlelength=1.8)

fig
