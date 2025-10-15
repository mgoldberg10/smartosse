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
             dtype=None, use_dask=True, extra_metadata=None, chunks="3D",
             llc=False, llc_method="smallchunks", legacy=True):
    """
    Read an MITgcm .meta / .data file pair or a binary file lacking the `.data` suffix.

    PARAMETERS
    ----------
    fname : str
        The base name of the data file pair (without a .data or .meta suffix).
    iternum : int, optional
        The iteration number suffix to append to `fname`.
    use_mmap : bool, optional
        Whether to read the data using a numpy.memmap.
        Mutually exclusive with `use_dask`.
    endian : {'>', '<', '|'}, optional
        Endianness of the data.
    dtype : numpy.dtype, optional
        Data type of the data (will be inferred from the .meta file by default).
    shape : tuple, optional
        Shape of the data (will be inferred from the .meta file by default).
    use_dask : bool, optional
        Whether to wrap reading in a ``dask.delayed`` object.
        Mutually exclusive with `use_mmap`.
    extra_metadata : dict, optional
        Dictionary containing extra metadata appended to MITgcm meta information
        (used for LLC or ASTE configurations). See `get_extra_metadata` for structure.
    chunks : {'3D', '2D', 'CS'}, optional
        Which routine to use for chunking data. Default is '3D'.
    llc : bool, optional
        Whether to apply LLC-style face decomposition (default False).
    llc_method : {'smallchunks'}, optional
        Legacy argument for LLC reading.
    legacy : bool, optional
        Whether to apply legacy reshaping logic (for backward compatibility).

    RETURNS
    -------
    data : dict
        Dictionary mapping variable names to NumPy or Dask arrays.

    NOTES
    -----
    This function has been patched to also handle binary files that
    do not end in `.data`. If the expected file `<fname>.data` does not exist,
    it falls back to reading `fname` directly.
    """
    if use_mmap and use_dask:
        raise TypeError('`use_mmap` and `use_dask` are mutually exclusive.')
    elif use_mmap is None:
        use_mmap = False if use_dask else True

    istr = '' if iternum is None else f'.{iternum:010d}'
    datafile = fname + istr + '.data'
    metafile = fname + istr + '.meta'

    # Attempt to parse metadata
    try:
        metadata = xu.parse_meta_file(metafile)
        nrecs, shape, name, dtype, fldlist = \
            xu._get_useful_info_from_meta_file(metafile)
        dtype = dtype.newbyteorder(endian)
    except IOError:
        # we can recover from not having a .meta file if dtype and shape have
        # been specified already
        # MG, 10/2025: Note that this still assumes we have a filename ending
        # in .data, hence the need to accomodate suffixless files with
        # known llc structure
        if shape is None:
            raise IOError("Cannot find the shape associated to %s in the \
                          metadata." % fname)
        elif dtype is None:
            raise IOError("Cannot find the dtype associated to %s in the \
                          metadata, please specify the default dtype to \
                          avoid this error." % fname)
        else:
            # add time dimensions
            shape = (1,) + shape if len(shape) == 2 else shape
            name = os.path.basename(fname)
            metadata = {'basename': name, 'shape': shape}

    # Determine dimensionality
    ndims = len(shape) - 1
    if ndims == 3:
        _, nz, ny, nx = shape
        dims_vars = ('nz', 'ny', 'nx')
    elif ndims == 2:
        _, ny, nx = shape
        nz = 1
        dims_vars = ('ny', 'nx')
    else:
        raise ValueError(f"Unexpected shape {shape}")

    if 'fldList' not in metadata:
        metadata['fldList'] = [metadata['basename']]

    dims_vars_list = [dims_vars] * len(metadata['fldList'])
    metadata.update({
        'dims_vars': dims_vars_list,
        'dtype': dtype,
        'endian': endian,
        'nx': nx, 'ny': ny, 'nz': nz,
        'nt': 1
    })

    file_metadata = metadata.copy()
    file_metadata.update({
        'filename': datafile,
        'vars': metadata['fldList'],
        'has_faces': False
    })

    if extra_metadata is not None:
        if llc:
            nhpts_ex = extra_metadata['nx'] * extra_metadata['ny']
            nhpts = metadata['nx'] * metadata['ny']
            if nhpts > 1:
                assert nhpts_ex == nhpts
        file_metadata.update(extra_metadata)

    if llc:
        chunks = "2D"

    for dim in ['nx', 'ny', 'nz']:
        if metadata[dim] == 1:
            file_metadata[dim] = 1


    # Handle missing ".data" suffix
    if not os.path.exists(file_metadata['filename']) and os.path.exists(fname):
        file_metadata['filename'] = fname

    # using fake_mds, can remove binary file .data extension but take
    # advantage of extra_metadata restructuring
    file_metadata['filename'] = file_metadata['filename'][:-5] if file_metadata['filename'].endswith('.data') else file_metadata['filename']

    # Read data
    d = xu.read_all_variables(
        file_metadata['fldList'], file_metadata,
        use_mmap=use_mmap, use_dask=use_dask, chunks=chunks
    )

    out = {}
    for n, name in enumerate(file_metadata['fldList']):
        arr = d[n]
        out[name] = arr[0, :] if legacy else arr

    return out


