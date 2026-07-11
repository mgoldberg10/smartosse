import numpy as np
from scipy.spatial import KDTree
import subprocess
import glob
import matplotlib.pyplot as plt
import os
import xmitgcm.utils as xu
import xarray as xr
from xmitgcm.utils import rebuild_llc_facets, llc_facets_3d_spatial_to_compact, get_extra_metadata

def write_float32(fout,fld):
    with open(fout, 'wb') as f:
        np.array(fld, dtype=">f").tofile(f)

def write_float64(fout,fld):
    with open(fout, 'wb') as f:
        np.array(fld, dtype=">f8").tofile(f)

def read_float32(fileIn):
    with open(fileIn, 'rb') as f:
        data = np.fromfile(f, dtype=np.dtype('>f'))
    return data

def read_float64(fileIn):
    with open(fileIn, 'rb') as f:
        data = np.fromfile(f, dtype=np.dtype('>f8'))
    return data

def grep_cost(grepstr, rundir_costfname):
    sysstr='grep \'' + grepstr + '.*=.*\' ' +rundir_costfname+\
    ' | cut -d \'=\' -f2 | awk \'{print $1}\' | sed ''s/D/E/'' '
    coststr = subprocess.check_output(sysstr, shell=True)
    return float(coststr.decode())

def plot_cost(run_dir, iter_subdirs=True, fname_pfx='costfunction'):
    costs=[]
    cost_files = sorted(glob.glob(run_dir + iter_subdirs*'*/' + fname_pfx+'*'))
    optim_its = range(len(cost_files))

    for cost_file in cost_files:
        costs.append(grep_cost('fc', cost_file))
    
    fig,ax=plt.subplots()
    ax.plot(optim_its,costs, 'k.-', markersize=15)
    ax.set_yscale('log')
    ax.set_xlabel(r'optimization iteration', size=20)
    ax.set_ylabel(r'Cost function $J$', size=20);
    return fig, ax

def grep_ctrl(path, field='file'):
    """
    Parse data.ctrl in a run directory and return values for a given field.

    Parameters
    ----------
    path : str
        Path to the run directory containing data.ctrl.
    field : str, optional
        Field to extract from data.ctrl. Typical values are 'file' (control
        variable filenames) and 'weight' (weight filenames). Default is 'file'.

    Returns
    -------
    list of str
        Extracted values for all matching lines.
    """
    fname = os.path.join(path.rstrip('/'), 'data.ctrl')
    sysstr = "grep '^ xx.*{}.*' {} | cut -d '=' -f2 | cut -d \"'\" -f2 | sed 's/$/,/g' | tr -d \\\\n".format(field, fname)
    grepstr = subprocess.check_output(sysstr, shell=True)
    return grepstr.decode().split(',')[:-1]

def get_basin(
    basin_dir='/work/08381/goldberg/ls6/aste_270x450x180/run_template/input_basin/',
    basin_fname='basin_masks_eccollc_90x50_llc270A.bin',
    ):
    return read_aste_bin(basin_dir + basin_fname)


def read_mds_nosuffixpatch(*args, **kwargs):
    return read_mds(*args, **kwargs)

