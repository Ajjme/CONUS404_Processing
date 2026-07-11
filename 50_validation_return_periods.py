"""
Phase 5: Visualization and Validation of GEV Return Periods.

This script reads the NetCDF output from Phase 4 and generates:
1. Spatial maps of return level estimates
2. Maps of confidence interval widths (uncertainty)
3. Return level curves with 95% confidence bands for sampled points
"""
"""
=============================================================================
VISUALIZATION CHECKS & VALIDATION GUIDE
-----------------------------------------------------------------------------
After generating the visualization plots, review them for the following quality 
indicators to ensure the GEV fitting and return period calculations are both 
physically and statistically sound:

1. SPATIAL MAPS (spatial_map_XXXyr.png)
   - Geographic Coherence: You should see recognizable meteorological and 
     topographical patterns (e.g., higher extreme wind speeds over the Great 
     Plains, exposed coastal regions, or high-elevation mountain ridges).
   - Spatial Smoothness vs. Noise: If the map looks like random "TV static", 
     the GEV fits may not have converged reliably across neighboring cells, 
     or the input block maxima data contains excessive noise.
   - Physical Realism: For 10-meter wind speeds (SPDUV10MAX), 100-year return 
     levels typically range from 25 m/s to 60+ m/s depending on the region 
     (e.g., higher in hurricane zones). Check the colorbar to ensure values 
     aren't impossibly high (e.g., >150 m/s) or negative.

2. UNCERTAINTY MAPS (uncertainty_map_XXXyr.png)
   - Expected Uncertainty Zones: High uncertainty (wide confidence intervals) 
     is entirely normal in areas dominated by rare, extreme events (like 
     hurricane tracks along the Gulf/Atlantic coasts) where the probability 
     distribution has a "heavy tail".
   - Convergence Artifacts: Isolated "hotspots" or single pixels of extreme 
     uncertainty usually indicate grid points where the Maximum Likelihood 
     Estimation (MLE) algorithm struggled to fit the shape parameter accurately.
   - Boundary Handling: Ensure areas outside the CONUS404 domain properly 
     render as blank/NaN rather than defaulting to zero or extreme values.

3. RETURN LEVEL CURVES (return_level_curves.png)
   - Monotonic Increase: The solid central estimate lines MUST slope upward 
     from left to right. A 100-year wind event must inherently be stronger 
     than a 10-year wind event.
   - Extrapolation Flaring (Horn Shape): The shaded confidence bands should 
     be relatively narrow at the 10-year mark (where historical data is 
     abundant) and widen significantly as you move toward the 200/500-year 
     marks. This reflects the mathematical penalty of extrapolating far 
     beyond the historical record.
   - Curve Shape (Tail Behavior): 
     * Concave down (flattening): Indicates a negative shape parameter 
       (Weibull distribution), suggesting wind speeds have an upper physical bound.
     * Straight line (on semilog plot): Indicates a shape parameter near 
       zero (Gumbel distribution).
     * Concave up (steepening): Indicates a positive shape parameter 
       (Fréchet distribution), implying "heavy tails" and a higher risk of 
       extreme outlier events.
=============================================================================
"""

import os
import numpy as np
import netCDF4 as nc
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

def setup_directories():
    """Define and create necessary directories."""
    base_dir = r'c:\Users\ajj4p\Documents\GitHub\CONUS404_Processing\raw_data\return_periods'
    input_nc = os.path.join(base_dir, 'gev_return_periods.nc')
    vis_dir = os.path.join(base_dir, 'visualizations')
    
    os.makedirs(vis_dir, exist_ok=True)
    return input_nc, vis_dir

def plot_spatial_map(ds, rp, vis_dir):
    """Plot a 2D map of the return level estimate for a given return period."""
    print(f"Generating spatial map for {rp}-year return period...")
    
    var_name = f'rp_{rp}_estimate'
    if var_name not in ds.variables:
        print(f"Error: Variable {var_name} not found in NetCDF.")
        return
        
    data = ds.variables[var_name][:]
    
    plt.figure(figsize=(10, 8))
    # Using origin='lower' assuming NetCDF arrays are stored South-to-North
    im = plt.imshow(data, cmap='turbo', origin='lower') 
    plt.colorbar(im, label='Wind Speed (m/s)', extend='both')
    
    plt.title(f'CONUS404 {rp}-Year Return Level Estimate (SPDUV10MAX)')
    plt.xlabel('West-East Grid Index')
    plt.ylabel('South-North Grid Index')
    
    out_path = os.path.join(vis_dir, f'spatial_map_{rp}yr.png')
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ Saved: {out_path}")

