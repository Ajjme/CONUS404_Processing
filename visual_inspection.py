"""
Method B Validation: Visual Inspection using Cartopy.
Plots wind data on its native LCC projection and overlays US State boundaries.
"""

import xarray as xr
import matplotlib.pyplot as plt
import numpy as np
import warnings

# Import Cartopy components
import cartopy.crs as ccrs
import cartopy.feature as cfeature

warnings.filterwarnings('ignore')

print("Loading NetCDF file...")
# Updating to point to your new Water Year 2024 output file
nc_file = r'c:\Users\ajj4p\Documents\GitHub\CONUS404_Processing\year_raw_data\water_year_2024\wrfxtrm_d01_max_spduv10max_2024.nc'
ds = xr.open_dataset(nc_file)

print("\n=== EXTRACTING DATA ===")
wind_speed = ds['SPDUV10MAX'].values

# Check for 2D coordinate variables we generated in the file
if 'lat_2d' in ds.variables and 'lon_2d' in ds.variables:
    lat_2d = ds['lat_2d'].values
    lon_2d = ds['lon_2d'].values
    print("✓ Successfully loaded 2D coordinates (lat_2d, lon_2d)")
else:
    # Fallback to standard lat/lon if 2D variables aren't found
    lat_2d = ds['lat'].values
    lon_2d = ds['lon'].values
    if lat_2d.ndim == 1:
        lon_2d, lat_2d = np.meshgrid(lon_2d, lat_2d)
    print("! Using 1D/fallback coordinates expanded to 2D meshgrid")

print("\n=== CREATING VISUALIZATION ===")

# 1. Define the Native Data Projection (LCC parameters from your file generation script)
# This matches the true WRF CONUS404 sphere and center
data_proj = ccrs.LambertConformal(
    central_longitude=-97.9, 
    central_latitude=39.1,
    standard_parallels=(30.0, 50.0),
    globe=ccrs.Globe(semimajor_axis=6370000, semiminor_axis=6370000)
)

# 2. Define the Map View Projection (We will use the same projection to keep rendering crisp)
fig = plt.figure(figsize=(14, 11))
ax = plt.axes(projection=data_proj)

# Set map boundaries to frame the continental US beautifully
ax.set_extent([-120, -74, 23, 50], crs=ccrs.PlateCarree())

# 3. Plot the wind data
# transform=ccrs.PlateCarree() is CRITICAL here because lon_2d/lat_2d are in degrees, not meters.
print("Plotting wind layers...")
im = ax.pcolormesh(lon_2d, lat_2d, wind_speed, cmap='viridis', 
                   shading='auto', transform=ccrs.PlateCarree(), zorder=1)

# 4. Add Cartopy Map Features (The alignment test!)
print("Adding state borders and coastlines...")
ax.add_feature(cfeature.COASTLINE, linewidth=1.2, edgecolor='black', zorder=3)
ax.add_feature(cfeature.BORDERS, linewidth=1.0, edgecolor='black', zorder=3)

# Add US States layer with high contrast color
states = cfeature.NaturalEarthFeature(category='cultural',
                                      name='admin_1_states_provinces_lines',
                                      scale='50m', facecolor='none')
ax.add_feature(states, linewidth=0.8, edgecolor='white', linestyle='--', zorder=3)

# 5. Add Gridlines (labeled with degrees)
gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.5, zorder=4)
gl.top_labels = False
gl.right_labels = False

# 6. Add aesthetics and Colorbar
ax.set_title('Maximum Wind Speed (Water Year 2024)\nVisual Alignment Validation with US States', 
             fontweight='bold', fontsize=14, pad=15)

cbar = plt.colorbar(im, ax=ax, orientation='horizontal', pad=0.05, shrink=0.7)
cbar.set_label('Wind Speed (m/s)', fontsize=12, labelpad=10)

# 7. Add quick stats text box directly onto the plot
stats_text = f"Max Wind: {np.nanmax(wind_speed):.2f} m/s\nMin Wind: {np.nanmin(wind_speed):.2f} m/s"
plt.text(0.02, 0.02, stats_text, transform=ax.transAxes, fontsize=10, 
         fontweight='bold', family='monospace',
         bbox=dict(boxstyle='round', facecolor='white', alpha=0.8), zorder=5)

print("Saving figure...")
output_png = 'max_wind_speed_cartopy_validation.png'
plt.savefig(output_png, dpi=200, bbox_inches='tight')
print(f"✓ Saved validation map to: {output_png}")

plt.show()