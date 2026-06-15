"""
Phase 1: Validate and load 40 years of annual maximum wind speed data.

This script:
1. Scans raw_data/annual_max/ for all wrfxtrm_d01_max_spduv10max_YYYY.nc files
2. Validates each file (grid consistency, variable presence)
3. Loads all years into a single consolidated array
4. Saves validated data as intermediate HDF5 for downstream processing
"""

import os
import glob
import netCDF4 as nc
import numpy as np
import h5py
from pathlib import Path
from datetime import datetime

def find_annual_max_files(base_dir):
    """Find all annual max wrfxtrm files in the directory."""
    pattern = os.path.join(base_dir, 'wrfxtrm_d01_max_spduv10max_*.nc')
    files = sorted(glob.glob(pattern))
    return files

def extract_year_from_filename(filename):
    """Extract year from filename pattern: wrfxtrm_d01_max_spduv10max_YYYY.nc"""
    basename = os.path.basename(filename)
    try:
        year = int(basename.split('_')[-1].replace('.nc', ''))
        return year
    except (ValueError, IndexError):
        return None

def validate_file(file_path):
    """
    Validate a single annual max NetCDF file.
    
    Returns:
        (is_valid, grid_shape, data, errors/warnings)
    """
    errors = []
    warnings = []
    data = None
    grid_shape = None
    
    try:
        ds = nc.Dataset(file_path, 'r')
        
        # Check dimensions
        if 'south_north' not in ds.dimensions or 'west_east' not in ds.dimensions:
            errors.append("Missing south_north or west_east dimension")
            ds.close()
            return False, None, None, errors
        
        south_north = len(ds.dimensions['south_north'])
        west_east = len(ds.dimensions['west_east'])
        grid_shape = (south_north, west_east)
        
        # Check SPDUV10MAX variable
        if 'SPDUV10MAX' not in ds.variables:
            errors.append("Missing SPDUV10MAX variable")
            ds.close()
            return False, grid_shape, None, errors
        
        # Extract data
        spduv = ds.variables['SPDUV10MAX'][:]
        
        # Handle dimensions
        if spduv.ndim == 3:
            spduv = spduv[0, :, :]  # Take first time step
        elif spduv.ndim != 2:
            errors.append(f"Unexpected dimensions: {spduv.shape}")
            ds.close()
            return False, grid_shape, None, errors
        
        # Check for expected grid
        if spduv.shape != grid_shape:
            errors.append(f"Data shape {spduv.shape} doesn't match grid {grid_shape}")
            ds.close()
            return False, grid_shape, None, errors
        
        # Data quality checks
        nan_count = np.isnan(spduv).sum()
        if nan_count > 0:
            warnings.append(f"{nan_count} NaN values found ({100*nan_count/spduv.size:.2f}%)")
        
        # Check for reasonable wind speed values (0-100 m/s)
        valid_data = spduv[~np.isnan(spduv)]
        if len(valid_data) > 0:
            if valid_data.min() < 0:
                warnings.append(f"Negative wind speeds found: min={valid_data.min()}")
            if valid_data.max() > 100:
                warnings.append(f"Very high wind speeds found: max={valid_data.max()}")
        
        data = spduv
        ds.close()
        is_valid = len(errors) == 0
        return is_valid, grid_shape, data, errors, warnings
        
    except Exception as e:
        errors.append(f"Error reading file: {str(e)}")
        return False, None, None, errors

