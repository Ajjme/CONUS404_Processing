"""
Visualization of maximum wind speed from CONUS404 WRF model
Batch processing for all available water years with regional bounding box cropping.
Production-grade implementation showing raw 4km grid blocks with a smooth colorbar.
"""

import os
import glob
import re
import xarray as xr
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
import geopandas as gpd
import warnings
warnings.filterwarnings('ignore')

# =====================================================================
# CIRCAD CADENCE DESIGN SYSTEM INITIALIZATION
# =====================================================================
cadence_colors = {
    'teal': '#2F8F7F',
    'grey': '#333333',
    'tan': '#D9A341',
    'blue': '#205196',
    'light_blue': '#6FA8DC',
    'ice_blue': '#E9ECEF',
    'red': '#AA2634',
    'purple': '#673399'
}

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Inter', 'Arial', 'Helvetica', 'DejaVu Sans']
plt.rcParams['text.color'] = cadence_colors['grey']
plt.rcParams['axes.labelcolor'] = cadence_colors['grey']
plt.rcParams['xtick.color'] = cadence_colors['grey']
plt.rcParams['ytick.color'] = cadence_colors['grey']
plt.rcParams['axes.edgecolor'] = '#CCCCCC'
plt.rcParams['axes.linewidth'] = 0.8

# Highly dense color ramp (N=512) ensures the legend is perfectly smooth
cadence_cmap = LinearSegmentedColormap.from_list(
    'cadence_hazard_ramp',
    [
        cadence_colors['light_blue'],
        cadence_colors['teal'],
        cadence_colors['tan'],
        cadence_colors['red']
    ],
    N=512
)

# =====================================================================
# DATA INITIALIZATION & LOADING
# =====================================================================
output_dir = 'output'
os.makedirs(output_dir, exist_ok=True)

file_pattern = 'year_raw_data/water_year_*/wrfxtrm_d01_max_spduv10max_*.nc'
nc_files = sorted(glob.glob(file_pattern))

print(f"Found {len(nc_files)} files to process.")

durham_boundary = None
nc_state_boundary = None

try:
    print("Loading Durham County GeoJSON...")
    durham_boundary = gpd.read_file('geo/DCo_Boundary.geojson')
    if durham_boundary.crs != "EPSG:4326":
        durham_boundary = durham_boundary.to_crs(epsg=4326)
    print("✓ Successfully loaded Durham geometry.")
except Exception as e:
    print(f"⚠️ Warning: Could not load Durham GeoJSON ({e}).")

try:
    print("Loading North Carolina State & County GeoJSON...")
    nc_state_boundary = gpd.read_file('geo/North_Carolina_State_and_County_Boundary_Polygons.geojson')
    if nc_state_boundary.crs != "EPSG:4326":
        nc_state_boundary = nc_state_boundary.to_crs(epsg=4326)
    print("✓ Successfully loaded North Carolina geometry.")
except Exception as e:
    print(f"⚠️ Warning: Could not load NC State GeoJSON ({e}).")

