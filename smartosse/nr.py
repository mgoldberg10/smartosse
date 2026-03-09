import xarray as xr
import numpy as np
import glob
from xmitgcm.utils import rebuild_llc_facets, llc_facets_3d_spatial_to_compact, get_extra_metadata
from .utils import write_float32
import os

class NRLoader:
    """
    A modular class for loading, transforming, and writing xarray data 
    from multi-tiled LLC (ASTE) domain simulations.
    """

    def __init__(self, data_dir, domain='aste', nx=270, field_name='PhiBot'):
        """
        Initializes the loader with common parameters.

        Parameters
        ----------
        data_dir : str
            Base directory containing the face-separated data files (e.g., '/work/.../smart_phibot/phibot_daily/').
        domain : str
            Domain type for metadata (e.g., 'aste').
        nx : int
            LLC horizontal resolution parameter (e.g., 270).
        field_name : str
            The name of the variable to extract (e.g., 'PhiBot').
        """
        self.data_dir = data_dir
        self.domain = domain
        self.nx = nx
        self.field_name = field_name
        self.data_array = None
        self.extra_metadata = get_extra_metadata(domain=self.domain, nx=self.nx)


    def load_data(self, tiles=[1, 2, 6, 7, 10, 11], file_pattern='*face{face:02d}*'):
        """
        Loads and concatenates the xarray DataArrays across specified LLC tiles (faces).

        Parameters
        ----------
        tiles : list of int
            The LLC face numbers to load (e.g., [1, 2, 6, 7, 10, 11]).
        file_pattern : str
            Pattern to match files for each face. Assumes the face number 
            is inserted where {face:02d} is.
        """
        nr_list = []
        for face in tiles:
            # Construct the full glob path
            face_pattern = file_pattern.format(face=face)
            bp_face_paths = np.sort(glob.glob(self.data_dir + face_pattern))
            
            if len(bp_face_paths) == 0:
                print(f"Warning: No files found for face {face} at {self.data_dir + face_pattern}")
                continue
                
            nr = xr.open_mfdataset(bp_face_paths)
            nr_list.append(nr)
        
        if not nr_list:
            raise ValueError("No data arrays were loaded.")
            
        # Concatenate along the 'face' dimension
        nr = xr.concat(nr_list, dim='face')
        
        # Select the target field and rename 'face' to 'tile'
        da = nr[self.field_name]
        da = da.rename({'face': 'tile'})
        da['tile'] = np.arange(len(da.tile)) # Ensure tile coord is sequential indices
        
        self.data_array = da
        return self.data_array


    def apply_transforms(self, sel_time=None, target_dims=None, resample_freq=None, mask=None, fill_value=-9999.):
        """
        Applies a sequence of transformations to the loaded DataArray.

        Parameters
        ----------
        sel_time : str or None
            Time slice to select (e.g., '2012-01').
        target_dims : list of str or None
            Dimensions for transpose (e.g., ['time', 'tile', 'j', 'i']).
        resample_freq : str or None
            Frequency for time resampling (e.g., '1D').
        mask : xarray.DataArray or None
            Mask to apply (e.g., branch_mask).
        fill_value : float
            Value to use for masked data points.
        """
        if self.data_array is None:
            raise RuntimeError("Data must be loaded first using load_data().")
            
        da = self.data_array.copy(deep=True)

        if sel_time:
            da = da.sel(time=sel_time)
            
        if target_dims:
            da = da.transpose(*target_dims)
            
        # Compute here to avoid large memory use during resampling/masking if data is dask-backed
        da = da.compute() 
            
        if resample_freq:
            da = da.resample(time=resample_freq).mean('time')
            
        if mask is not None:
            # Apply the mask, filling masked regions with the fill_value
            da = da.where(mask, fill_value)
        
        return da


    def write_data(self, dir_out, fname_out):
        """
        Writes the transformed DataArray to disk using MITgcm LLC compact format.

        Parameters
        ----------
        dir_out : str
            Output directory path.
        fname_out : str
            Output file name (excluding directory).
        """
        if self.data_array is None:
            raise RuntimeError("Data must be loaded and transformed first.")
            
        da_aste = self.data_array.copy()

        # Rename dimensions to match xmitgcm/MITgcm convention for rebuild/compact
        if 'tile' in da_aste.dims:
            da_aste = da_aste.rename({'tile':'face'})
        if 'time' in da_aste.dims:
            da_aste = da_aste.rename({'time': 'k'}) 
        
        # 1. Rebuild the facets (creates a single large grid, usually temporary)
        da_aste = rebuild_llc_facets(da_aste, self.extra_metadata)
        
        # 2. Convert to compact spatial format (LLC files are flattened/compacted)
        # Assuming the rebuild added a 'k' dimension if time was present
        da_aste = llc_facets_3d_spatial_to_compact(da_aste, 'k', self.extra_metadata)
        
        # 3. Write to binary file
        # Note: Requires the 'write_float32' utility function from your environment
        # The code is written assuming the utility function 'write_float32' is available
        os.makedirs(dir_out, exist_ok=True)
        try:
             write_float32(f'{dir_out}/{fname_out}', da_aste)
        except NameError:
             print("Error: The 'write_float32' function is not defined. Data not written.")

        return f"Successfully processed and written to {dir_out}/{fname_out}"

# --- Example Usage ---

# Define required environment variables (replace with actual values)
# bp_dir = '/work/08381/goldberg/ls6/aste_270x450x180/run_template/input_ecco/smart_phibot/'
# aste_tiles = [1, 2, 6, 7, 10, 11]
# dir_out = './output/' 
# fname_out = 'nr_bp_201201_daily.bin'
# branch_mask = ... # Your xarray mask, shape (tile, j, i)

# # Example Initialization
# loader = NRLoader(
#     data_dir=bp_dir + 'phibot_daily/',
#     domain='aste',
#     nx=270,
#     field_name='PhiBot'
# )

# # 1. Load Data
# loader.load_data(tiles=aste_tiles)

# # 2. Apply Transforms
# loader.apply_transforms(
#     sel_time='2012-01',
#     target_dims=['time', 'tile', 'j', 'i'],
#     resample_freq='1D',
#     mask=branch_mask,
#     fill_value=-9999.
# )

# # 3. Write Data
# # print(loader.write_data(dir_out, fname_out))
