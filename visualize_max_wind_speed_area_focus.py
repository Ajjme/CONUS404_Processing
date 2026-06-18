"""
Visualization of maximum wind speed from CONUS404 WRF model
with regional bounding box cropping around Durham, NC.
"""

import xarray as xr
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import Normalize
import warnings
warnings.filterwarnings('ignore')

print("Loading NetCDF file...")
nc_file = 'year_raw_data/water_year_2020/wrfxtrm_d01_max_spduv10max_2020.nc'
ds = xr.open_dataset(nc_file)

print("\n=== DATASET INFORMATION ===")
print(ds)

# Extract coordinates and data
print("\n=== EXAMINING DATA ===")

# Find coordinate variables
coord_vars = list(ds.coords.keys())
data_vars = list(ds.data_vars.keys())

print(f"Coordinates: {coord_vars}")
print(f"Data variables: {data_vars}")

# Prioritize the true 2D variables we generated if they are available
if 'lat_2d' in ds.variables and 'lon_2d' in ds.variables:
    lat_2d = ds['lat_2d'].values
    lon_2d = ds['lon_2d'].values
    print("\nFound 'lat_2d' and 'lon_2d' variables")
elif 'lat' in ds.coords:
    lat = ds['lat'].values
    lon = ds['lon'].values
    lon_2d, lat_2d = np.meshgrid(lon, lat)
    print("\nFound 'lat' and 'lon' coordinates, expanded to 2D")
elif 'XLAT' in ds.data_vars:
    lat_2d = ds['XLAT'].values
    lon_2d = ds['XLONG'].values
    print("\nFound 'XLAT' and 'XLONG' data variables")
else:
    print("\nNo explicit coordinates found. Creating synthetic grid...")
    grid_shape = ds['SPDUV10MAX'].shape
    south_north, west_east = grid_shape
    lat_min, lat_max = 24.5, 49.5
    lon_min, lon_max = -125.0, -66.0
    lat = np.linspace(lat_max, lat_min, south_north)
    lon = np.linspace(lon_min, lon_max, west_east)
    lon_2d, lat_2d = np.meshgrid(lon, lat)

# Get the main wind speed variable
wind_var = None
for var in data_vars:
    if 'spd' in var.lower() or 'wind' in var.lower():
        wind_var = var
        break

if wind_var is None:
    wind_var = data_vars[0]

print(f"\nUsing variable: {wind_var}")
wind_speed = ds[wind_var].values

# Handle multi-dimensional data
if wind_speed.ndim == 3:
    wind_speed = np.nanmax(wind_speed, axis=0)
elif wind_speed.ndim == 4:
    wind_speed = np.nanmax(wind_speed[:, 0, :, :], axis=0)

# =====================================================================
# NEW: REGIONAL CROPPING CONFIGURATION (Durham, NC)
# =====================================================================
# Center: 35.9940° N, -78.8986° W
# Let's create a +/- 1.5 degree box around Durham for a nice regional view
lat_center, lon_center = 35.9940, -78.8986
lat_padding, lon_padding = 3, 3

crop_lat_min = lat_center - lat_padding
crop_lat_max = lat_center + lat_padding
crop_col_min = lon_center - lon_padding
crop_col_max = lon_center + lon_padding

# Create a boolean mask matching the regional box
region_mask = (
    (lat_2d >= crop_lat_min) & (lat_2d <= crop_lat_max) & 
    (lon_2d >= crop_col_min) & (lon_2d <= crop_col_max)
)

# Pull local statistics just for this cropped window
cropped_wind = np.where(region_mask, wind_speed, np.nan)

if np.sum(region_mask) == 0:
    print("\n⚠️ WARNING: Your crop bounds do not overlap with the dataset grid.")
    print("Defaulting back to the full domain view.")
    # Reset bounds to full map if something went wrong
    crop_lat_min, crop_lat_max = 24, 50
    crop_col_min, crop_col_max = -125, -65
    cropped_wind = wind_speed
else:
    print(f"\n✓ Successfully cropped around Durham, NC!")
    print(f"  Cropped Lat Box: {crop_lat_min:.2f}° to {crop_lat_max:.2f}°")
    print(f"  Cropped Lon Box: {crop_col_min:.2f}° to {crop_col_max:.2f}°")
# =====================================================================

print(f"\n=== REGIONAL WIND SPEED STATISTICS ===")
print(f"Min: {np.nanmin(cropped_wind):.2f} m/s")
print(f"Max: {np.nanmax(cropped_wind):.2f} m/s")
print(f"Mean: {np.nanmean(cropped_wind):.2f} m/s")

# Create simple matplotlib map
print("\n=== CREATING VISUALIZATION ===")

fig, axes = plt.subplots(2, 1, figsize=(12, 10))

# Main map (We still plot the arrays, but adjust the view limits)
im = axes[0].pcolormesh(lon_2d, lat_2d, wind_speed, cmap='viridis', shading='auto')
axes[0].set_xlabel('Longitude')
axes[0].set_ylabel('Latitude')
axes[0].set_title(f'Maximum Wind Speed (Zoomed: Durham, NC Region)\nCONUS404 WRF Model', fontweight='bold', fontsize=12)

# Apply our cropped limits here
axes[0].set_xlim([crop_col_min, crop_col_max])
axes[0].set_ylim([crop_lat_min, crop_lat_max])

# Drop a red marker directly onto Durham's coordinates
axes[0].plot(lon_center, lat_center, marker='*', color='red', markersize=12, label='Durham, NC')
axes[0].legend(loc='upper right')

cbar = plt.colorbar(im, ax=axes[0])
cbar.set_label('Wind Speed (m/s)', rotation=270, labelpad=20)
axes[0].grid(True, alpha=0.4)

# Statistics (Updated to use regional statistics)
stats_text = f"""
Durham Region Wind Speed Statistics:
  Maximum: {np.nanmax(cropped_wind):.2f} m/s
  Minimum: {np.nanmin(cropped_wind):.2f} m/s
  Mean:    {np.nanmean(cropped_wind):.2f} m/s
  
Bounding Box Dimensions:
  Lat: {crop_lat_min:.2f}° to {crop_lat_max:.2f}°
  Lon: {crop_col_min:.2f}° to {crop_col_max:.2f}°
"""
axes[1].text(0.1, 0.5, stats_text, fontsize=11, family='monospace',
            verticalalignment='center',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
axes[1].axis('off')

plt.tight_layout()

print("Saving figure...")
plt.savefig('max_wind_speed_durham_crop.png', dpi=150, bbox_inches='tight')
print("✓ Saved to max_wind_speed_durham_crop.png")

print("\nDone!")