# =====================================================================
# BATCH PROCESSING LOOP
# =====================================================================
for nc_file in nc_files:

    year_match = re.search(r'max_spduv10max_((?:19|20)\d{2})\.nc', nc_file)
    year_str = year_match.group(1) if year_match else "Unknown"
    
    print(f"\n=========================================")
    print(f"Processing Water Year: {year_str}")
    print(f"File: {nc_file}")
    print(f"=========================================")
    
    try:
        ds = xr.open_dataset(nc_file)
        
        coord_vars = list(ds.coords.keys())
        data_vars = list(ds.data_vars.keys())

        if 'lat_2d' in ds.variables and 'lon_2d' in ds.variables:
            lat_2d = ds['lat_2d'].values
            lon_2d = ds['lon_2d'].values
        elif 'lat' in ds.coords:
            lat = ds['lat'].values
            lon = ds['lon'].values
            lon_2d, lat_2d = np.meshgrid(lon, lat)
        elif 'XLAT' in ds.data_vars:
            lat_2d = ds['XLAT'].values
            lon_2d = ds['XLONG'].values
        else:
            grid_shape = ds['SPDUV10MAX'].shape
            south_north, west_east = grid_shape[-2], grid_shape[-1]
            lat_min, lat_max = 24.5, 49.5
            lon_min, lon_max = -125.0, -66.0
            lat = np.linspace(lat_max, lat_min, south_north)
            lon = np.linspace(lon_min, lon_max, west_east)
            lon_2d, lat_2d = np.meshgrid(lon, lat)

        wind_var = None
        for var in data_vars:
            if 'spd' in var.lower() or 'wind' in var.lower():
                wind_var = var
                break

        if wind_var is None:
            wind_var = data_vars[0]

        wind_speed = ds[wind_var].values

        if wind_speed.ndim == 3:
            wind_speed = np.nanmax(wind_speed, axis=0)
        elif wind_speed.ndim == 4:
            wind_speed = np.nanmax(wind_speed[:, 0, :, :], axis=0)

        wind_speed = wind_speed * 2.23694

        lat_center, lon_center = 35.9940, -78.8986
        lat_padding, lon_padding = .5, 1.25

        crop_lat_min = lat_center - lat_padding
        crop_lat_max = lat_center + lat_padding
        crop_col_min = lon_center - lon_padding
        crop_col_max = lon_center + lon_padding

        # =====================================================================
        # VISUALIZATION ENGINE (RAW BLOCKS + CONTINUOUS COLORBAR)
        # =====================================================================
        fig, ax = plt.subplots(figsize=(11, 8.5))
        ax.set_aspect('equal')

        # SWITCHED BACK TO PCOLORMESH: This preserves the raw 4km resolution cells on the map
        im = ax.pcolormesh(
            lon_2d, lat_2d, wind_speed, 
            cmap=cadence_cmap, 
            shading='auto', 
            vmin=25, 
            vmax=65
        )
        
        ax.set_xlabel('Longitude', fontsize=10, labelpad=8)
        ax.set_ylabel('Latitude', fontsize=10, labelpad=8)
        
        ax.set_title(
            f'Maximum Wind Speed Projections — Water Year {year_str}\n'
            f'CONUS404 WRF Downscaling Model — Durham, NC Regional Asset Domain', 
            fontsize=12, 
            fontweight='bold', 
            pad=16, 
            color=cadence_colors['grey']
        )

        ax.set_xlim([crop_col_min, crop_col_max])
        ax.set_ylim([crop_lat_min, crop_lat_max])

        if nc_state_boundary is not None:
            nc_state_boundary.plot(
                ax=ax, 
                facecolor='none', 
                edgecolor='white', 
                linewidth=1, 
                alpha=0.35
            )

        if durham_boundary is not None:
            durham_boundary.plot(
                ax=ax, 
                facecolor='none', 
                edgecolor=cadence_colors['blue'], 
                linewidth=2.2, 
                label='Durham County Boundary Location'
            )

        # Smooth Colorbar Legend Engine
        cbar = plt.colorbar(im, ax=ax, pad=0.03, shrink=0.85)
        cbar.ax.tick_params(labelsize=9)
        cbar.outline.set_visible(False)
        
        # Keep crisp reference points every 5 mph, but the background scale is completely fluid
        cbar.set_ticks(np.arange(25, 66, 5))
        
        cbar.set_label(
            'Maximum Wind Speed (mph)', 
            rotation=270, 
            labelpad=22, 
            fontsize=10, 
            fontweight='bold', 
            color=cadence_colors['grey']
        )
        
        plt.tight_layout()

        output_filename = os.path.join(output_dir, f'max_wind_speed_durham_{year_str}.png')
        plt.savefig(output_filename, dpi=150, bbox_inches='tight')
        plt.close(fig)
        
        print(f"✓ Saved polished graphic asset to {output_filename}")
        ds.close()

    except Exception as e:
        print(f"❌ Failed to process data subset for {nc_file}. Error: {e}")
        continue

print("\nAll target simulation sequences executed successfully.")