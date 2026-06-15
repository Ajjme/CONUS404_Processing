"""
Phase 2: Fit Generalized Extreme Value (GEV) distributions using MLE at all grid points.

This script:
1. Loads validated annual max data from HDF5
2. For each grid point, fits GEV distribution to 40-year time series
3. Extracts location (μ), scale (σ), and shape (ξ) parameters
4. Uses multiprocessing for efficiency (~1.4M grid points)
5. Saves intermediate results and final consolidated parameter grids
"""

import os
import h5py
import numpy as np
import netCDF4 as nc
from scipy.stats import genextreme
from scipy.optimize import minimize
from multiprocessing import Pool, cpu_count
from functools import partial
import warnings
from datetime import datetime

warnings.filterwarnings('ignore')

# Global variable for worker processes
_validated_data = None

def fit_gev_at_gridpoint(args):
    """
    Fit GEV distribution to 40-year time series at a single grid point.
    
    Args:
        args: tuple of (lat_idx, lon_idx)
    
    Returns:
        dict with lat, lon, location, scale, shape, converged, warnings
    """
    lat_idx, lon_idx = args
    
    try:
        # Extract time series for this grid point
        time_series = _validated_data[:, lat_idx, lon_idx]
        
        # Remove NaN values
        valid_data = time_series[~np.isnan(time_series)]
        
        if len(valid_data) < 3:
            return {
                'lat': lat_idx,
                'lon': lon_idx,
                'location': np.nan,
                'scale': np.nan,
                'shape': np.nan,
                'converged': False,
                'warning': f'Insufficient valid data: {len(valid_data)} points'
            }
        
        # Fit GEV using scipy.stats.genextreme
        # genextreme parameterization: c=shape, loc=location, scale=scale
        try:
            # Use MLE fit from scipy
            params = genextreme.fit(valid_data)
            shape, location, scale = params
            
            # Verify parameters are reasonable
            if scale <= 0:
                return {
                    'lat': lat_idx,
                    'lon': lon_idx,
                    'location': np.nan,
                    'scale': np.nan,
                    'shape': np.nan,
                    'converged': False,
                    'warning': f'Invalid scale parameter: {scale}'
                }
            
            return {
                'lat': lat_idx,
                'lon': lon_idx,
                'location': float(location),
                'scale': float(scale),
                'shape': float(shape),
                'converged': True,
                'warning': None,
                'n_samples': len(valid_data)
            }
        
        except Exception as e:
            return {
                'lat': lat_idx,
                'lon': lon_idx,
                'location': np.nan,
                'scale': np.nan,
                'shape': np.nan,
                'converged': False,
                'warning': f'Fit error: {str(e)[:50]}'
            }
    
    except Exception as e:
        return {
            'lat': lat_idx,
            'lon': lon_idx,
            'location': np.nan,
            'scale': np.nan,
            'shape': np.nan,
            'converged': False,
            'warning': f'Processing error: {str(e)[:50]}'
        }

def init_worker(validated_data):
    """Initialize worker process with shared data."""
    global _validated_data
    _validated_data = validated_data

