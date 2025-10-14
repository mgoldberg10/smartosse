# Load data related to routine calc_gencost_bpv4.F

from dataclasses import dataclass, field
import numpy as np
import xarray as xr
from typing import List
from tabulate import tabulate
import re
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
        Scan iteration directories to find available BP variable files.
        """
        # Expected base variable names
        expected_vars = [
            "bpdatanom_raw",
            "bpdatanom_smooth",
            "bpdifanom_raw",
            "bpdifanom_smooth",
            self.m_bp_str,
        ]

        found_vars = set()
        missing_vars = []

        # Just use first iteration directory for discovery
        first_iter_dir = f"{self.run_dir_root}/iter{self.iternums[0]:04d}"
        if not os.path.isdir(first_iter_dir):
            raise FileNotFoundError(f"Iteration directory not found: {first_iter_dir}")

        all_files = glob.glob(os.path.join(first_iter_dir, "*.data"))

        for var in expected_vars:
            pattern = re.compile(rf"{var}(\.\d{{10}})?\.data$")
            match = any(pattern.search(os.path.basename(f)) for f in all_files)
            if match:
                found_vars.add(var)
            else:
                missing_vars.append(var)

        # Report any missing expected files
        if missing_vars:
            print(f"[BPReader] Warning: Missing expected files for variables: {', '.join(missing_vars)}")

        print(f"[BPReader] Found variables: {', '.join(sorted(found_vars))}")
        return sorted(found_vars)

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

        if self.compute_cost:
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

                # Read data using `utils.aste_da`
                da = aste_da(fname, var_name=var_name, fake_mds=True)

                # Append the DataArray to the list
                data_list.append(da)

            # Add the 'ioptim' coordinate for different iternums
            data_vars[var_name] = xr.concat(data_list, dim='ioptim')

        # Concatenate the list along the 'ioptim' axis
        self.ds = xr.Dataset(data_vars = data_vars)
        self.ds = self.ds.rename({'k':'time'})

    def compute_model_anom(self):
        model_str = f'm_bp{self.ecco_frequency}'
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
        sigma = aste_da(errfile, var_name='sigma', fake_mds=True)
        self.ds['sigma'] = sigma.where(sigma != -9999.).squeeze()
        self.ds['weight'] = self.ds.sigma.where((self.ds.sigma != 0) & ~np.isnan(self.ds.sigma)) ** -2

    def get_sensors(self, bad_val=0.):
        """Find coordinates of sensors -- this is specific to the case in which we have (fixed in time) pointwise bp data"""
        nt = len(self.ds.time)
        time = 0
        while time <= nt:
            tile, j, i = np.where(self.ds.bpdifanom_raw.isel(ioptim=0, time=time) != bad_val)
            if (len(tile) > 0) & (len(j) > 0) & (len(i) > 0):
                break
            time += 1
        if time > nt:
            print('Error: could not find sensor indices')
            return
        print(f'Found {len(tile)} sensors')
        self.sensor_args = dict(tile=xr.DataArray(tile), j=xr.DataArray(j), i=xr.DataArray(i))

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

