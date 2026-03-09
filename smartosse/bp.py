# Load data related to routine calc_gencost_bpv4.F

from dataclasses import dataclass, field
import numpy as np
import xarray as xr
from typing import List
from tabulate import tabulate
import re
from pathlib import Path
import xmitgcm.utils as xu
from .utils import *

@dataclass
class BPReader:
    """
    A class to read and manage BP data from multiple iterations and variables.
    """
    run_dir_root: str
    iternums: List[int]
    nx: int = 270
    ecco_frequency: str = 'day'
    dtype: np.dtype = np.dtype('>f4')
    compute_cost: bool = True

    # Populated internally
    var_names: List[str] = field(init=False)

    def _discover_bp_vars(self) -> List[str]:
        """
        Scan iteration directories and find variables that exist in *all* iteration subdirectories.
        """
        expected_vars = [
            "bpdatanom_raw",
            "bpdatanom_smooth",
            "bpdifanom_raw",
            "bpdifanom_smooth",
            self.m_bp_str,
        ]
    
        found_vars = []
        missing_summary = {}
    
        # Check that iteration directories exist
        missing_dirs = [it for it in self.iternums
                        if not os.path.isdir(f"{self.run_dir_root}/iter{it:04d}")]
        if missing_dirs:
            raise FileNotFoundError(f"[BPReader] Missing iteration directories: {missing_dirs}")
    
        # For each variable, verify its file exists in *all* iteration directories
        for var in expected_vars:
            all_exist = True
            for iternum in self.iternums:
                iter_dir = f"{self.run_dir_root}/iter{iternum:04d}"
                if var == self.m_bp_str:
                    fname = os.path.join(iter_dir, f"{var}.{iternum:010d}.data")
                else:
                    fname = os.path.join(iter_dir, f"{var}.data")
    
                if not os.path.isfile(fname):
                    all_exist = False
                    missing_summary.setdefault(var, []).append(iternum)
    
            if all_exist:
                found_vars.append(var)
    
        # Log missing vars
        if missing_summary:
            for var, iters in missing_summary.items():
                iters_str = ", ".join(str(i) for i in iters)
                print(f"[BPReader] Skipping '{var}': missing in iterations [{iters_str}]")
    
        if not found_vars:
            print(f"[BPReader] Warning: No variable files found across all iterations.")
    
        print(f"[BPReader] Found variables (common to all iterations): {', '.join(found_vars)}")
        return found_vars

    def __post_init__(self):
        self.m_bp_str = f"m_bp{self.ecco_frequency}"
        if self.ecco_frequency not in ['day', 'mon']:
            raise ValueError("Invalid ecco_frequency. Must be 'day' or 'mon'")

        # Auto-discover available BP variable names
        self.var_names = self._discover_bp_vars()

        # Load supporting metadata
        self.aste_extra_metadata = xu.get_extra_metadata(domain='aste', nx=self.nx)

        # Load all data
        self.read_data()
        self.compute_model_anom()
        self.read_weight()

        if ('bpdifanom_raw' in self.ds.data_vars) and self.compute_cost:
            self.get_cost()

    def __repr__(self):
        var_table = tabulate(enumerate(self.var_names, start=1),
                             headers=["Index", "Variable Name"], tablefmt="grid")
        indented_table = "\n".join(f"    {line}" for line in var_table.splitlines())
        return (
            f"{'-'*16}\n"
            f"    BPReader\n"
            f"{'-'*16}\n"
            f"run_dir_root : '{self.run_dir_root}'\n"
            f"iternums     : {self.iternums}\n"
            f"dtype        : {self.dtype}\n"
            f"var_names    : \n{indented_table}\n"
        )

    def read_data(self):
        """Generate dataset with bp fields"""
        data_vars = {}

        # Iterate over each file and iternum, loading the data
        for var_name in self.var_names:

            # Initialize an empty list to hold data for different iternums
            data_list = []

            for iternum in self.iternums:
                var_name_literal = var_name

                # Hack: even though the files spit out from cost_gencost_bpv4.F are all
                # in mds format, I am unable to load mds files with xmitgcm that have
                # multiple records aside from diagnostic files. As far as I can tell,
                # while file_metadata['nrecords'] might be appropriately populated, 
                # xmitgcm.utils.read_mds will only ever return the top record e.g. from 
                # read_2D_chunks -> read_xy_chunks
                # As a workaround, I run these through my fake_mds logic, in which 
                # I specify the shape and dtype (nrecords becomes k, fixed below)
                if var_name == self.m_bp_str:
                    var_name_literal = f'{var_name}.{iternum:010d}'
                var_name_literal += '.data'

                run_dir = f'{self.run_dir_root}/iter{iternum:04d}/'
                fname = f'{run_dir}/{var_name_literal}'

                # Read data using `utils.read_aste_bin`
                da = read_aste_bin(fname, var_name=var_name)

                # Append the DataArray to the list
                data_list.append(da)
                print(fname)
                print(da.dims, da.shape)

            # Add the 'ioptim' coordinate for different iternums
            data_vars[var_name] = xr.concat(data_list, dim='ioptim')

        # Concatenate the list along the 'ioptim' axis
        self.ds = xr.Dataset(data_vars = data_vars)
        self.ds = self.ds.rename({'k':'time'})

    def compute_model_anom(self):
        model_str = f'm_bp{self.ecco_frequency}'
        if model_str in list(self.ds.keys()):
            model_anom_str = f'{model_str}_anom'
            self.ds[model_anom_str] = 100 / 9.81 * (self.ds[model_str] - self.ds[model_str].mean('time'))

    def read_weight(self, iternum=0):
        """Load weights, attempting to intuit from data.ecco"""

        run_dir = f'{self.run_dir_root}/iter{iternum:04d}/'

        data_ecco_path = f'{run_dir}/data.ecco'
        
        # Open the file
        try:
            with open(data_ecco_path, "r") as file:
                lines = file.readlines()
        except FileNotFoundError:
            raise FileNotFoundError(f"The file '{data_ecco_path}' was not found. Please check the file path.")
        except Exception as e:
            raise Exception(f"An error occurred while opening the file: {e}")
        
        # Extract the index for the target gencost_name
        index = None
        try:
            for line in lines:
                if "gencost_name" in line and "bpv4-grace" in line:
                    match = re.search(r"gencost_name\((\d+)\)", line)
                    if match:
                        index = match.group(1)
                        break
            if index is None:
                raise ValueError("The gencost_name 'bpv4-grace' was not found in the file.")
        except Exception as e:
            raise Exception(f"An error occurred while searching for the gencost_name index: {e}")
        
        # If the index is found, extract the corresponding gencost_errfile
        try:
            found_errfile = False
            for line in lines:
                pattern = rf"gencost_errfile\({index}\)\s*=\s*['\"](.+?)['\"]"
                match = re.search(pattern, line)
                if match:
                    errfile = run_dir + match.group(1)
                    found_errfile = True
                    break
            if not found_errfile:
                raise ValueError(f"The gencost_errfile for index {index} was not found in the file.")
        except Exception as e:
            raise Exception(f"An error occurred while searching for the gencost_errfile: {e}")

        # Assume weight is a 2D aste field. We will spoof its .data/.meta files using XC
        sigma = read_aste_bin(errfile, var_name='sigma')
        self.ds['sigma'] = sigma.where(sigma != -9999.).squeeze()
        self.ds['weight'] = self.ds.sigma.where((self.ds.sigma != 0) & ~np.isnan(self.ds.sigma)) ** -2

    def get_sensors(self, bad_vals=[0., -9999.]):
        """
        Find coordinates of sensors for fixed-in-time pointwise bp data.
    
        Strategy
        --------
        1. Try to infer sensor locations from self.ds.bpdifanom_raw
        2. If that fails, parse gencost_datafile(1) from data.ecco
           and read the corresponding ASTE binary
        """
    
        # --------------------------------------------------
        # Method 1: infer from dataset directly
        # --------------------------------------------------
        try:
            nt = self.ds.dims.get("time", 0)
    
            found = False
            for time in range(nt):
                da = self.ds.bpdifanom_raw.isel(ioptim=0, time=time)
                mask = ~np.isin(da.values, bad_vals)
                tile, j, i = np.where(mask)
    
                if len(tile) > 0:
                    found = True
                    break
    
            if found:
                print(f"Found {len(tile)} sensors from bpdifanom_raw (time index {time})")
    
                self.sensor_args = dict(
                    tile=xr.DataArray(tile, dims="sensor"),
                    j=xr.DataArray(j, dims="sensor"),
                    i=xr.DataArray(i, dims="sensor"),
                )
                return
    
        except Exception as e:
            print("WARNING: failed to infer sensors from dataset, falling back.")
            print(f"Reason: {e}")
    
        # --------------------------------------------------
        # Method 2: parse data.ecco and read binary
        # --------------------------------------------------
        try:
            run_dir = Path(self.run_dir_root)
            data_ecco = run_dir / "iter0000" / "data.ecco"
    
            if not data_ecco.exists():
                raise FileNotFoundError(f"{data_ecco} not found")
    
            text = data_ecco.read_text()
    
            # Match: gencost_datafile(1) = 'filename',
            m = re.search(
                r"gencost_datafile\s*\(\s*1\s*\)\s*=\s*'([^']+)'",
                text,
            )
            if m is None:
                raise ValueError("Could not find gencost_datafile(1) in data.ecco")
    
            fname = m.group(1)
            binpath = run_dir / "iter0000" / fname
    
            if not binpath.exists():
                raise FileNotFoundError(f"Binary file {binpath} not found")
    
            da = read_aste_bin(str(binpath))[0]
            mask = ~np.isin(da.values, bad_vals)
            tile, j, i = np.where(mask)
    
            if len(tile) == 0:
                raise RuntimeError("Binary read succeeded but no sensors found")
    
            print(f"Found {len(tile)} sensors from {fname}")
    
            self.sensor_args = dict(
                tile=xr.DataArray(tile, dims="sensor"),
                j=xr.DataArray(j, dims="sensor"),
                i=xr.DataArray(i, dims="sensor"),
            )
            return
    
        except Exception as e:
            print("ERROR: failed to determine sensor locations by any method.")
            raise RuntimeError(e)

    def get_cost(self):
        # Check if self.ds exists
        if not hasattr(self, 'ds') or self.ds is None:
            print("Error: 'self.ds' does not exist or is None.")
            return

        if not hasattr(self, 'sensor_args') or self.sensor_args is None:
            self.get_sensors()
        
        # Check if required variables exist in self.ds
        required_vars = ['bpdifanom_smooth', 'sigma']
        missing_vars = [var for var in required_vars if var not in self.ds]
        if missing_vars:
            print(f"Error: Missing required variables in 'self.ds': {missing_vars}")
            return
        
        # Perform the computation
        try:
            cost = ((self.ds.bpdifanom_smooth ** 2) * self.ds.weight)
            self.cost = cost.isel(self.sensor_args).sum(('time', 'dim_0')).values 
            for io, jo in enumerate(self.cost):
                print(f'J{io}={jo:.8f}')
        except Exception as e:
            print(f"Error during computation: {e}")

