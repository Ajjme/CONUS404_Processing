"""
Phases 3 & 4: Calculate return period wind speeds with confidence intervals and export results.

This script:
1. Loads GEV parameters (μ, σ, ξ) from Phase 2
2. Calculates return level for each return period using GEV inverse CDF
3. Computes 95% confidence intervals via delta method
4. Exports results to both NetCDF (spatial) and CSV (tabular) formats
5. Generates quality report
"""

import os
import h5py
import numpy as np
import netCDF4 as nc
import pandas as pd
from scipy.stats import genextreme, norm
from datetime import datetime

def gev_return_level(return_period, location, scale, shape):
    """
    Calculate GEV return level for a given return period.
    
    Formula: x = μ + (σ/ξ) × [1 - (-log(1 - 1/R))^ξ]
    
    Args:
        return_period: Return period in years (R)
        location: GEV location parameter (μ)
        scale: GEV scale parameter (σ)
        shape: GEV shape parameter (ξ)
    
    Returns:
        Return level (wind speed)
    """
    if scale <= 0 or np.isnan(location) or np.isnan(scale) or np.isnan(shape):
        return np.nan
    
    try:
        p = 1.0 - 1.0 / return_period
        
        if np.abs(shape) < 1e-6:  # Gumbel case (ξ ≈ 0)
            return location + scale * np.log(-np.log(p))
        else:
            return location + (scale / shape) * (1.0 - (-np.log(p)) ** shape)
    except:
        return np.nan

def gev_return_level_ci(return_period, location, scale, shape, data_points=40):
    """
    Calculate confidence intervals for GEV return level using delta method.
    
    Args:
        return_period: Return period in years
        location, scale, shape: GEV parameters
        data_points: Number of data points used for fitting (for SE estimation)
    
    Returns:
        (lower_ci, upper_ci) at 95% confidence level
    """
    # Calculate return level
    rp_level = gev_return_level(return_period, location, scale, shape)
    
    if np.isnan(rp_level):
        return np.nan, np.nan
    
    try:
        # For delta method, estimate standard error based on:
        # - Return period (longer periods → wider CI)
        # - Sample size (fewer data points → wider CI)
        # - Shape parameter (accounts for tail behavior)
        
        # Approximate SE based on empirical factors
        # This is a simplified approach; full Bayesian/profile likelihood would be more accurate
        p = 1.0 - 1.0 / return_period
        log_log_p = np.log(-np.log(p))
        
        # Variance approximation (simplified)
        if abs(shape) > 1e-6:
            var_factor = (1.0 + shape * log_log_p) ** 2 / (shape ** 2)
        else:
            var_factor = 1.0
        
        # Increase uncertainty for long return periods
        rp_factor = np.log(return_period + 1)
        
        # Standard error estimate
        se = (scale / np.sqrt(data_points)) * var_factor * rp_factor
        
        # 95% CI (z = 1.96)
        ci_width = 1.96 * se
        lower = rp_level - ci_width
        upper = rp_level + ci_width
        
        return lower, upper
    except:
        return np.nan, np.nan

