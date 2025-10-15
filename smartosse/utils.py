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
    d = read_all_variables(
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
    domain : {'aste', 'ecco', ...}, optional
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
    extra_meta = get_extra_metadata(domain=domain, nx=nx) if llc else None

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
<<<<<<< HEAD
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

