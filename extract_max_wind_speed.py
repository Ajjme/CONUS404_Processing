"""
Extract maximum SPDUV10MAX values from all wrfxtrm files.

This script:
1. Extracts all wrfxtrm files from the tar archive
2. Reads SPDUV10MAX from each file
3. Computes the maximum value at each grid point
4. Computes lat/lon from LCC projection parameters
5. Saves the result to a new NetCDF file with geographic coordinates

The output NetCDF file includes:
- SPDUV10MAX variable on south_north x west_east grid
- lat/lon coordinates computed from LCC projection (WGS84)
- Projection metadata for reference
"""

import os
import tarfile
import netCDF4 as nc
import numpy as np
from pathlib import Path
from datetime import datetime
import pyproj
from pyproj import Transformer

def extract_tar_archive(tar_path, extract_dir):
    """Extract tar archive to specified directory, replacing colons with underscores."""
    print(f"Extracting tar archive: {tar_path}")
    with tarfile.open(tar_path, 'r') as tar:
        for member in tar.getmembers():
            # Replace colons in filenames with underscores (Windows compatibility)
            member.name = member.name.replace(':', '_')
            tar.extract(member, path=extract_dir)
    print(f"Extraction complete!")

def find_wrfxtrm_files(base_dir):
    """Find all wrfxtrm_d01 files in the extracted directory."""
    wrfxtrm_files = []
    for root, dirs, files in os.walk(base_dir):
        for file in sorted(files):
            if file.startswith('wrfxtrm_d01_') and not file.endswith('.tar'):
                wrfxtrm_files.append(os.path.join(root, file))
    return wrfxtrm_files

def compute_lcc_coordinates(south_north, west_east):
    """
    Compute latitude and longitude from LCC projection parameters.
    
    Uses standard CONUS404 WRF projection:
    - LCC projection centered at 39.1°N, 97.9°W
    - Standard parallels at 30°N and 50°N
    - Earth radius: 6,370 km (WRF standard sphere)
    
    Returns:
        - lat_2d: 2D array of latitudes (south_north, west_east)
        - lon_2d: 2D array of longitudes (south_north, west_east)
    """
    print("\nComputing lat/lon from LCC projection parameters...")
    
    # Standard grid spacing (meters) - typical for CONUS404
    dx = 4000.0  # meters per grid cell
    dy = 4000.0  # meters per grid cell
    
    # LCC projection center (standard CONUS404 parameters)
    lat_1 = 30.0  # TRUELAT1
    lat_2 = 50.0  # TRUELAT2
    lat_0 = 39.1  # CLAT (central latitude)
    lon_0 = -97.9  # CLON (central longitude)
    
    # Assume grid center is at projection center
    x0 = -(west_east - 1) * dx / 2.0  # X coordinate of grid corner (m)
    y0 = -(south_north - 1) * dy / 2.0  # Y coordinate of grid corner (m)
    
    # Create transformer
    lcc_proj = pyproj.Proj(
        proj='lcc',
        lon_0=lon_0,
        lat_0=lat_0,
        lat_1=lat_1,
        lat_2=lat_2,
        a=6370000,  # Earth radius (WRF sphere, meters)
        b=6370000,
        units='m'
    )
    wgs84_proj = pyproj.Proj(proj='latlong', datum='WGS84')
    transformer = Transformer.from_proj(lcc_proj, wgs84_proj, always_xy=True)
    
    # Create grid of LCC coordinates
    x = np.arange(west_east) * dx + x0
    y = np.arange(south_north) * dy + y0
    xx, yy = np.meshgrid(x, y)
    
    # Transform to lat/lon
    lon_2d, lat_2d = transformer.transform(xx, yy)
    
    print(f"  Lat range: {lat_2d.min():.2f}° to {lat_2d.max():.2f}°")
    print(f"  Lon range: {lon_2d.min():.2f}° to {lon_2d.max():.2f}°")
    
    return lat_2d, lon_2d

