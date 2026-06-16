import os
import tarfile
import glob
import shutil
import netCDF4 as nc
import numpy as np
from pathlib import Path
from datetime import datetime
import pyproj
from pyproj import Transformer

def extract_tar_archive(tar_path, extract_dir):
    """Extract tar archive to specified directory, replacing colons with underscores."""
    print(f"Extracting tar archive: {os.path.basename(tar_path)}")
    with tarfile.open(tar_path, 'r') as tar:
        for member in tar.getmembers():
            # Replace colons in filenames with underscores (Windows compatibility)
            member.name = member.name.replace(':', '_')
            tar.extract(member, path=extract_dir)
    print(f"Extraction of {os.path.basename(tar_path)} complete!")

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
    """
    print("\nComputing lat/lon from LCC projection parameters...")
    
    dx = 4000.0  # meters per grid cell
    dy = 4000.0  # meters per grid cell
    
    lat_1 = 30.0  # TRUELAT1
    lat_2 = 50.0  # TRUELAT2
    lat_0 = 39.1  # CLAT (central latitude)
    lon_0 = -97.9  # CLON (central longitude)
    
    x0 = -(west_east - 1) * dx / 2.0
    y0 = -(south_north - 1) * dy / 2.0
    
    lcc_proj = pyproj.Proj(
        proj='lcc',
        lon_0=lon_0,
        lat_0=lat_0,
        lat_1=lat_1,
        lat_2=lat_2,
        a=6370000,
        b=6370000,
        units='m'
    )
    wgs84_proj = pyproj.Proj(proj='latlong', datum='WGS84')
    transformer = Transformer.from_proj(lcc_proj, wgs84_proj, always_xy=True)
    
    x = np.arange(west_east) * dx + x0
    y = np.arange(south_north) * dy + y0
    xx, yy = np.meshgrid(x, y)
    
    lon_2d, lat_2d = transformer.transform(xx, yy)
    
    print(f"  Lat range: {lat_2d.min():.2f}° to {lat_2d.max():.2f}°")
    print(f"  Lon range: {lon_2d.min():.2f}° to {lon_2d.max():.2f}°")
    
    return lat_2d, lon_2d

def process_wrfxtrm_files(file_list, existing_max_wind=None, existing_grid_info=None):
    """
    Process a list of wrfxtrm files and update maximum SPDUV10MAX.
    Accepts existing data arrays to allow continuous accumulation across multiple tar files.
    """
    max_wind_2d = existing_max_wind
    grid_info = existing_grid_info
    
    for i, file_path in enumerate(file_list, 1):
        print(f"  [{i}/{len(file_list)}] Processing: {os.path.basename(file_path)}")
        
        try:
            ds = nc.Dataset(file_path, 'r')
            spduv_data = ds.variables['SPDUV10MAX'][:]
            
            if spduv_data.ndim == 3:
                spduv_2d = spduv_data[0, :, :]
            else:
                spduv_2d = spduv_data
            
            if grid_info is None:
                south_north = len(ds.dimensions['south_north'])
                west_east = len(ds.dimensions['west_east'])
                lat_2d, lon_2d = compute_lcc_coordinates(south_north, west_east)
                
                grid_info = {
                    'south_north': south_north,
                    'west_east': west_east,
                    'lat_2d': lat_2d,
                    'lon_2d': lon_2d,
                    'file': file_path
                }
                print(f"  Captured grid info: {south_north} x {west_east}")
            
            if max_wind_2d is None:
                max_wind_2d = spduv_2d.copy()
            else:
                max_wind_2d = np.maximum(max_wind_2d, spduv_2d)
            
            ds.close()
            
        except Exception as e:
            print(f"  Error processing {file_path}: {e}")
            continue
    
    return max_wind_2d, grid_info

def create_output_netcdf(output_path, max_wind_data, grid_info):
    """Create a new NetCDF file with maximum wind speed data and geographic coordinates."""
    print(f"\nCreating final output NetCDF file: {output_path}")
    
    south_north = grid_info['south_north']
    west_east = grid_info['west_east']
    lat_2d = grid_info['lat_2d']
    lon_2d = grid_info['lon_2d']
    
    lat_1d = lat_2d[:, 0]
    lon_1d = lon_2d[0, :]
    
    ds_out = nc.Dataset(output_path, 'w', format='NETCDF4')
    
    ds_out.createDimension('lat', south_north)
    ds_out.createDimension('lon', west_east)
    ds_out.createDimension('y', south_north)
    ds_out.createDimension('x', west_east)
    
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
    
    lat2d_var = ds_out.createVariable('lat_2d', 'f4', ('y', 'x'))
    lat2d_var.long_name = 'latitude (2D)'
    lat2d_var.units = 'degrees_north'
    lat2d_var.standard_name = 'latitude'
    lat2d_var[:] = lat_2d
    
    lon2d_var = ds_out.createVariable('lon_2d', 'f4', ('y', 'x'))
    lon2d_var.long_name = 'longitude (2D)'
    lon2d_var.units = 'degrees_east'
    lon2d_var.standard_name = 'longitude'
    lon2d_var[:] = lon_2d
    
    spduv_var = ds_out.createVariable('SPDUV10MAX', 'f4', ('lat', 'lon'), zlib=True, complevel=4)
    spduv_var.long_name = 'Maximum Water Year wind speed at 10 meters'
    spduv_var.units = 'm s-1'
    spduv_var.standard_name = 'wind_speed'
    spduv_var.coordinates = 'lat lon lat_2d lon_2d'
    spduv_var[:] = max_wind_data
    
    ds_out.title = 'CONUS404 Maximum Water Year Wind Speed at 10m (2013)'
    ds_out.history = f'Created {datetime.now().isoformat()} across 12 monthly tar archives.'
    ds_out.Conventions = 'CF-1.7'
    
    ds_out.close()
    print(f"\nOutput file created successfully!")

def main():
    # Paths configured for Water Year 2013
    raw_data_dir = r'c:\Users\ajj4p\Documents\GitHub\CONUS404_Processing\year_raw_data\water_year_2013'
    extract_dir = r'c:\Users\ajj4p\Documents\GitHub\CONUS404_Processing\year_raw_data\water_year_2013_output'
    output_file = os.path.join(raw_data_dir, 'wrfxtrm_d01_max_spduv10max_2013.nc')
    
    # Create extraction directory if it doesn't exist
    os.makedirs(extract_dir, exist_ok=True)
    
    # Find all .tar files in the folder (will match your 12 files)
    tar_files = sorted(glob.glob(os.path.join(raw_data_dir, 'wrfxtrm_conusii_*.tar')))
    
    if not tar_files:
        print(f"Error: No tar files found in {raw_data_dir}")
        return
        
    print(f"Found {len(tar_files)} tar files to process for the water year.")
    
    max_wind_data = None
    grid_info = None
    
    # Loop through each tar file one by one
    for idx, tar_file in enumerate(tar_files, 1):
        print(f"\n--- Processing Tar Archive [{idx}/{len(tar_files)}]: {os.path.basename(tar_file)} ---")
        
        # 1. Extract the current tar file
        extract_tar_archive(tar_file, extract_dir)
        
        # 2. Find the netCDF files inside the extract folder
        wrfxtrm_files = find_wrfxtrm_files(extract_dir)
        
        if not wrfxtrm_files:
            print(f"Warning: No wrfxtrm files found in {tar_file}")
            continue
            
        # 3. Process files and update the running max wind data matrix
        max_wind_data, grid_info = process_wrfxtrm_files(wrfxtrm_files, max_wind_data, grid_info)
        
        # 4. Clean up extracted files immediately to save storage space
        print(f"Cleaning up extracted files for {os.path.basename(tar_file)}...")
        for file in wrfxtrm_files:
            try:
                os.remove(file)
            except OSError:
                pass
                
    # Create final compiled output NetCDF file
    if max_wind_data is not None:
        create_output_netcdf(output_file, max_wind_data, grid_info)
        print(f"\nProcessing complete! Output saved to: {output_file}")
    else:
        print("Error: No data was successfully processed.")
        
    # Optional: Remove empty output extraction folder
    try:
        shutil.rmtree(extract_dir)
    except Exception:
        pass

if __name__ == '__main__':
    main()