def read_mds(fname, iternum=None, use_mmap=None, endian='>', shape=None,
             dtype=None, use_dask=True, extra_metadata=None, chunks="3D",
             llc=False, llc_method="smallchunks", legacy=True):
    """Read an MITgcm .meta / .data file pair


    PARAMETERS
    ----------
    fname : str
        The base name of the data file pair (without a .data or .meta suffix)
    iternum : int, optional
        The iteration number suffix
    use_mmap : bool, optional
        Whether to read the data using a numpy.memmap.
        Mutually exclusive with `use_dask`.
    endian : {'>', '<', '|'}, optional
        Dndianness of the data
    dtype : numpy.dtype, optional
        Data type of the data (will be inferred from the .meta file by default)
    shape : tuple, optional
        Shape of the data (will be inferred from the .meta file by default)
    use_dask : bool, optional
        Whether wrap the reading of the raw data in a ``dask.delayed`` object.
        Mutually exclusive with `use_mmap`.
    extra_metadata : dict, optional
        Dictionary containing some extra metadata that will be appended to
        content of MITgcm meta file to create the file_metadata. This is needed
        for llc type configurations (global or regional). In this case the
        extra metadata used is of the form :

        aste = {'has_faces': True, 'ny': 1350, 'nx': 270,
        'ny_facets': [450,0,270,180,450],
        'pad_before_y': [90,0,0,0,0],
        'pad_after_y': [0,0,0,90,90],
        'face_facets': [0, 0, 2, 3, 4, 4],
        'facet_orders' : ['C', 'C', 'C', 'F', 'F'],
        'face_offsets' : [0, 1, 0, 0, 0, 1],
        'transpose_face' : [False, False, False,
        True, True, True]}

        llc90 = {'has_faces': True, 'ny': 13*90, 'nx': 90,
        'ny_facets': [3*90, 3*90, 90, 3*90, 3*90],
        'face_facets': [0, 0, 0, 1, 1, 1, 2, 3, 3, 3, 4, 4, 4],
        'facet_orders': ['C', 'C', 'C', 'F', 'F'],
        'face_offsets': [0, 1, 2, 0, 1, 2, 0, 0, 1, 2, 0, 1, 2],
        'transpose_face' : [False, False, False,
        False, False, False, False,
        True, True, True, True, True, True]}

        llc grids have typically 5 rectangular facets and will be mapped onto
        N (=13 for llc, =6 for aste) square faces.
        Keys for the extra_metadata dictionary can be of different types and
        length:


        * bool:

        #. has_faces : True if domain is combination of connected grids

        * list of len=nfacets:

        #. ny_facets : number of points in y direction of each facet
        (usually n * nx)
        #. pad_before_y (Regional configuration) : pad data with N zeros
        before array
        #. pad_after_y (Regional configuration) : pad data with N zeros
        after array
        #. facet_order : row/column major order of this facet

        * list of len=nfaces:

        #. face_facets : facet of origin for this face

        #. face_offsets : position of the face in the facet (0 = start)

        #. transpose_face : transpose the data for this face

    chunks : {'3D', '2D', 'CS'}
        Which routine to use for chunking data. '2D' splits the file
        into a individual dask chunk of size (nx x nx) for each face (if llc)
        of each record of each level.
        '3D' loads the whole raw data file (either into memory or as a
        numpy.memmap) and is not suitable for llc configurations.
        The different methods will have different memory and i/o performance
        depending on the details of the system configuration.
        'CS' loads 2d (nx, ny) chunks for each face of the Cube Sphere model.

    obsolete : llc and llc_methods, kept for testing

    RETURNS
    -------
    data : dict
       The keys correspond to the variable names of the different variables in
       the data file. The values are the data itself, either as an
       ``numpy.ndarray``, ``numpy.memmap``, or ``dask.array.Array`` depending
       on the options selected.
    """

    if use_mmap and use_dask:
        raise TypeError('`use_mmap` and `use_dask` are mutually exclusive:'
                        ' Both memory-mapped and dask arrays'
                        ' use lazy evaluation.')
    elif use_mmap is None:
        use_mmap = False if use_dask else True

    if iternum is None:
        istr = ''
    else:
        assert isinstance(iternum, int)
        istr = '.%010d' % iternum
    datafile = fname + istr + '.data'
    metafile = fname + istr + '.meta'

    if use_mmap and use_dask:
        raise TypeError('nope')
    elif use_mmap is None:
        use_mmap = False if use_dask else True

    # get metadata
    try:
        metadata = xu.parse_meta_file(metafile)
        nrecs, shape, name, dtype, fldlist = \
            xu._get_useful_info_from_meta_file(metafile)
        dtype = dtype.newbyteorder(endian)
    except IOError:
        # we can recover from not having a .meta file if dtype and shape have
        # been specified already
        if shape is None:
            raise IOError("Cannot find the shape associated to %s in the \
                          metadata." % fname)
        elif dtype is None:
            raise IOError("Cannot find the dtype associated to %s in the \
                          metadata, please specify the default dtype to \
                          avoid this error." % fname)
        else:
            # add time dimensions
            shape = (1,) + shape
            shape = list(shape)
            name = os.path.basename(fname)

            metadata = {'basename': name, 'shape': shape}

    # figure out dimensions
    ndims = len(shape)-1
    if ndims == 3:
        _, nz, ny, nx = shape
        dims_vars = ('nz', 'ny', 'nx')
    elif ndims == 2:
        _, ny, nx = shape
        nz = 1
        dims_vars = ('ny', 'nx')

    # and variables
    if 'fldList' not in metadata:
        metadata['fldList'] = [metadata['basename']]

    # if not provided in extra_metadata, we assume that the variables in file
    # have the same shape
    if extra_metadata is None or 'dims_vars' not in extra_metadata:
        dims_vars_list = []
        for var in metadata['fldList']:
            dims_vars_list.append(dims_vars)

    # add extra dim information and set aside
    metadata.update({'dims_vars': dims_vars_list,
                     'dtype': dtype, 'endian': endian,
                     'nx': nx, 'ny': ny,
                     'nz': nz, 'nt': 1})  # parse_meta harcoded for nt = 1

    file_metadata = metadata.copy()

    # by default, we set to non-llc grid
    file_metadata.update({'filename': datafile, 'vars': metadata['fldList'],
                          'has_faces': False})

    # extra_metadata contains informations about llc/regional llc grid
    if extra_metadata is not None and llc:
        nhpts_ex = extra_metadata['nx'] * extra_metadata['ny']
        nhpts = metadata['nx'] * metadata['ny']
        # check that nx * ny is consistent between extra_metadata and meta file
        # unless it's a vertical profile nx = ny = 1
        if nhpts > 1:
            assert nhpts_ex == nhpts
    if extra_metadata is not None:
        file_metadata.update(extra_metadata)

    # --------------- LEGACY --------------------------
    # from legacy code (needs to be phased out)
    # transition code to keep unit tests working
    if llc:
        chunks = "2D"
    # --------------- /LEGACY --------------------------

    # it is possible to override the values of nx, ny, nz from extra_metadata
    # (needed for bug meta file ASTE) except if those are = 1 (vertical coord)
    # where we override by values found in meta file
    for dim in ['nx', 'ny', 'nz']:
        if metadata[dim] == 1:
            file_metadata.update({dim: 1})

    # MG: Handle case in which binary lacks the ".data" suffix
    # TODO: confirm this doesnt break tests
    if not os.path.exists(file_metadata['filename']) and os.path.exists(fname):
        file_metadata['filename'] = fname

    # read all variables from file into the list d
    d = xu.read_all_variables(file_metadata['fldList'], file_metadata,
                           use_mmap=use_mmap, use_dask=use_dask,
                           chunks=chunks)

    # convert list into dictionary
    out = {}
    for n, name in enumerate(file_metadata['fldList']):
        if ndims == 3:
            out[name] = d[n]
        elif ndims == 2:
            out[name] = d[n][:, 0, :]

    # --------------- LEGACY --------------------------
    # from legacy code (needs to be phased out)
    # transition code to keep unit tests working
    if legacy:
        for n, name in enumerate(file_metadata['fldList']):
            out[name] = out[name][0, :]
    # --------------- /LEGACY --------------------------
    return out

