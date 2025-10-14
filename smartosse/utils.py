import numpy as np
from scipy.spatial import KDTree
import subprocess
import glob
import matplotlib.pyplot as plt
import os
import xmitgcm.utils as xu
import xarray as xr

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

def grep_ctrl(field, fname='data.ctrl'):
    sysstr='grep \'^ xx.*{}.*\' {} | cut -d \'=\' -f2 | cut -d \"\'\" -f2 | sed \'s/$/,/g\' | tr -d \\\\n'.format(field,fname)
    grepstr = subprocess.check_output(sysstr, shell=True)
    # return list of ctrl info
    return grepstr.decode().split(',')[:-1]

def read_mds(fname, iternum=None, use_mmap=None, endian='>', shape=None,
             dtype=None, use_dask=True, extra_metadata=None, fake_mds=False, chunks="3D",
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

    fake_mds : bool, optional
        For binary files having structure encoded in extra_metadata but 
        lack .data and .meta extensions

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
        # MG, 10/2025: Note that this still assumes we have a filename ending
        # in .data, hence the need for fake_mds (to accomodate e.g. .bin
        # files with known llc structure)
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

    # using fake_mds, can remove binary file .data extension but take
    # advantage of extra_metadata restructuring
    if fake_mds:
        file_metadata['filename'] = file_metadata['filename'][:-5] if file_metadata['filename'].endswith('.data') else file_metadata['filename']

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

def aste_read_mds(fname, nx=270, nz=None, dtype='>f4', fake_mds=False, **read_mds_kwargs):
    """
    Read raw ASTE/MITgcm-style binary file and infer nz if not provided.
    
    Parameters
    ----------
    fname : str
        Path to the binary file
    nx : int
        Grid size (default 270)
    nz : int or None
        Vertical levels; if None, infer from file size
    dtype : str or np.dtype
        Data type (default '>f4')
    
    Returns
    -------
    dict
        Dictionary from read_mds with reshaped data
    """
    ntiles = 5 # ASTE binaries have length 5*nx
    ntiles_xr = 6  # in xarray after padding, ASTE has 6 tiles
    ny = nx * ntiles   
    
    itemsize = np.dtype(dtype).itemsize

    # try to infer nz by file size, check if .data extension is needed
    fname_check = fname
    if not os.path.exists(fname_check):
        # try adding .data
        fname_check = fname + '.data'
        if not os.path.exists(fname_check) and 'iternum' in read_mds_kwargs:
            # try adding .{iternum:010d}.data
            iternum = read_mds_kwargs['iternum']
            fname_check = f"{fname}.{iternum:010d}.data"
    if not os.path.exists(fname_check):
        raise FileNotFoundError(f"File not found with any variant: {fname}, .data, or iternum extension")

    filesize = os.path.getsize(fname_check)
    
    # infer nz if not provided 
    if nz is None:
        total_elements = filesize // itemsize
        nz = total_elements // (ntiles * nx * nx)
        if total_elements % (ntiles * nx * nx) != 0:
            raise ValueError(f"Cannot evenly reshape file {fname} into "
                             f"(nz, tile, j, i) with nx={nx}, tiles={ntiles_xr}")
    
    shape = (nz, ny, nx) if nz > 1 else (ny, nx)
    
    # get extra_metadata if llc
    extra_meta = xu.get_extra_metadata(domain='aste', nx=nx)

    return read_mds(
        fname=fname,
        shape=shape,
        dtype=np.dtype(dtype),
        endian='>',
        use_dask=False,
        extra_metadata=extra_meta,
        llc=True,
        fake_mds=fake_mds,
        **read_mds_kwargs,
    )

def aste_da(fname, nx=270, nz=None, var_name=None, dims=None, fake_mds=False, domain='aste', **read_mds_kwargs):
    """
    Read an ASTE raw file and convert the output into an xarray DataArray.

    Parameters
    ----------
    fname : str
        Path to the raw binary file.
    nx : int
        Size of the x/y grid (default 270)
    nz : int or None
        Number of vertical levels; if None, infer from file size
    var_name : str, optional
        Name of the variable for the DataArray
    dims : tuple of str, optional
        Names of the dimensions. Defaults:
            - 2D: ('tile', 'j', 'i')
            - 3D: ('k', 'tile', 'j', 'i')
    fake_mds : bool
        Whether to use fake_mds flag within modified read_mds
    domain : str
        Domain name for extra_metadata (if using fake_mds)

    Returns
    -------
    xarray.DataArray
        The reshaped variable as a DataArray
    """
    # Read data
    data_dict = aste_read_mds(fname, nx=nx, nz=nz, fake_mds=fake_mds, **read_mds_kwargs)

    if len(data_dict) != 1:
        raise ValueError(f"Expected a single variable, got {len(data_dict)} keys")

    key, arr = next(iter(data_dict.items()))

    # Determine dimension names
    if dims is None:
        if arr.ndim == 3:
            dim_names = ('tile', 'j', 'i')
        elif arr.ndim == 4:
            dim_names = ('k', 'tile', 'j', 'i')
        else:
            raise ValueError(f"Unexpected array shape {arr.shape}")
    else:
        dim_names = dims

    name = var_name if var_name else key
    return xr.DataArray(arr, dims=dim_names, name=name)
