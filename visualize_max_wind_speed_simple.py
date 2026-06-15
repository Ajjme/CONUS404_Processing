"""
Lightweight visualization of maximum wind speed from CONUS404 WRF model
Uses basemap instead of cartopy for potentially faster rendering
"""

import xarray as xr
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import Normalize
import warnings
warnings.filterwarnings('ignore')

print("Loading NetCDF file...")
nc_file = 'raw_data/wrfxtrm_d01_max_spduv10max.nc'
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

# Extract latitude and longitude
if 'lat' in ds.coords:
    lat = ds['lat'].values
    lon = ds['lon'].values
    print(f"\nFound 'lat' and 'lon' coordinates")
elif 'XLAT' in ds.data_vars:
    lat = ds['XLAT'].values
    lon = ds['XLONG'].values
    print(f"\nFound 'XLAT' and 'XLONG' data variables")
else:
    # No explicit lat/lon in file - create synthetic grid for visualization
    # CONUS404 uses Lambert Conformal projection centered on CONUS
    # For visualization, we'll use approximate lat/lon bounds
    print("\nNo explicit lat/lon coordinates found in file.")
    print("Creating synthetic coordinate grid for visualization...")
    
    # Get grid dimensions from the main variable
    grid_shape = ds['SPDUV10MAX'].shape
    south_north, west_east = grid_shape
    
    # CONUS404 approximate bounds (Lambert Conformal projection)
    # These are approximate lat/lon boundaries for the domain
    lat_min, lat_max = 24.5, 49.5  # Approximate range
    lon_min, lon_max = -125.0, -66.0  # Approximate range
    
    # Create regular grid
    lat = np.linspace(lat_max, lat_min, south_north)  # Reversed for standard orientation
    lon = np.linspace(lon_min, lon_max, west_east)
    
    # Create 2D grid
    lon_2d, lat_2d = np.meshgrid(lon, lat)
    lat = lat_2d
    lon = lon_2d
    print(f"Created synthetic grid: lat range [{lat.min():.1f}, {lat.max():.1f}], "
          f"lon range [{lon.min():.1f}, {lon.max():.1f}]")

# Get the main wind speed variable
wind_var = None
for var in data_vars:
    if 'spd' in var.lower() or 'wind' in var.lower():
        wind_var = var
        break

if wind_var is None:
    wind_var = data_vars[0]

print(f"\nUsing variable: {wind_var}")
print(f"  Shape: {ds[wind_var].shape}")
print(f"  Dtype: {ds[wind_var].dtype}")

wind_speed = ds[wind_var].values

# Handle multi-dimensional data
print(f"\nOriginal shape: {wind_speed.shape}")
if wind_speed.ndim == 3:
    # If 3D (time, lat, lon), take the max across time
    wind_speed = np.nanmax(wind_speed, axis=0)
    print(f"Reduced to 2D by taking max across time: {wind_speed.shape}")
elif wind_speed.ndim == 4:
    # If 4D, might be (time, level, lat, lon) - take first level and max across time
    wind_speed = np.nanmax(wind_speed[:, 0, :, :], axis=0)
    print(f"Reduced to 2D by taking first level and max across time: {wind_speed.shape}")

# Ensure lat/lon are properly shaped
if lat.ndim == 1 and lon.ndim == 1:
    lon_2d, lat_2d = np.meshgrid(lon, lat)
    print(f"Expanded 1D coords to 2D meshgrid")
else:
    lat_2d = lat if lat.ndim == 2 else lat
    lon_2d = lon if lon.ndim == 2 else lon

print(f"\n=== WIND SPEED STATISTICS ===")
print(f"Min: {np.nanmin(wind_speed):.2f} m/s")
print(f"Max: {np.nanmax(wind_speed):.2f} m/s")
print(f"Mean: {np.nanmean(wind_speed):.2f} m/s")
print(f"Std Dev: {np.nanstd(wind_speed):.2f} m/s")
print(f"Valid data points: {np.sum(~np.isnan(wind_speed))} / {wind_speed.size}")

print(f"\nLatitude range: {np.nanmin(lat):.2f} to {np.nanmax(lat):.2f}")
print(f"Longitude range: {np.nanmin(lon):.2f} to {np.nanmax(lon):.2f}")

# Create simple matplotlib map
print("\n=== CREATING VISUALIZATION ===")

fig, axes = plt.subplots(2, 1, figsize=(14, 10))

# Main map
im = axes[0].pcolormesh(lon_2d, lat_2d, wind_speed, cmap='viridis', shading='auto')
axes[0].set_xlabel('Longitude')
axes[0].set_ylabel('Latitude')
axes[0].set_title(f'Maximum Wind Speed - {wind_var}\nCONUS404 WRF Model', fontweight='bold', fontsize=12)
axes[0].set_xlim([-125, -65])
axes[0].set_ylim([24, 50])
cbar = plt.colorbar(im, ax=axes[0])
cbar.set_label('Wind Speed (m/s)', rotation=270, labelpad=20)
axes[0].grid(True, alpha=0.2)

# Statistics
stats_text = f"""
Wind Speed Statistics:
  Maximum: {np.nanmax(wind_speed):.2f} m/s
  Minimum: {np.nanmin(wind_speed):.2f} m/s
  Mean: {np.nanmean(wind_speed):.2f} m/s
  Std Dev: {np.nanstd(wind_speed):.2f} m/s
  
Domain:
  Lat: {np.nanmin(lat):.2f}° to {np.nanmax(lat):.2f}°
  Lon: {np.nanmin(lon):.2f}° to {np.nanmax(lon):.2f}°
"""
axes[1].text(0.1, 0.5, stats_text, fontsize=11, family='monospace',
            verticalalignment='center',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
axes[1].axis('off')

plt.tight_layout()

print("Saving figure...")
plt.savefig('max_wind_speed_map_simple.png', dpi=150, bbox_inches='tight')
print("✓ Saved to max_wind_speed_map_simple.png")

print("\nDone!")
