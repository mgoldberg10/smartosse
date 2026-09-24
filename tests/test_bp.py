import os
import tempfile
import numpy as np
import pytest
import xarray as xr
from unittest import mock
from smartosse.bp import BPReader


# === Helper to create temporary binary data ===
def generate_temp_bp_files(run_dir_root, iternums, nx, dtype=np.dtype('>f4')):
    """
    Creates fake BP binary data files and a mock data.ecco file.
    Files are structured as: run_dir_root/iterXXXX/var.data
    """
    vars_to_create = [
        "bpdatanom_raw",
        "bpdatanom_smooth",
        "bpdifanom_raw",
        "bpdifanom_smooth",
        "m_bpday",
    ]
    data_shape = (2, nx, nx, 5)  # as per your note: 2*30*30*5
    nbytes = np.prod(data_shape) * dtype.itemsize

    for iternum in iternums:
        iter_dir = os.path.join(run_dir_root, f"iter{iternum:04d}")
        os.makedirs(iter_dir, exist_ok=True)

        # Create each variable file
        for var in vars_to_create:
            if var.startswith("m_bp"):
                filename = f"{var}.{iternum:010d}.data"
            else:
                filename = f"{var}.data"

            path = os.path.join(iter_dir, filename)
            arr = np.random.rand(*data_shape).astype(dtype)
            arr.tofile(path)

        # Write a mock data.ecco file
        with open(os.path.join(iter_dir, "data.ecco"), "w") as f:
            f.write(" &GENCOST_NML\n")
            f.write(" gencost_name(1) = 'bpv4-grace'\n")
            f.write(" gencost_errfile(1) = 'sigma.data'\n")
            f.write(" /\n")

        # Create corresponding sigma.data
        sigma = np.ones((nx, nx), dtype=dtype)
        sigma.tofile(os.path.join(iter_dir, "sigma.data"))


@pytest.fixture
def mock_environment(tmp_path):
    """Creates a temporary fake BP directory structure for testing."""
    run_dir = tmp_path / "run"
    iternums = [0, 2]
    nx = 30
    generate_temp_bp_files(run_dir, iternums, nx)
    return run_dir, iternums, nx


# === Mocked read_aste_bin ===
def mock_read_aste_bin(filepath, var_name):
    """Return a small deterministic xarray.DataArray to avoid real binary I/O."""
    data = np.ones((2, 6, 30, 30))
    da = xr.DataArray(data, dims=('k', 'tile', 'j', 'i'), name=var_name)
    return da

# === deterministic fake bpdifanom_raw for seeding sensor detection ===
def generate_deterministic_bpdifanom(nx=30):
    data = np.zeros((2, 2, 6, nx, nx), dtype=np.float32)  # ioptim=2 to match mock_read_aste_bin
    np.random.seed(42)
    for t in range(6):
        n_points = np.random.randint(1, 10)
        js = np.random.randint(0, nx, n_points)
        is_ = np.random.randint(0, nx, n_points)
        # Fill both ioptim slices
        for io in range(2):
            data[io, 0, t, js, is_] = 1.0
    return xr.DataArray(data, dims=["ioptim", "time", "tile", "j", "i"])

@mock.patch("smartosse.bp.xu.get_extra_metadata", return_value={"meta": "mocked"})
@mock.patch("smartosse.bp.read_aste_bin", side_effect=mock_read_aste_bin)
def test_bpread_initialization(mock_read, mock_meta, mock_environment):
    run_dir, iternums, nx = mock_environment

    # Instantiate BPReader
    bpr = BPReader(str(run_dir), iternums=iternums, nx=nx)

    # === Verify discovered variables ===
    expected_vars = [
        "bpdatanom_raw",
        "bpdatanom_smooth",
        "bpdifanom_raw",
        "bpdifanom_smooth",
        "m_bpday",
    ]
    assert sorted(bpr.var_names) == sorted(expected_vars)

    # === Verify dataset structure ===
    assert isinstance(bpr.ds, xr.Dataset)
    for v in expected_vars:
        assert v in bpr.ds

    # === Verify metadata was loaded ===
    mock_meta.assert_called_once()

    # === Verify compute_model_anom added variable ===
    assert "m_bpday_anom" in bpr.ds

    # === Check weight and sigma ===
    assert "sigma" in bpr.ds
    assert "weight" in bpr.ds

    # === Ensure __repr__ returns a string ===
    repr_str = repr(bpr)
    assert "BPReader" in repr_str
    assert "run_dir_root" in repr_str



@mock.patch("smartosse.bp.xu.get_extra_metadata", return_value={"meta": "mocked"})
@mock.patch("smartosse.bp.read_aste_bin", side_effect=mock_read_aste_bin)
def test_get_sensors_with_deterministic_field(mock_read, mock_meta, mock_environment, capsys):
    """Test BPReader.get_sensors() using a deterministic seeded bpdifanom_raw pattern."""
    run_dir, iternums, nx = mock_environment

    # Instantiate BPReader as normal
    bpr = BPReader(str(run_dir), iternums=iternums, nx=nx)

    # Overwrite bpdifanom_raw with known deterministic data
    bpr.ds["bpdifanom_raw"] = generate_deterministic_bpdifanom()

    # Run the real method
    bpr.get_sensors(bad_vals=[0.0])

    # Capture printed output
    out = capsys.readouterr().out
    assert "Found 33 sensors" in out

    # Verify sensor_args created and structure correct
    sa = bpr.sensor_args
    assert isinstance(sa, dict)
    for key in ["tile", "j", "i"]:
        assert key in sa
        assert isinstance(sa[key], xr.DataArray)

    # Verify deterministic match with known arrays for np.random.seed(42)
    expected_tiles = np.array([
        0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2,
        3, 3, 3, 4, 4, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5
    ])
    expected_j = np.array([
         7, 10, 14, 19, 20, 28, 28,  2,  3,  7, 21, 23,  0,  1, 11, 20, 25,
        27, 11, 19, 22,  6,  8, 20,  1,  8, 13, 17, 19, 20, 25, 25, 27
    ])
    expected_i = np.array([
        10, 22, 18,  6, 23, 10, 25, 11, 20,  1, 29, 23, 24, 21, 16, 11, 26,
        28, 24,  4,  2,  6,  3, 17, 14, 11, 14, 27,  2,  7,  6, 28, 27
    ])

    np.testing.assert_array_equal(sa["tile"].values, expected_tiles)
    np.testing.assert_array_equal(sa["j"].values, expected_j)
    np.testing.assert_array_equal(sa["i"].values, expected_i)
