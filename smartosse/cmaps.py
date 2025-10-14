# https://pyhogs.github.io/colormap-examples.html
import cmocean
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

class Colormaps:
    def __init__(self, num_colors=11):
        self.num_colors = num_colors

    def truncate(self, cmap, minval=0.0, maxval=1.0, n=256, name='truncated'):
        """Return a truncated version of a colormap."""
        new_colors = cmap(np.linspace(minval, maxval, n))
        return LinearSegmentedColormap.from_list(name, new_colors)

    def custom_div_cmap(self, template_cmap=cmocean.cm.balance, name='custom_div_cmap'):
        """Create a diverging colormap with white in the center from a template."""
        sampled_colors = [template_cmap(i) for i in np.linspace(0, 1, self.num_colors)]
        mid_idx = self.num_colors // 2
        sampled_colors[mid_idx] = (1, 1, 1, 1)  # force white center
        return LinearSegmentedColormap.from_list(name, sampled_colors, N=self.num_colors)

    def gwp_div_cmap(self):
        """Green-white-purple diverging colormap."""
        colors = [
            (0, 0.5, 0),       # Dark Green
            (0.3, 0.7, 0.3),   # Light Green
            (1, 1, 1),         # White
            (0.7, 0.5, 0.8),   # Light Purple
            (0.4, 0, 0.6)      # Dark Purple
        ]
        base = LinearSegmentedColormap.from_list("gwp_base", colors)
        return self.custom_div_cmap(template_cmap=base, name='gwp_div_cmap')

    def grace_cmap(self):
        """GRACE-style scientific colormap."""
        colors = [
            "#ffffff", "#d1d8fa", "#acb9f8", "#849afe", "#014be6", "#004bb0",
            "#01ab5d", "#00c439", "#a7e100", "#f9f903", "#fcc800", "#ff9603",
            "#ff5c02", "#fb0000", "#fd0000", "#940000"
        ]
        return LinearSegmentedColormap.from_list('grace_cmap', colors)

    def rainbow_cmap(self):
        """Custom rainbow colormap."""
        colors = [
            '#0D3791', '#0D50AA', '#048BCE', '#00B5C5', '#A2D050',
            '#FFFF00', '#FFAE2E', '#FF3018', '#BE2519'
        ]
        return LinearSegmentedColormap.from_list('rainbow_cmap', colors)

    def rainbow_cmap_alt(self):
        """Custom rainbow colormap."""
        colors = [
            '#0100d2', '#0036f0', '#026ca3', '#3b954c', '#67ae10',
            '#abc01b', '#f5c826', '#fd9f13', '#fe6f02', '#f52a01',
            '#ca1c00','#a30700'
        ]
        return LinearSegmentedColormap.from_list('rainbow_cmap', colors)
