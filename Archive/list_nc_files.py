"""List NetCDF files and check for ones with coordinates."""
from pathlib import Path
import netCDF4 as nc

raw_data_dir = Path('raw_data')
print("NetCDF files in raw_data directory:")
for nc_file in raw_data_dir.rglob('*.nc'):
    size_mb = nc_file.stat().st_size / (1024**2)
    print(f"  {nc_file.relative_to(raw_data_dir)}: {size_mb:.1f} MB")

# Check if there's a reference file with coordinates
print("\nLooking for files with XLAT/XLONG...")
for nc_file in raw_data_dir.rglob('*.nc'):
    try:
        ds = nc.Dataset(nc_file, 'r')
        has_xlat = 'XLAT' in ds.variables
        has_xlong = 'XLONG' in ds.variables
        if has_xlat or has_xlong:
            print(f"  ✓ {nc_file.relative_to(raw_data_dir)}: XLAT={has_xlat}, XLONG={has_xlong}")
        ds.close()
    except:
        pass
