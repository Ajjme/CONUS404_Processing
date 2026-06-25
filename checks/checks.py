import netCDF4 as nc
import numpy as np

# 1. FIX: Make sure this points to a RAW file from WRF (not your processed output)
# 2. FIX: Added 'c:' drive letter and ensured the exact file name is typed out
raw_wrf_file = r'c:\Users\ajj4p\Documents\GitHub\CONUS404_Processing\year_raw_data\water_year_2021\wrfxtrm_conusii_202010\caldera\projects\usgs\water\impd\wrf-conus404\kyoko\wrfout_post\WY2021\wrfxtrm_d01_2020-10-01_00_00_00'

try:
    ds = nc.Dataset(raw_wrf_file, 'r')
    print("✓ Successfully opened the raw WRF file!")
except Exception as e:
    print(f"Error opening file: {e}")
    print("Double check that the file exists at this exact path and isn't missing an extension!")
    exit()

# 1. Check if the file already has coordinates built-in
print("\nVariables in file:", list(ds.variables.keys())[:15], "... [truncated]")

# If XLAT and XLONG exist, compare them to your script's output:
if 'XLAT' in ds.variables:
    raw_lat = ds.variables['XLAT'][:]
    raw_lon = ds.variables['XLONG'][:]
    
    # Handle both 2D and 3D shapes gracefully
    mid_y = raw_lat.shape[-2] // 2
    mid_x = raw_lat.shape[-1] // 2
    
    if raw_lat.ndim == 3:
        print(f"True Raw Center: {raw_lat[0, mid_y, mid_x]}°N, {raw_lon[0, mid_y, mid_x]}°E")
        print(f"True Bottom-Left Corner: {raw_lat[0, 0, 0]}°N, {raw_lon[0, 0, 0]}°E")
    else:
        print(f"True Raw Center: {raw_lat[mid_y, mid_x]}°N, {raw_lon[mid_y, mid_x]}°E")
        print(f"True Bottom-Left Corner: {raw_lat[0, 0]}°N, {raw_lon[0, 0]}°E")

# 2. Check global metadata to see if our assumptions match reality
print("\n--- Global Metadata Projection Attributes ---")
for attr in ds.ncattrs():
    if any(p in attr.upper() for p in ['DX', 'DY', 'CEN_LAT', 'CEN_LON', 'TRUELAT']):
        print(f"{attr}: {ds.getncattr(attr)}")

ds.close()

#If the printed CEN_LAT isn't 39.1 or DX isn't 4000.0, your assumptions are wrong and you must change the hardcoded numbers in compute_lcc_coordinates to match these attributes.
# --- Global Metadata Projection Attributes ---
# DX: 4000.0
# DY: 4000.0
# CEN_LAT: 39.100006103515625
# CEN_LON: -97.89999389648438
# TRUELAT1: 30.0
# TRUELAT2: 50.0
# MOAD_CEN_LAT: 39.100006103515625