"""``get_llc_grid`` and ``UEVNfromUXVY``, vendored from ``ecco_v4_py``.

Why vendored instead of imported: these are the only two ``ecco_v4_py``
functions this package uses, but ``import ecco_v4_py`` (package ``__init__``)
eagerly pulls in cartopy, matplotlib, shapely, pyproj and scipy along with it
-- packages the data-extraction path (``gen_*.py`` cache builders, run on pfe
next to the model output) has no other reason to need. Both functions
themselves depend on nothing but numpy, xarray and xgcm (light: xarray, dask,
numpy, future -- see ``environment-extract.yml``), so vendoring them removes
the single heaviest, hardest-to-install dependency from that path. See
ROADMAP.md §4b.

Copied from ``ecco_v4_py`` 1.6.0's ``ecco_utils.py`` (``get_llc_grid``) and
``vector_calc.py`` (``UEVNfromUXVY``), with deliberate deviations for xgcm
>=0.8's renamed kwargs (found and fixed 2026-09-24 by actually running this
against real grid data on pfe with xgcm 0.10.1, not just imported -- same
behavior, current API):

- ``xgcm.Grid(..., padding='fill')`` instead of the removed ``periodic=False``
  (``ValueError: The periodic argument has been removed``).
- ``grid.interp_2d_vector(..., padding='fill')`` instead of ``boundary='fill'``
  (``ValueError: Argument 'boundary' has been renamed to 'padding'``).

Source: https://github.com/ECCO-GROUP/ECCOv4-py
License: MIT (Copyright 2018 Ian Fenty), reproduced below per its terms.

    Permission is hereby granted, free of charge, to any person obtaining a
    copy of this software and associated documentation files (the
    "Software"), to deal in the Software without restriction, including
    without limitation the rights to use, copy, modify, merge, publish,
    distribute, sublicense, and/or sell copies of the Software, and to
    permit persons to whom the Software is furnished to do so, subject to
    the following conditions:

    The above copyright notice and this permission notice shall be included
    in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
    OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
    MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
    CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
    TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
    SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
import xgcm


def get_llc_grid(ds, domain='global'):
    """
    Define xgcm Grid object for the LLC grid
    See example usage in the xgcm documentation:
    https://xgcm.readthedocs.io/en/latest/example_eccov4.html#Spatially-Integrated-Heat-Content-Anomaly

    Parameters
    ----------
    ds : xarray Dataset
        formed from LLC90 grid, must have the basic coordinates:
        i,j,i_g,j_g,k,k_l,k_u,k_p1

    Returns
    -------
    grid : xgcm Grid object
        defines horizontal connections between LLC tiles

    """

    if 'domain' in ds.attrs:
        domain = ds.attrs['domain']

    if domain == 'global':
        # Establish grid topology
        tile_connections = {'tile':  {
                0: {'X': ((12, 'Y', False), (3, 'X', False)),
                    'Y': (None, (1, 'Y', False))},
                1: {'X': ((11, 'Y', False), (4, 'X', False)),
                    'Y': ((0, 'Y', False), (2, 'Y', False))},
                2: {'X': ((10, 'Y', False), (5, 'X', False)),
                    'Y': ((1, 'Y', False), (6, 'X', False))},
                3: {'X': ((0, 'X', False), (9, 'Y', False)),
                    'Y': (None, (4, 'Y', False))},
                4: {'X': ((1, 'X', False), (8, 'Y', False)),
                    'Y': ((3, 'Y', False), (5, 'Y', False))},
                5: {'X': ((2, 'X', False), (7, 'Y', False)),
                    'Y': ((4, 'Y', False), (6, 'Y', False))},
                6: {'X': ((2, 'Y', False), (7, 'X', False)),
                    'Y': ((5, 'Y', False), (10, 'X', False))},
                7: {'X': ((6, 'X', False), (8, 'X', False)),
                    'Y': ((5, 'X', False), (10, 'Y', False))},
                8: {'X': ((7, 'X', False), (9, 'X', False)),
                    'Y': ((4, 'X', False), (11, 'Y', False))},
                9: {'X': ((8, 'X', False), None),
                    'Y': ((3, 'X', False), (12, 'Y', False))},
                10: {'X': ((6, 'Y', False), (11, 'X', False)),
                     'Y': ((7, 'Y', False), (2, 'X', False))},
                11: {'X': ((10, 'X', False), (12, 'X', False)),
                     'Y': ((8, 'Y', False), (1, 'X', False))},
                12: {'X': ((11, 'X', False), None),
                     'Y': ((9, 'Y', False), (0, 'X', False))}
        }}

        grid = xgcm.Grid(ds,
                padding='fill',
                face_connections=tile_connections
        )
    elif domain == 'aste':
        tile_connections = {'tile':{
                    0:{'X':((5,'Y',False),None),
                       'Y':(None,(1,'Y',False))},
                    1:{'X':((4,'Y',False),None),
                       'Y':((0,'Y',False),(2,'X',False))},
                    2:{'X':((1,'Y',False),(3,'X',False)),
                       'Y':(None,(4,'X',False))},
                    3:{'X':((2,'X',False),None),
                       'Y':(None,None)},
                    4:{'X':((2,'Y',False),(5,'X',False)),
                       'Y':(None,(1,'X',False))},
                    5:{'X':((4,'X',False),None),
                       'Y':(None,(0,'X',False))}
                   }}
        grid = xgcm.Grid(ds, padding='fill', face_connections=tile_connections)
    else:
        raise TypeError(f'Domain {domain} not recognized')

    return grid


def UEVNfromUXVY(xfld, yfld, coords, grid=None):
    """Compute east, north facing vector field components from x, y components
    by interpolating to cell centers and rotating by grid cell angle

    Note: this mirrors gcmfaces_calc/calc_UEVNfromUXVY.m

    Parameters
    ----------
    xfld, yfld : xarray DataArray
        fields living on west and south grid cell edges, e.g. UVELMASS and VVELMASS
    coords : xarray Dataset
        must contain CS (cosine of grid orientation) and
        SN (sine of grid orientation)
    grid : xgcm Grid object, optional
        see get_llc_grid and xgcm.Grid

    Returns
    -------
    u_east, v_north : xarray DataArray
        eastward and northward components of input vector field at
        grid cell center/tracer points
    """

    # Check to make sure 'CS' and 'SN' are in coords
    # before doing calculation
    required_fields = ['CS','SN']
    for var in required_fields:
        if var not in coords.variables:
            raise KeyError('Could not find %s in coords Dataset' % var)

    # If no grid, establish it
    if grid is None:
        grid = get_llc_grid(coords)

    # First, interpolate velocity fields from cell edges to cell centers
    velc = grid.interp_2d_vector({'X': xfld, 'Y': yfld}, padding='fill')

    # Compute UE VN using cos(), sin()
    u_east = velc['X']*coords['CS'] - velc['Y']*coords['SN']
    v_north= velc['X']*coords['SN'] + velc['Y']*coords['CS']

    return u_east, v_north