def main():
    # Paths
    base_dir = r'c:\Users\ajj4p\Documents\GitHub\CONUS404_Processing\raw_data\annual_max'
    output_dir = r'c:\Users\ajj4p\Documents\GitHub\CONUS404_Processing\raw_data'
    output_file = os.path.join(output_dir, 'validated_annual_max_data.h5')
    
    # Check if directory exists
    if not os.path.exists(base_dir):
        print(f"Error: Directory not found: {base_dir}")
        print(f"Please create the directory and populate it with annual max files.")
        return
    
    # Find all files
    files = find_annual_max_files(base_dir)
    
    if not files:
        print(f"Error: No annual max files found in {base_dir}")
        print(f"Expected files matching pattern: wrfxtrm_d01_max_spduv10max_YYYY.nc")
        return
    
    print(f"Found {len(files)} annual max files\n")
    print("=" * 80)
    print("VALIDATING FILES")
    print("=" * 80)
    
    # Validate each file
    valid_data = {}
    year_list = []
    reference_grid = None
    
    for file_path in files:
        year = extract_year_from_filename(file_path)
        basename = os.path.basename(file_path)
        
        is_valid, grid_shape, data, errors, warnings = validate_file(file_path)
        
        status = "✓ VALID" if is_valid else "✗ INVALID"
        print(f"\n{status}: {basename} (Year: {year})")
        
        if errors:
            print(f"  Errors:")
            for err in errors:
                print(f"    - {err}")
        
        if warnings:
            print(f"  Warnings:")
            for warn in warnings:
                print(f"    - {warn}")
        
        if is_valid:
            # Set reference grid from first valid file
            if reference_grid is None:
                reference_grid = grid_shape
            
            # Check grid consistency
            if grid_shape != reference_grid:
                print(f"  ERROR: Grid mismatch! Expected {reference_grid}, got {grid_shape}")
                continue
            
            valid_data[year] = data
            year_list.append(year)
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total files found: {len(files)}")
    print(f"Valid files: {len(valid_data)}")
    print(f"Years loaded: {sorted(year_list)}")
    print(f"Grid dimensions: {reference_grid}")
    
    if len(valid_data) == 0:
        print("\nError: No valid files found! Cannot proceed.")
        return
    
    # Create consolidated array
    print(f"\nCreating consolidated array...")
    
    # Sort by year
    sorted_years = sorted(valid_data.keys())
    num_years = len(sorted_years)
    south_north, west_east = reference_grid
    
    # Initialize array
    consolidated_data = np.zeros((num_years, south_north, west_east), dtype=np.float32)
    
    for i, year in enumerate(sorted_years):
        consolidated_data[i, :, :] = valid_data[year]
    
    print(f"Consolidated array shape: {consolidated_data.shape}")
    print(f"Data type: {consolidated_data.dtype}")
    print(f"Memory usage: {consolidated_data.nbytes / 1e9:.2f} GB")
    
    # Compute statistics
    print(f"\nData statistics (all years combined):")
    valid_mask = ~np.isnan(consolidated_data)
    if valid_mask.sum() > 0:
        print(f"  Min wind speed: {np.nanmin(consolidated_data):.2f} m/s")
        print(f"  Max wind speed: {np.nanmax(consolidated_data):.2f} m/s")
        print(f"  Mean wind speed: {np.nanmean(consolidated_data):.2f} m/s")
        print(f"  Std dev wind speed: {np.nanstd(consolidated_data):.2f} m/s")
        print(f"  Total NaN values: {(~valid_mask).sum()} ({100*(~valid_mask).sum()/valid_mask.size:.2f}%)")
    
    # Save to HDF5
    print(f"\nSaving validated data to HDF5...")
    try:
        with h5py.File(output_file, 'w') as f:
            # Save consolidated data
            ds_data = f.create_dataset('spduv10max', data=consolidated_data, compression='gzip', compression_opts=4)
            
            # Save metadata
            f.attrs['num_years'] = num_years
            f.attrs['south_north'] = south_north
            f.attrs['west_east'] = west_east
            f.attrs['years'] = np.array(sorted_years, dtype=np.int32)
            f.attrs['validation_date'] = datetime.now().isoformat()
            f.attrs['variable_name'] = 'SPDUV10MAX'
            f.attrs['units'] = 'm/s'
            f.attrs['description'] = 'Annual maximum daily wind speed at 10 meters'
            
            # Save per-year metadata
            years_group = f.create_group('years')
            for year in sorted_years:
                years_group.attrs[f'year_{year}'] = sorted_years.index(year)
        
        print(f"✓ Data saved to: {output_file}")
        print(f"  File size: {os.path.getsize(output_file) / 1e9:.2f} GB")
        
    except Exception as e:
        print(f"✗ Error saving HDF5: {str(e)}")
        return
    
    # Summary report
    print("\n" + "=" * 80)
    print("VALIDATION COMPLETE")
    print("=" * 80)
    print(f"Next steps:")
    print(f"  1. Run: python fit_gev_parameters.py")
    print(f"  2. This will fit GEV distributions at all grid points")
    print(f"  3. Then run: python calculate_return_periods.py")

if __name__ == '__main__':
    main()