def read_domain_bin(fname, dtype=">f4", shape=None, domain="aste",
                           nx=None, nz=None, var_name=None, dims=None,
                           vert_dim="k", use_dask=False, llc=True):
    """
    Reader for MITgcm binary files coming from irregular grid

    PARAMETERS
    ----------
    fname : str
        Path to the binary file (may or may not end with `.data`).
    dtype : str or numpy.dtype, optional
        Data type of the binary file (default '>f4').
    shape : tuple, optional
        Shape of the data (required if no .meta file exists).
    domain : {'aste', 'llc', ...}, optional
        Domain name used for extra metadata and facet reshaping.
    nx : int, optional
        Horizontal grid dimension (required for LLC-style grids).
    nz : int, optional
        Number of vertical levels. If not provided, inferred from file size.
    var_name : str, optional
        Name to assign to the DataArray (default: variable name inferred from file).
    dims : tuple of str, optional
        Custom dimension names. Defaults:
            - 2D: ('tile', 'j', 'i')
            - 3D: ('k', 'tile', 'j', 'i')
    use_dask : bool, optional
        Whether to return a dask-backed DataArray (default False).
    llc : bool, optional
        Whether to apply LLC/ASTE facet reshaping (default True).

    RETURNS
    -------
    da : xarray.DataArray
        DataArray representation of the binary file.

    NOTES
    -----
    - Infers nz and shape from file size if not provided.
    - Applies domain-specific facet reshaping using `xu.get_extra_metadata(domain, nx)` if available.
    """

    # --- Infer metadata if shape is not provided ---
    extra_meta = xu.get_extra_metadata(domain=domain, nx=nx) if llc else None

    if shape is None and nx is not None:
        filesize = os.path.getsize(fname)
        itemsize = np.dtype(dtype).itemsize
        ntiles = 5 if domain == "aste" else 13
        ny = nx * ntiles
        total_elements = filesize // itemsize
        if nz is None:
            nz = total_elements // (ny * nx)
        shape = (nz, ny, nx)

    # --- Read using standard reader ---

    data_dict = read_mds_nosuffixpatch(
        fname=fname,
        shape=shape,
        dtype=np.dtype(dtype),
        endian=">",
        use_dask=use_dask,
        extra_metadata=extra_meta,
        llc=llc,
    )

    if len(data_dict) != 1:
        raise ValueError(f"Expected a single variable, got {len(data_dict)}")

    key, arr = next(iter(data_dict.items()))

    # --- Assign dimensions ---
    if dims is None:
        if arr.ndim == 3:
            dim_names = ("tile", "j", "i")
        elif arr.ndim == 4:
            dim_names = (vert_dim, "tile", "j", "i")
        else:
            raise ValueError(f"Unexpected array shape {arr.shape}")
    else:
        dim_names = dims

    name = var_name or key
    da = xr.DataArray(arr, dims=dim_names, name=name)

    return da.squeeze()