def main():
    # Paths
    base_dir = r'c:\Users\ajj4p\Documents\GitHub\CONUS404_Processing\raw_data'
    input_file = os.path.join(base_dir, 'validated_annual_max_data.h5')
    output_dir = base_dir
    output_params_file = os.path.join(output_dir, 'gev_parameters.h5')
    
    # Check input file
    if not os.path.exists(input_file):
        print(f"Error: Input file not found: {input_file}")
        print("Please run validate_annual_max_files.py first")
        return
    
    print("=" * 80)
    print("PHASE 2: GEV PARAMETER FITTING")
    print("=" * 80)
    
    # Load validated data
    print(f"\nLoading validated data from {input_file}...")
    try:
        with h5py.File(input_file, 'r') as f:
            validated_data = f['spduv10max'][:]
            num_years = f.attrs['num_years']
            south_north = f.attrs['south_north']
            west_east = f.attrs['west_east']
            years = f.attrs['years'][:]
    except Exception as e:
        print(f"Error loading HDF5: {str(e)}")
        return
    
    print(f"  Data shape: {validated_data.shape}")
    print(f"  Years: {sorted(years)}")
    print(f"  Grid: {south_north} × {west_east} = {south_north * west_east:,} grid points")
    print(f"  Memory: {validated_data.nbytes / 1e9:.2f} GB")
    
    # Prepare grid point list
    grid_points = [(lat, lon) for lat in range(south_north) for lon in range(west_east)]
    total_points = len(grid_points)
    
    print(f"\nFitting GEV to {total_points:,} grid points...")
    print(f"Using {cpu_count()} CPU cores")
    
    # Initialize parameter grids
    location_grid = np.full((south_north, west_east), np.nan, dtype=np.float32)
    scale_grid = np.full((south_north, west_east), np.nan, dtype=np.float32)
    shape_grid = np.full((south_north, west_east), np.nan, dtype=np.float32)
    converged_grid = np.zeros((south_north, west_east), dtype=np.int8)
    warning_grid = np.empty((south_north, west_east), dtype=object)
    
    # Fit using multiprocessing
    try:
        with Pool(processes=cpu_count(), initializer=init_worker, initargs=(validated_data,)) as pool:
            results = pool.imap_unordered(fit_gev_at_gridpoint, grid_points, chunksize=100)
            
            converged_count = 0
            failed_count = 0
            
            for i, result in enumerate(results):
                lat, lon = result['lat'], result['lon']
                location_grid[lat, lon] = result['location']
                scale_grid[lat, lon] = result['scale']
                shape_grid[lat, lon] = result['shape']
                converged_grid[lat, lon] = 1 if result['converged'] else 0
                warning_grid[lat, lon] = result.get('warning', '')
                
                if result['converged']:
                    converged_count += 1
                else:
                    failed_count += 1
                
                # Progress update
                if (i + 1) % 50000 == 0:
                    pct = 100 * (i + 1) / total_points
                    print(f"  Progress: {i + 1:,} / {total_points:,} ({pct:.1f}%) | Converged: {converged_count:,}")
    
    except KeyboardInterrupt:
        print("\nFitting interrupted by user")
        return
    except Exception as e:
        print(f"Error during fitting: {str(e)}")
        return
    
    # Summary
    print("\n" + "=" * 80)
    print("FIT SUMMARY")
    print("=" * 80)
    print(f"Total grid points: {total_points:,}")
    print(f"Converged fits: {converged_count:,} ({100*converged_count/total_points:.2f}%)")
    print(f"Failed fits: {failed_count:,} ({100*failed_count/total_points:.2f}%)")
    
    # Parameter statistics
    valid_locs = location_grid[~np.isnan(location_grid)]
    valid_scales = scale_grid[~np.isnan(scale_grid)]
    valid_shapes = shape_grid[~np.isnan(shape_grid)]
    
    if len(valid_locs) > 0:
        print(f"\nLocation (μ) statistics:")
        print(f"  Min: {np.min(valid_locs):.4f}")
        print(f"  Max: {np.max(valid_locs):.4f}")
        print(f"  Mean: {np.mean(valid_locs):.4f}")
        print(f"  Std: {np.std(valid_locs):.4f}")
        
        print(f"\nScale (σ) statistics:")
        print(f"  Min: {np.min(valid_scales):.4f}")
        print(f"  Max: {np.max(valid_scales):.4f}")
        print(f"  Mean: {np.mean(valid_scales):.4f}")
        print(f"  Std: {np.std(valid_scales):.4f}")
        
        print(f"\nShape (ξ) statistics:")
        print(f"  Min: {np.min(valid_shapes):.4f}")
        print(f"  Max: {np.max(valid_shapes):.4f}")
        print(f"  Mean: {np.mean(valid_shapes):.4f}")
        print(f"  Std: {np.std(valid_shapes):.4f}")
    
    # Save parameters to HDF5
    print(f"\nSaving parameters to {output_params_file}...")
    try:
        with h5py.File(output_params_file, 'w') as f:
            f.create_dataset('location', data=location_grid, compression='gzip', compression_opts=4)
            f.create_dataset('scale', data=scale_grid, compression='gzip', compression_opts=4)
            f.create_dataset('shape', data=shape_grid, compression='gzip', compression_opts=4)
            f.create_dataset('converged', data=converged_grid, compression='gzip', compression_opts=4)
            
            # Metadata
            f.attrs['south_north'] = south_north
            f.attrs['west_east'] = west_east
            f.attrs['num_years'] = num_years
            f.attrs['fit_date'] = datetime.now().isoformat()
            f.attrs['fit_method'] = 'MLE (scipy.stats.genextreme)'
            f.attrs['converged_count'] = converged_count
            f.attrs['failed_count'] = failed_count
        
        print(f"✓ Parameters saved to: {output_params_file}")
        print(f"  File size: {os.path.getsize(output_params_file) / 1e9:.3f} GB")
    
    except Exception as e:
        print(f"✗ Error saving parameters: {str(e)}")
        return
    
    # Summary
    print("\n" + "=" * 80)
    print("FITTING COMPLETE")
    print("=" * 80)
    print(f"Next steps:")
    print(f"  1. Run: python calculate_return_periods.py")
    print(f"  2. This will calculate return period wind speeds")

if __name__ == '__main__':
    main()