def plot_uncertainty_map(ds, rp, vis_dir):
    """Plot the width of the 95% confidence interval to visualize uncertainty."""
    print(f"Generating uncertainty map for {rp}-year return period...")
    
    upper_var = f'rp_{rp}_upper_ci'
    lower_var = f'rp_{rp}_lower_ci'
    
    upper_data = ds.variables[upper_var][:]
    lower_data = ds.variables[lower_var][:]
    
    # Calculate CI width
    ci_width = upper_data - lower_data
    
    plt.figure(figsize=(10, 8))
    im = plt.imshow(ci_width, cmap='magma', origin='lower')
    plt.colorbar(im, label='95% CI Width (m/s)', extend='max')
    
    plt.title(f'Uncertainty (95% CI Width) for {rp}-Year Return Level')
    plt.xlabel('West-East Grid Index')
    plt.ylabel('South-North Grid Index')
    
    out_path = os.path.join(vis_dir, f'uncertainty_map_{rp}yr.png')
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ Saved: {out_path}")

def plot_return_level_curves(ds, vis_dir, num_samples=3):
    """Plot return period vs wind speed curves for random valid grid points."""
    print("Generating return level curves for sampled points...")
    
    return_periods = [10, 25, 50, 100, 200, 500]
    
    # Find valid points (where the 10-year estimate is not NaN)
    valid_mask = ~np.isnan(ds.variables['rp_10_estimate'][:])
    valid_coords = np.argwhere(valid_mask)
    
    if len(valid_coords) == 0:
        print("No valid data points found to plot.")
        return
        
    # Pick random points, or use all if fewer than requested
    np.random.seed(42)  # For reproducibility
    sample_indices = np.random.choice(
        len(valid_coords), 
        size=min(num_samples, len(valid_coords)), 
        replace=False
    )
    sampled_points = valid_coords[sample_indices]
    
    plt.figure(figsize=(12, 6))
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    
    for i, (lat, lon) in enumerate(sampled_points):
        estimates = []
        lowers = []
        uppers = []
        
        for rp in return_periods:
            estimates.append(ds.variables[f'rp_{rp}_estimate'][lat, lon])
            lowers.append(ds.variables[f'rp_{rp}_lower_ci'][lat, lon])
            uppers.append(ds.variables[f'rp_{rp}_upper_ci'][lat, lon])
            
        color = colors[i % len(colors)]
        label = f'Grid Point (Y:{lat}, X:{lon})'
        
        # Plot central estimate
        plt.semilogx(return_periods, estimates, marker='o', linestyle='-', 
                     color=color, linewidth=2, label=label)
        
        # Plot confidence bands
        plt.fill_between(return_periods, lowers, uppers, 
                         color=color, alpha=0.15)
        
        # Plot bounds as dashed lines
        plt.semilogx(return_periods, lowers, linestyle='--', color=color, alpha=0.5)
        plt.semilogx(return_periods, uppers, linestyle='--', color=color, alpha=0.5)

    plt.grid(True, which="both", ls="-", alpha=0.2)
    plt.title('Return Level Curves with 95% Confidence Intervals')
    plt.xlabel('Return Period (Years)')
    plt.ylabel('Wind Speed (m/s)')
    plt.xticks(return_periods, [str(rp) for rp in return_periods])
    plt.legend()
    
    out_path = os.path.join(vis_dir, 'return_level_curves.png')
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ Saved: {out_path}")

def main():
    print("=" * 80)
    print("PHASE 5: VISUALIZATION AND VALIDATION")
    print("=" * 80)
    
    input_nc, vis_dir = setup_directories()
    
    if not os.path.exists(input_nc):
        print(f"Error: Input NetCDF file not found at {input_nc}")
        print("Please ensure Phases 3 & 4 ran successfully.")
        return
        
    try:
        ds = nc.Dataset(input_nc, 'r')
        
        # 1. Plot Spatial Maps (using 100-year return period as standard)
        plot_spatial_map(ds, rp=100, vis_dir=vis_dir)
        
        # 2. Plot Uncertainty Map (using 100-year return period)
        plot_uncertainty_map(ds, rp=100, vis_dir=vis_dir)
        
        # 3. Plot Return Level Curves (Random sample of points)
        plot_return_level_curves(ds, vis_dir=vis_dir, num_samples=3)
        
        ds.close()
        
        print("\n" + "=" * 80)
        print(f"VISUALIZATIONS COMPLETE. Check the '{vis_dir}' directory.")
        print("=" * 80)
        
    except Exception as e:
        print(f"An error occurred during visualization: {str(e)}")

if __name__ == '__main__':
    main()