def read_aste_bin(fname, nx=270, nz=None, var_name=None, dims=None, **kwargs):
    """
    Convenience wrapper for reading ASTE binary files as xarray.DataArray.

    PARAMETERS
    ----------
    fname : str
        Path to the ASTE binary file (may lack `.data` suffix).
    nx : int, optional
        ASTE horizontal grid size (default 270).
    nz : int, optional
        Number of vertical levels. If None, inferred from file size.
    var_name : str, optional
        Name for the DataArray.
    dims : tuple of str, optional
        Custom dimension names.

    RETURNS
    -------
    da : xarray.DataArray
        ASTE DataArray.
    """
    return read_domain_bin(fname, domain='aste', nx=nx, nz=nz, var_name=var_name, dims=dims, **kwargs)


def read_llc_bin(fname, nx=90, nz=None, var_name=None, dims=None, **kwargs):
    """
    Convenience wrapper for reading ECCO binary files as xarray.DataArray.

    PARAMETERS
    ----------
    fname : str
        Path to the ECCO binary file (may lack `.data` suffix).
    nx : int, optional
        ECCO grid size (default 90 for LLC90).
    nz : int, optional
        Number of vertical levels. If None, inferred from file size.
    var_name : str, optional
        Name for the DataArray.
    dims : tuple of str, optional
        Custom dimension names.

    RETURNS
    -------
    da : xarray.DataArray
        ECCO DataArray.
    """
    return read_domain_bin(fname, domain='llc', nx=nx, nz=nz, var_name=var_name, dims=dims, **kwargs)

def write_aste_compact(fname, da, nx=270, nrepeat=1):
    aste_extra_metadata = get_extra_metadata(domain='aste', nx=nx)
    if 'tile' in da.dims:
        da = da.rename({'tile':'face'})
    if 'time' in da.dims:
        da = da.rename({'time':'k'})
    if 'k' not in da.dims:
        da = da.expand_dims(k=np.arange(nrepeat))
    da_facets = rebuild_llc_facets(da, aste_extra_metadata)
    da_compact = llc_facets_3d_spatial_to_compact(da_facets, 'k', aste_extra_metadata)
    write_float32(fname, da_compact)

def get_fH(ds, g=9.81, tau=86164):
    # coriolis
    H = ds.Depth
    lat = ds.YC
    Omega = (2 * np.pi) / tau
    lat_rad = (np.pi / 180) * lat  # convert latitude from degrees to radians
    f = 2 * Omega * np.sin(lat_rad)
    return f, H
