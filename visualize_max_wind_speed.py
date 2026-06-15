"""
Script to visualize maximum wind speed from CONUS404 WRF model output
Displays a map of the United States colored by max wind speed values
"""

import xarray as xr
import matplotlib.pyplot as plt
import numpy as np
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
import warnings
warnings.filterwarnings('ignore')

# Load the NetCDF file
print("Loading NetCDF file...")
nc_file = 'raw_data/wrfxtrm_d01_max_spduv10max.nc'
ds = xr.open_dataset(nc_file)

# Print dataset info
print("\nDataset Information:")
print(ds)
print("\nVariables in dataset:", list(ds.data_vars.keys()))
print("Dimensions:", dict(ds.dims))

# Extract the max wind speed variable
# The variable is likely named something like 'spduv10max' or similar
var_names = list(ds.data_vars.keys())
print(f"\nAvailable variables: {var_names}")

# Find the wind speed variable (usually contains 'spd' or 'wind')
wind_var = None
for var in var_names:
    if 'spd' in var.lower() or 'wind' in var.lower() or 'u10' in var.lower() or 'v10' in var.lower():
        wind_var = var
        print(f"Using variable: {wind_var}")
        break

if wind_var is None:
    # If no match found, use the first data variable
    wind_var = var_names[0]
    print(f"No obvious wind variable found. Using first variable: {wind_var}")

# Extract data
wind_speed = ds[wind_var].values

# Get latitude and longitude
if 'lat' in ds.coords:
    lat = ds['lat'].values
    lon = ds['lon'].values
elif 'XLAT' in ds.data_vars:
    lat = ds['XLAT'].values
    lon = ds['XLONG'].values
else:
    # Try to find lat/lon in data variables
    lat_names = [v for v in ds.data_vars.keys() if 'lat' in v.lower()]
    lon_names = [v for v in ds.data_vars.keys() if 'lon' in v.lower()]
    if lat_names and lon_names:
        lat = ds[lat_names[0]].values
        lon = ds[lon_names[0]].values
    else:
        raise ValueError("Cannot find latitude and longitude coordinates in the file")

print(f"\nData shape: {wind_speed.shape}")
print(f"Latitude range: {lat.min():.2f} to {lat.max():.2f}")
print(f"Longitude range: {lon.min():.2f} to {lon.max():.2f}")
print(f"Wind speed range: {np.nanmin(wind_speed):.2f} to {np.nanmax(wind_speed):.2f} m/s")

# Handle multiple time steps (if present)
if wind_speed.ndim == 3:
    # Take the maximum across all time steps
    wind_speed = np.nanmax(wind_speed, axis=0)
    print("Computed maximum across time dimension")
elif wind_speed.ndim == 2:
    print("Data is 2D (single time step or already aggregated)")
else:
    print(f"Warning: Unexpected data dimensions: {wind_speed.ndim}")

# Ensure lat and lon are 2D
if lat.ndim == 1:
    lon_2d, lat_2d = np.meshgrid(lon, lat)
else:
    lat_2d = lat
    lon_2d = lon

# Create the map
print("\nCreating map visualization...")
fig = plt.figure(figsize=(16, 10))

# Use PlateCarree projection for plotting data, but display with US-focused projection
ax = plt.axes(projection=ccrs.LambertConformal(central_latitude=40, central_longitude=-96))

# Set extent to roughly cover the US
ax.set_extent([-125, -65, 24, 50], crs=ccrs.PlateCarree())

# Plot the wind speed data
im = ax.pcolormesh(lon_2d, lat_2d, wind_speed, 
                     transform=ccrs.PlateCarree(),
                     cmap='viridis', 
                     shading='auto',
                     alpha=0.8)

# Add map features
ax.add_feature(cfeature.STATES, linewidth=0.5, edgecolor='black', alpha=0.3)
ax.add_feature(cfeature.COASTLINE, linewidth=0.5, edgecolor='black')
ax.add_feature(cfeature.BORDERS, linewidth=0.5, edgecolor='black', alpha=0.3)

# Add colorbar
cbar = plt.colorbar(im, ax=ax, orientation='vertical', pad=0.02, shrink=0.8)
cbar.set_label('Maximum Wind Speed (m/s)', rotation=270, labelpad=20, fontsize=12)

# Add title and labels
plt.title(f'Maximum Wind Speed - {wind_var}\nCONUS404 WRF Model', fontsize=14, fontweight='bold')

# Add gridlines
ax.gridlines(draw_labels=True, alpha=0.3)

# Save the figure
output_file = 'max_wind_speed_map.png'
print(f"\nSaving map to {output_file}...")
plt.tight_layout()
plt.savefig(output_file, dpi=150, bbox_inches='tight')
print(f"Map saved successfully!")

# Also save a statistics figure
fig2, axes = plt.subplots(2, 2, figsize=(12, 10))

# Histogram
axes[0, 0].hist(wind_speed.flatten(), bins=50, edgecolor='black', alpha=0.7)
axes[0, 0].set_xlabel('Wind Speed (m/s)')
axes[0, 0].set_ylabel('Frequency')
axes[0, 0].set_title('Distribution of Max Wind Speed')
axes[0, 0].grid(True, alpha=0.3)

# Spatial plot (different colormap)
im2 = axes[0, 1].pcolormesh(lon_2d, lat_2d, wind_speed, cmap='RdYlBu_r', shading='auto')
axes[0, 1].set_xlabel('Longitude')
axes[0, 1].set_ylabel('Latitude')
axes[0, 1].set_title('Max Wind Speed Map (Mercator projection)')
plt.colorbar(im2, ax=axes[0, 1], label='m/s')

# Statistics text
stats_text = f"""Dataset Statistics:
Max Wind Speed: {np.nanmax(wind_speed):.2f} m/s
Min Wind Speed: {np.nanmin(wind_speed):.2f} m/s
Mean Wind Speed: {np.nanmean(wind_speed):.2f} m/s
Std Dev: {np.nanstd(wind_speed):.2f} m/s
Data Points: {np.sum(~np.isnan(wind_speed))}
"""
axes[1, 0].text(0.1, 0.5, stats_text, fontsize=11, verticalalignment='center',
                family='monospace', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
axes[1, 0].axis('off')

# Zonal profile (mean along latitude)
mean_by_lon = np.nanmean(wind_speed, axis=0)
axes[1, 1].plot(lon[0] if lon.ndim > 1 else lon, mean_by_lon, linewidth=2)
axes[1, 1].set_xlabel('Longitude')
axes[1, 1].set_ylabel('Mean Wind Speed (m/s)')
axes[1, 1].set_title('Zonal Profile (mean along latitude)')
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
stats_file = 'wind_speed_statistics.png'
plt.savefig(stats_file, dpi=150, bbox_inches='tight')
print(f"Statistics figure saved to {stats_file}")

plt.show()
print("\nVisualization complete!")