def read_mds_suffixless(fname, dtype='>f4', shape=None, domain='aste', nx=None,
                        nz=None, use_dask=False, llc=True):
    """
    Wrapper for reading MITgcm-style binary files that may lack the `.data` suffix.

    PARAMETERS
    ----------
    fname : str
        Path to the binary file (may or may not end with `.data`).
    dtype : str or numpy.dtype, optional
        Data type of the binary file (default '>f4').
    shape : tuple, optional
        Shape of the data (required if no .meta file exists).
    domain : {'aste', 'llc', ...}, optional
        Domain name used to retrieve extra metadata via `get_extra_metadata`.
    nx : int, optional
        Horizontal grid dimension, required for LLC-style grids.
    nz : int, optional
        Number of vertical levels. If not provided, inferred from file size.
    use_dask : bool, optional
        Whether to return dask arrays (default False).
    llc : bool, optional
        Whether to apply LLC/ASTE reshaping logic (default True).

    RETURNS
    -------
    data : dict
        Dictionary mapping variable names to NumPy or Dask arrays.

    NOTES
    -----
    This wrapper automatically handles:
      * Binary files without `.data` suffixes.
      * ASTE or ECCO domain reshaping via `get_extra_metadata(domain, nx)`.
      * Inference of `nz` if not specified and file size is known.
    """
    extra_meta = xu.get_extra_metadata(domain=domain, nx=nx) if llc else None

    if shape is None and nx is not None:
        filesize = os.path.getsize(fname)
        itemsize = np.dtype(dtype).itemsize
        ntiles = 5 if domain == 'aste' else 13
        ny = nx * ntiles
        total_elements = filesize // itemsize
        if nz is None:
            nz = total_elements // (ny * nx)
        shape = (nz, ny, nx)

    data = read_mds(
        fname=fname,
        shape=shape,
        dtype=np.dtype(dtype),
        endian='>',
        use_dask=use_dask,
        extra_metadata=extra_meta,
        llc=llc
    )
    return data


def read_region_bin(fname, domain='aste', nx=None, nz=None, var_name=None, dims=None):
    """
    Generic reader for MITgcm regional binary files, returning an xarray.DataArray.

    PARAMETERS
    ----------
    fname : str
        Path to the raw binary file (may lack `.data` suffix).
    domain : {'aste', 'llc', ...}, optional
        Model domain name. Used to determine facet layout and metadata.
    nx : int, optional
        X-dimension grid size for the regional grid (e.g., 270 for ASTE).
    nz : int, optional
        Number of vertical levels. If None, inferred from file size.
    var_name : str, optional
        Name to assign to the DataArray (default: variable name from file).
    dims : tuple of str, optional
        Custom dimension names. Defaults:
            - 2D: ('tile', 'j', 'i')
            - 3D: ('k', 'tile', 'j', 'i')

    RETURNS
    -------
    da : xarray.DataArray
        DataArray representation of the binary file.
    """
    data_dict = read_mds_suffixless(fname, domain=domain, nx=nx, nz=nz)
    if len(data_dict) != 1:
        raise ValueError(f"Expected a single variable, got {len(data_dict)}")

    key, arr = next(iter(data_dict.items()))

    if dims is None:
        if arr.ndim == 3:
            dim_names = ('tile', 'j', 'i')
        elif arr.ndim == 4:
            dim_names = ('k', 'tile', 'j', 'i')
        else:
            raise ValueError(f"Unexpected array shape {arr.shape}")
    else:
        dim_names = dims

    name = var_name or key
    return xr.DataArray(arr, dims=dim_names, name=name)


def read_aste_bin(fname, nx=270, nz=None, var_name=None, dims=None):
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
    return read_region_bin(fname, domain='aste', nx=nx, nz=nz, var_name=var_name, dims=dims)


def read_llc_bin(fname, nx=90, nz=None, var_name=None, dims=None):
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
    return read_region_bin(fname, domain='llc', nx=nx, nz=nz, var_name=var_name, dims=dims)