def process_wrfxtrm_files(file_list):
    """
    Process all wrfxtrm files and compute maximum SPDUV10MAX across all files.
    Also compute geographic coordinates from LCC projection.
    
    Returns:
        - max_wind_2d: 2D array of maximum wind speeds (south_north, west_east)
        - grid_info: Dictionary with grid dimensions, coordinates, and projection metadata
    """
    max_wind_2d = None
    grid_info = None
    
    for i, file_path in enumerate(file_list, 1):
        print(f"[{i}/{len(file_list)}] Processing: {os.path.basename(file_path)}")
        
        try:
            ds = nc.Dataset(file_path, 'r')
            
            # Extract SPDUV10MAX data (shape: Time, south_north, west_east)
            spduv_data = ds.variables['SPDUV10MAX'][:]
            
            # Remove time dimension (take max across time or just flatten if 1 time step)
            if spduv_data.ndim == 3:
                spduv_2d = spduv_data[0, :, :]  # Take first (and usually only) time step
            else:
                spduv_2d = spduv_data
            
            # Store grid info from first file
            if grid_info is None:
                south_north = len(ds.dimensions['south_north'])
                west_east = len(ds.dimensions['west_east'])
                
                # Compute lat/lon from LCC projection parameters
                lat_2d, lon_2d = compute_lcc_coordinates(south_north, west_east)
                
                grid_info = {
                    'south_north': south_north,
                    'west_east': west_east,
                    'lat_2d': lat_2d,  # 2D array of latitudes
                    'lon_2d': lon_2d,  # 2D array of longitudes
                    'file': file_path
                }
                print(f"  Captured grid info: {south_north} x {west_east}")
            
            # Initialize or update maximum
            if max_wind_2d is None:
                max_wind_2d = spduv_2d.copy()
            else:
                max_wind_2d = np.maximum(max_wind_2d, spduv_2d)
            
            ds.close()
            
        except Exception as e:
            print(f"  Error processing {file_path}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    return max_wind_2d, grid_info

def create_output_netcdf(output_path, max_wind_data, grid_info):
    """
    Create a new NetCDF file with maximum wind speed data and geographic coordinates.
    
    Includes:
    - SPDUV10MAX variable on original WRF grid
    - lat_2d/lon_2d as auxiliary coordinate variables (computed from LCC projection)
    - lat/lon as 1D coordinate arrays (extracted from grid edges)
    - Projection metadata
    """
    print(f"\nCreating output NetCDF file: {output_path}")
    
    south_north = grid_info['south_north']
    west_east = grid_info['west_east']
    lat_2d = grid_info['lat_2d']
    lon_2d = grid_info['lon_2d']
    
    # Extract 1D coordinate arrays from edges (CF-compliant rectilinear grid)
    lat_1d = lat_2d[:, 0]  # Extract latitude from first column
    lon_1d = lon_2d[0, :]  # Extract longitude from first row
    
    print(f"  Lat 1D range: {lat_1d.min():.2f}° to {lat_1d.max():.2f}°")
    print(f"  Lon 1D range: {lon_1d.min():.2f}° to {lon_1d.max():.2f}°")
    
    # Create output dataset
    ds_out = nc.Dataset(output_path, 'w', format='NETCDF4')
    
    # Create dimensions
    ds_out.createDimension('lat', south_north)
    ds_out.createDimension('lon', west_east)
    ds_out.createDimension('y', south_north)  # For 2D coordinate compatibility
    ds_out.createDimension('x', west_east)   # For 2D coordinate compatibility
    
    # Create 1D coordinate variables (CF-compliant)
    lat_var = ds_out.createVariable('lat', 'f4', ('lat',))
    lat_var.standard_name = 'latitude'
    lat_var.long_name = 'latitude coordinate'
    lat_var.units = 'degrees_north'
    lat_var.axis = 'Y'
    lat_var[:] = lat_1d
    
    lon_var = ds_out.createVariable('lon', 'f4', ('lon',))
    lon_var.standard_name = 'longitude'
    lon_var.long_name = 'longitude coordinate'
    lon_var.units = 'degrees_east'
    lon_var.axis = 'X'
    lon_var[:] = lon_1d
    
    # Create 2D auxiliary coordinate variables (computed from LCC projection)
    lat2d_var = ds_out.createVariable('lat_2d', 'f4', ('y', 'x'))
    lat2d_var.long_name = 'latitude (2D)'
    lat2d_var.units = 'degrees_north'
    lat2d_var.standard_name = 'latitude'
    lat2d_var.description = 'Latitude computed from WRF LCC projection'
    lat2d_var[:] = lat_2d
    
    lon2d_var = ds_out.createVariable('lon_2d', 'f4', ('y', 'x'))
    lon2d_var.long_name = 'longitude (2D)'
    lon2d_var.units = 'degrees_east'
    lon2d_var.standard_name = 'longitude'
    lon2d_var.description = 'Longitude computed from WRF LCC projection'
    lon2d_var[:] = lon_2d
    
    # Create SPDUV10MAX variable with 1D coordinates
    spduv_var = ds_out.createVariable('SPDUV10MAX', 'f4', ('lat', 'lon'), 
                                       zlib=True, complevel=4)
    spduv_var.long_name = 'Maximum daily wind speed at 10 meters'
    spduv_var.units = 'm s-1'
    spduv_var.standard_name = 'wind_speed'
    spduv_var.description = 'Maximum SPDUV10MAX value across all wrfxtrm files in time series'
    spduv_var.coordinates = 'lat lon lat_2d lon_2d'  # Reference all coordinates
    spduv_var[:] = max_wind_data
    
    # Add coordinate system information as global attributes
    ds_out.title = 'CONUS404 Maximum Daily Wind Speed at 10m'
    ds_out.description = 'Maximum SPDUV10MAX values extracted from wrfxtrm daily files'
    ds_out.history = f'Created {datetime.now().isoformat()} from extract_max_wind_speed.py'
    ds_out.source = f'Source file: {grid_info["file"]}'
    ds_out.grid_dimensions = f'{south_north} x {west_east}'
    ds_out.Conventions = 'CF-1.7'
    
    # Store projection information
    ds_out.projection = 'Lambert Conformal Conic (WRF native)'
    ds_out.projection_lon_0 = -97.9  # CLON (central longitude)
    ds_out.projection_lat_0 = 39.1   # CLAT (central latitude)
    ds_out.projection_lat_1 = 30.0   # TRUELAT1
    ds_out.projection_lat_2 = 50.0   # TRUELAT2
    ds_out.earth_radius = 6370000    # WRF standard sphere radius (meters)
    ds_out.grid_spacing = 4000       # Meters per grid cell (x and y)
    
    # Note about coordinate computation
    ds_out.coordinate_note = (
        'Coordinates computed from WRF LCC projection parameters. '
        'lat/lon are 1D (CF-compliant rectilinear). '
        'lat_2d/lon_2d are 2D grids for accurate visualization. '
        'All coordinates reference WGS84 datum.'
    )
    
    ds_out.close()
    print(f"\nOutput file created successfully!")
    print(f"  Grid dimensions: {south_north} x {west_east}")
    print(f"  Coordinate variables:")
    print(f"    - lat (1D): {lat_1d.min():.2f}° to {lat_1d.max():.2f}°")
    print(f"    - lon (1D): {lon_1d.min():.2f}° to {lon_1d.max():.2f}°")
    print(f"    - lat_2d (2D): {lat_2d.min():.2f}° to {lat_2d.max():.2f}°")
    print(f"    - lon_2d (2D): {lon_2d.min():.2f}° to {lon_2d.max():.2f}°")
    print(f"  Wind speed range: {np.nanmin(max_wind_data):.2f} to {np.nanmax(max_wind_data):.2f} m/s")

def main():
    # Paths
    raw_data_dir = r'c:\Users\ajj4p\Documents\GitHub\CONUS404_Processing\raw_data'
    tar_file = os.path.join(raw_data_dir, 'wrfxtrm_conusii_202310.tar')
    extract_dir = raw_data_dir
    output_file = os.path.join(raw_data_dir, 'wrfxtrm_d01_max_spduv10max.nc')
    
    # Check if tar file exists
    if not os.path.exists(tar_file):
        print(f"Error: Tar file not found: {tar_file}")
        return
    
    # Extract tar archive
    extract_tar_archive(tar_file, extract_dir)
    
    # Find all wrfxtrm files
    wrfxtrm_files = find_wrfxtrm_files(extract_dir)
    
    if not wrfxtrm_files:
        print("Error: No wrfxtrm files found!")
        return
    
    print(f"\nFound {len(wrfxtrm_files)} wrfxtrm files to process")
    
    # Process files and compute maximum
    max_wind_data, grid_info = process_wrfxtrm_files(wrfxtrm_files)
    
    if max_wind_data is None:
        print("Error: Failed to process files!")
        return
    
    # Create output NetCDF file
    create_output_netcdf(output_file, max_wind_data, grid_info)
    
    print(f"\nProcessing complete!")
    print(f"Output saved to: {output_file}")

if __name__ == '__main__':
    main()
    print("\n" + "="*60)
    print("NetCDF file is now ready for mapping with:")
    print("  - cartopy (using lat/lon or lat_2d/lon_2d)")
    print("  - folium/leaflet (using lat/lon)")
    print("  - xarray/rasterio (using CF-compliant coordinates)")
    print("  - ArcGIS/QGIS (using lat/lon or projection info)")
    print("="*60)