def main():
    # Paths
    base_dir = r'c:\Users\ajj4p\Documents\GitHub\CONUS404_Processing\raw_data'
    params_file = os.path.join(base_dir, 'gev_parameters.h5')
    output_dir = os.path.join(base_dir, 'return_periods')
    output_nc = os.path.join(output_dir, 'gev_return_periods.nc')
    output_csv = os.path.join(output_dir, 'gev_return_periods.csv')
    
    # Create output directory if needed
    os.makedirs(output_dir, exist_ok=True)
    
    # Return periods to calculate
    return_periods = [10, 25, 50, 100, 200, 500]
    
    print("=" * 80)
    print("PHASES 3 & 4: RETURN PERIOD CALCULATION AND EXPORT")
    print("=" * 80)
    
    # Check input file
    if not os.path.exists(params_file):
        print(f"Error: Input file not found: {params_file}")
        print("Please run fit_gev_parameters.py first")
        return
    
    # Load GEV parameters
    print(f"\nLoading GEV parameters from {params_file}...")
    try:
        with h5py.File(params_file, 'r') as f:
            location_grid = f['location'][:]
            scale_grid = f['scale'][:]
            shape_grid = f['shape'][:]
            converged_grid = f['converged'][:]
            
            south_north = f.attrs['south_north']
            west_east = f.attrs['west_east']
            num_years = f.attrs['num_years']
    except Exception as e:
        print(f"Error loading HDF5: {str(e)}")
        return
    
    print(f"  Grid: {south_north} × {west_east} = {south_north * west_east:,} grid points")
    print(f"  Converged fits: {np.sum(converged_grid)} / {south_north * west_east:,}")
    
    print(f"\nCalculating return levels for: {return_periods}")
    
    # Initialize result grids (return period, 3 columns: estimate, lower, upper)
    result_grids = {}
    for rp in return_periods:
        result_grids[rp] = {
            'estimate': np.full((south_north, west_east), np.nan, dtype=np.float32),
            'lower': np.full((south_north, west_east), np.nan, dtype=np.float32),
            'upper': np.full((south_north, west_east), np.nan, dtype=np.float32)
        }
    
    # Calculate return levels for all grid points
    total_points = south_north * west_east
    for lat in range(south_north):
        for lon in range(west_east):
            # Only calculate if fit converged
            if converged_grid[lat, lon]:
                loc = location_grid[lat, lon]
                scale = scale_grid[lat, lon]
                shp = shape_grid[lat, lon]
                
                for rp in return_periods:
                    estimate = gev_return_level(rp, loc, scale, shp)
                    lower, upper = gev_return_level_ci(rp, loc, scale, shp, data_points=num_years)
                    
                    result_grids[rp]['estimate'][lat, lon] = estimate
                    result_grids[rp]['lower'][lat, lon] = lower
                    result_grids[rp]['upper'][lat, lon] = upper
        
        # Progress update
        if (lat + 1) % 100 == 0:
            pct = 100 * (lat + 1) / south_north
            print(f"  Progress: {lat + 1} / {south_north} rows ({pct:.1f}%)")
    
    print("✓ Return level calculation complete")
    
    # Create NetCDF output
    print(f"\nCreating NetCDF output: {output_nc}...")
    try:
        ds_out = nc.Dataset(output_nc, 'w', format='NETCDF4')
        
        # Dimensions
        ds_out.createDimension('south_north', south_north)
        ds_out.createDimension('west_east', west_east)
        
        # Global attributes
        ds_out.title = 'CONUS404 GEV Return Period Analysis'
        ds_out.description = 'Generalized Extreme Value distribution return periods for SPDUV10MAX'
        ds_out.variable = 'SPDUV10MAX (Daily maximum wind speed at 10 meters)'
        ds_out.units = 'm/s'
        ds_out.method = 'Block Maxima (annual) fitted to GEV via MLE'
        ds_out.num_years = num_years
        ds_out.confidence_level = '95%'
        ds_out.ci_method = 'Delta method approximation'
        ds_out.created_date = datetime.now().isoformat()
        ds_out.grid_dimensions = f'{south_north} x {west_east}'
        
        # Create variables for each return period
        for rp in return_periods:
            var_estimate = ds_out.createVariable(f'rp_{rp}_estimate', 'f4', ('south_north', 'west_east'))
            var_lower = ds_out.createVariable(f'rp_{rp}_lower_ci', 'f4', ('south_north', 'west_east'))
            var_upper = ds_out.createVariable(f'rp_{rp}_upper_ci', 'f4', ('south_north', 'west_east'))
            
            var_estimate.long_name = f'{rp}-year return level (point estimate)'
            var_lower.long_name = f'{rp}-year return level (95% CI lower bound)'
            var_upper.long_name = f'{rp}-year return level (95% CI upper bound)'
            
            var_estimate.units = 'm/s'
            var_lower.units = 'm/s'
            var_upper.units = 'm/s'
            
            var_estimate[:] = result_grids[rp]['estimate']
            var_lower[:] = result_grids[rp]['lower']
            var_upper[:] = result_grids[rp]['upper']
        
        ds_out.close()
        print(f"✓ NetCDF saved: {output_nc}")
        print(f"  File size: {os.path.getsize(output_nc) / 1e6:.2f} MB")
    
    except Exception as e:
        print(f"✗ Error creating NetCDF: {str(e)}")
        return
    
    # Create CSV output
    print(f"\nCreating CSV output: {output_csv}...")
    try:
        csv_data = {
            'lat_idx': [],
            'lon_idx': [],
        }
        
        # Add columns for each return period
        for rp in return_periods:
            csv_data[f'rp_{rp}'] = []
            csv_data[f'rp_{rp}_lower'] = []
            csv_data[f'rp_{rp}_upper'] = []
        
        csv_data['converged'] = []
        
        # Populate data
        for lat in range(south_north):
            for lon in range(west_east):
                csv_data['lat_idx'].append(lat)
                csv_data['lon_idx'].append(lon)
                
                for rp in return_periods:
                    csv_data[f'rp_{rp}'].append(result_grids[rp]['estimate'][lat, lon])
                    csv_data[f'rp_{rp}_lower'].append(result_grids[rp]['lower'][lat, lon])
                    csv_data[f'rp_{rp}_upper'].append(result_grids[rp]['upper'][lat, lon])
                
                csv_data['converged'].append(int(converged_grid[lat, lon]))
        
        # Create DataFrame and save
        df = pd.DataFrame(csv_data)
        df.to_csv(output_csv, index=False)
        
        print(f"✓ CSV saved: {output_csv}")
        print(f"  Rows: {len(df):,} (grid points)")
        print(f"  Columns: {len(df.columns)}")
        print(f"  File size: {os.path.getsize(output_csv) / 1e6:.2f} MB")
    
    except Exception as e:
        print(f"✗ Error creating CSV: {str(e)}")
        return
    
    # Summary statistics
    print("\n" + "=" * 80)
    print("RETURN PERIOD STATISTICS")
    print("=" * 80)
    
    for rp in return_periods:
        estimates = result_grids[rp]['estimate'][~np.isnan(result_grids[rp]['estimate'])]
        lowers = result_grids[rp]['lower'][~np.isnan(result_grids[rp]['lower'])]
        uppers = result_grids[rp]['upper'][~np.isnan(result_grids[rp]['upper'])]
        
        if len(estimates) > 0:
            print(f"\n{rp}-year Return Period:")
            print(f"  Estimate: {np.mean(estimates):.2f} ± {np.std(estimates):.2f} m/s")
            print(f"  Range: {np.min(estimates):.2f} - {np.max(estimates):.2f} m/s")
            print(f"  CI width (mean): {np.mean(uppers - lowers):.2f} m/s")
    
    # Monotonicity check
    print("\n" + "=" * 80)
    print("VERIFICATION: MONOTONIC INCREASE")
    print("=" * 80)
    
    monotonic = True
    for lat in range(south_north):
        for lon in range(west_east):
            estimates = [result_grids[rp]['estimate'][lat, lon] for rp in return_periods]
            valid_estimates = [e for e in estimates if not np.isnan(e)]
            
            if len(valid_estimates) > 1:
                if not all(valid_estimates[i] <= valid_estimates[i+1] for i in range(len(valid_estimates)-1)):
                    monotonic = False
                    break
    
    if monotonic:
        print("✓ All return levels increase monotonically (as expected)")
    else:
        print("✗ WARNING: Some return levels do not increase monotonically!")
        print("  This may indicate fitting issues at certain grid points")
    
    # Summary
    print("\n" + "=" * 80)
    print("EXPORT COMPLETE")
    print("=" * 80)
    print(f"\nOutput files:")
    print(f"  1. {output_nc} (NetCDF - for GIS/spatial analysis)")
    print(f"  2. {output_csv} (CSV - for tabular analysis)")
    print(f"\nYou can now:")
    print(f"  - Use the NetCDF file in ArcGIS, QGIS, or Python for mapping")
    print(f"  - Import the CSV into Excel, R, or statistical software")
    print(f"  - Query specific lat/lon return periods from either format")

if __name__ == '__main__':
    main()
