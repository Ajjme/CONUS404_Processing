"""Inspect the structure of wrfxtrm files to see what variables are available."""
import netCDF4 as nc
import os

# Check one of the wrfxtrm files
file_path = r'raw_data\caldera\projects\usgs\water\impd\jkim\wrfout_post\WY2024\wrfxtrm_d01_2023-10-01_00_00_00'

if os.path.exists(file_path):
    try:
        ds = nc.Dataset(file_path, 'r')
        print("Available variables and dimensions in wrfxtrm file:")
        print("\nDimensions:")
        for dim_name, dim in ds.dimensions.items():
            print(f"  {dim_name}: {len(dim)}")
        
        print("\nVariables:")
        for var_name in sorted(ds.variables.keys()):
            var = ds.variables[var_name]
            print(f"  {var_name}: {var.dimensions} {var.dtype}")
        
        # Check for XLAT specifically
        if 'XLAT' in ds.variables:
            print("\n✓ XLAT found")
        else:
            print("\n✗ XLAT NOT found")
            
        # Check for any lat/lon variables
        lat_vars = [v for v in ds.variables.keys() if 'lat' in v.lower()]
        lon_vars = [v for v in ds.variables.keys() if 'lon' in v.lower()]
        print(f"\nLat-related variables: {lat_vars}")
        print(f"Lon-related variables: {lon_vars}")
        
        ds.close()
    except Exception as e:
        print(f"Error reading file: {e}")
        import traceback
        traceback.print_exc()
else:
    print(f"File not found: {file_path}")
