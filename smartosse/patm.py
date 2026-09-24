import numpy as np
import xarray as xr
import pandas as pd
import re
from pathlib import Path
import matplotlib.pyplot as plt
from .utils import read_float32

def plot_jra_vs_aste_cable_variability(
        jra_std,
        ds_ctrl,
        sensor_args,
        grid_ds,
        fig = None,
        ax = None,
        ):

    if fig is None:
        fig, ax = plt.subplots()

    cable_lons, cable_lats = [grid_ds[coord].isel(sensor_args).values for coord in ['XC', 'YC']]

    # ASTE perturbation: mean and std across sensors
    xx_sensors = ds_ctrl.xx.isel(sensor_args).rename({'dim_0': 'sensor'})
    xx_mean = xx_sensors.mean('sensor')
    xx_std = xx_sensors.std('sensor')
    
    # plot timeseries with error envelope
    xx_mean.plot(c='b', ax=ax)
    ax.fill_between(
        ds_ctrl.time,
        xx_mean - xx_std,
        xx_mean + xx_std,
        color='b',
        alpha=0.3,
        label='ASTE ± std',
        edgecolor=None,
    )
    
    # JRA: mean and std across sensors
    jra_std_sensors = jra_std.sel(
        lon=xr.DataArray(cable_lons),
        lat=xr.DataArray(cable_lats),
        method="nearest"
    ).rename({'dim_0': 'sensor'})
    
    jra_std_sensors_mean = jra_std_sensors.mean('sensor')
    jra_std_sensors_std = jra_std_sensors.std('sensor')
    
    # plot timeseries with error envelope
    jra_std_sensors_mean.plot(c='r', ax=ax)
    ax.fill_between(
        jra_std_sensors_mean.time,
        jra_std_sensors_mean - jra_std_sensors_std,
        jra_std_sensors_mean + jra_std_sensors_std,
        color='r',
        alpha=0.3,
        label='JRA ± std',
        edgecolor=None,
    )
    
    # Aesthetics
    ax.set_xlim([ds_ctrl.time[0].values, ds_ctrl.time[-1].values])
    ax.set_ylabel('[Pa]', fontsize=20)
    ax.set_xlabel('Time', fontsize=20)
    ax.legend(fontsize=12)
    ax.grid()
    ax.set_title('Atm. Pressure Variability along cable', fontsize=20)
    ax.tick_params(axis='both', labelsize=12)
    
    return fig, ax



def load_forcing_generic(
    forcing_dir,
    year,
    fld='pres',
    dataset=None
):
    """
    Load JRA-55, JRA-3Q, or ERA binary data into an xarray DataArray.

    Parameters:
        forcing_dir (str or Path): Path to directory containing forcing files.
        year (int): Year to load.
        fld (str): Field name (e.g., 'pres', 'rain', 'tmp2m_degC', etc.).
        dataset (str): Optional. Either 'jra55', 'jra3q', or 'ERA5'. If None, attempts to infer from path.

    Returns:
        xarray.DataArray: Data with dimensions [time, lat, lon].
    """

    dataset = dataset or re.search(r'(jra55|jra3q|ERA5|erai|era_interim|EIG)', str(forcing_dir)).group(1).lower()
    fname = f"{dataset}_{fld}_{year}"

    if dataset == 'jra55':
        nx, ny = 320, 640
        freq = "3H"

        lon = np.arange(0, 0.5625 * ny, 0.5625)
        lon = (lon + 180) % 360 - 180
        lon = np.sort(lon)

        lat_increments = np.array([
            0.556914, 0.560202, 0.560946, 0.561227, 0.561363,
            0.561440, 0.561487, 0.561518, 0.561539, 0.561554,
            0.561566, 0.561575, 0.561582, 0.561587, 0.561592,
            *([0.561619268965519] * 289),
            0.561592, 0.561587, 0.561582, 0.561575, 0.561566,
            0.561554, 0.561539, 0.561518, 0.561487, 0.561440,
            0.561363, 0.561227, 0.560946, 0.560202, 0.556914
        ])
        lat = np.cumsum(np.insert(lat_increments, 0, -89.57009))

    elif dataset == 'jra3q':
        nx, ny = 480, 960
        freq = "1H"

        lon0 = 0.0
        dlon = 0.375
        lon = np.arange(ny) * dlon + lon0
        lon = (lon + 180) % 360 - 180
        lon = np.sort(lon)

        lat0 = -89.7132492
        lat_increments = np.concatenate([
            [0.3714721, 0.3736626, 0.3741583, 0.3743463, 0.3744372, 0.3744881, 0.3745193, 0.3745399,
             0.3745542, 0.3745645, 0.3745722, 0.3745781, 0.3745827, 0.3745863, 0.3745893],
            np.full(33, 0.374603536309304),
            np.full(383, 0.374609290606391),
            np.full(33, 0.374603536309304),
            [0.3745893, 0.3745863, 0.3745827, 0.3745781, 0.3745722, 0.3745645, 0.3745542,
             0.3745399, 0.3745193, 0.3744881, 0.3744372, 0.3743463, 0.3741583, 0.3736626, 0.3714721]
        ])
        lat = np.cumsum(np.insert(lat_increments, 0, lat0))

    elif dataset == 'ERA5':
        nx, ny = 640, 1280
        freq = "H"

        lon0 = 0.0
        dlon = 0.28125
        lon = np.arange(ny) * dlon + lon0
        lon = (lon + 180) % 360 - 180
        lon = np.sort(lon)

        lat0 = -89.784885
        lat_increments = np.concatenate([
            [0.2786766, 0.2803199, 0.2806917, 0.2808328, 0.2809011, 0.2809392, 0.2809626, 0.2809781,
             0.2809888, 0.2809965, 0.2810023, 0.2810067, 0.2810102, 0.2810129, 0.2810151],
            np.full(33, 0.2810258),
            np.full(543, 0.2810302),
            np.full(33, 0.2810258),
            [0.2810151, 0.2810129, 0.2810102, 0.2810067, 0.2810023, 0.2809965, 0.2809888, 0.2809781,
             0.2809626, 0.2809392, 0.2809011, 0.2808328, 0.2806917, 0.2803199, 0.2786766]
        ])
        lat = np.cumsum(np.insert(lat_increments, 0, lat0))

    elif dataset.lower() in ['erai', 'era_interim', 'era-interim', 'eig']:
        nx, ny = 256, 512
        freq = "6H"

        # Regular lon grid
        lon0 = 0.0
        dlon = 360.0 / ny   # 0.703125
        lon = np.arange(ny) * dlon + lon0
        lon = (lon + 180) % 360 - 180
        lon = np.sort(lon)

        # Regular lat grid
        dlat = 180.0 / nx   # 0.703125
        lat = np.linspace(-90 + dlat/2, 90 - dlat/2, nx)

    else:
        raise ValueError(f"Unsupported dataset type: {dataset}")

    # Read raw binary data
    fpath = Path(forcing_dir) / fname
    raw = read_float32(fpath)
    nt = len(raw) // (nx * ny)
    data = raw.reshape(nt, nx, ny)

    # Time dimension
    time = pd.date_range(start=f"{year}-01-01", periods=nt, freq=freq)

    return xr.DataArray(
        data,
        dims=["time", "lat", "lon"],
        coords={"time": time, "lat": lat, "lon": lon},
        name=f"{dataset}_{fld}"
    )

