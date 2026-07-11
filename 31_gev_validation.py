import os
import h5py
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from scipy.stats import genextreme, probplot
import warnings

# Suppress runtime warnings for plotting NaNs
warnings.filterwarnings('ignore')

def plot_spatial_heatmaps(location, scale, shape):
    """Visualizes the spatial distribution of the GEV parameters."""
    print("Generating spatial heatmaps...")
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    
    # Setup plotting limits to ignore extreme outliers in the colormap
    loc_vmin, loc_vmax = np.nanpercentile(location, [1, 99])
    scale_vmin, scale_vmax = np.nanpercentile(scale, [1, 99])
    shape_vmin, shape_vmax = np.nanpercentile(shape, [1, 99])

    # Location
    im1 = axes[0].imshow(location, cmap='viridis', origin='lower', vmin=loc_vmin, vmax=loc_vmax)
    axes[0].set_title('Location (μ) - Typical Extremes')
    fig.colorbar(im1, ax=axes[0], fraction=0.046, pad=0.04)

    # Scale
    im2 = axes[1].imshow(scale, cmap='plasma', origin='lower', vmin=scale_vmin, vmax=scale_vmax)
    axes[1].set_title('Scale (σ) - Variability')
    fig.colorbar(im2, ax=axes[1], fraction=0.046, pad=0.04)

    # Shape
    im3 = axes[2].imshow(shape, cmap='RdBu', origin='lower', vmin=-0.5, vmax=0.5)
    axes[2].set_title('Shape (ξ) - Tail Behavior\n(SciPy formulation: c = -ξ)')
    fig.colorbar(im3, ax=axes[2], fraction=0.046, pad=0.04)

    plt.tight_layout()
    plt.savefig('diagnostic_heatmaps.png', dpi=300, bbox_inches='tight')
    plt.show()

def plot_convergence_map(converged):
    """Visualizes where the MLE optimizer succeeded vs failed."""
    print("Generating convergence map...")
    plt.figure(figsize=(8, 6))
    
    # Custom colormap: Red for failed (0), Teal for converged (1)
    cmap = ListedColormap(['#d73027', '#4575b4'])
    
    im = plt.imshow(converged, cmap=cmap, origin='lower', interpolation='none')
    plt.title('MLE Convergence Status')
    
    # Custom colorbar labels
    cbar = plt.colorbar(im, ticks=[0.25, 0.75], fraction=0.046, pad=0.04)
    cbar.ax.set_yticklabels(['Failed', 'Converged'])
    
    plt.tight_layout()
    plt.savefig('diagnostic_convergence.png', dpi=300, bbox_inches='tight')
    plt.show()

def plot_parameter_histograms(location, scale, shape):
    """Plots 1D distributions of the parameters to check bounds."""
    print("Generating parameter histograms...")
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    
    valid_loc = location[~np.isnan(location)]
    valid_scale = scale[~np.isnan(scale)]
    valid_shape = shape[~np.isnan(shape)]

    axes[0].hist(valid_loc, bins=100, color='teal', alpha=0.7)
    axes[0].set_title('Location Distribution')
    axes[0].set_yscale('log') # Log scale helps spot wild outliers

    axes[1].hist(valid_scale, bins=100, color='coral', alpha=0.7)
    axes[1].set_title('Scale Distribution')
    axes[1].set_yscale('log')

    axes[2].hist(valid_shape, bins=100, color='purple', alpha=0.7)
    axes[2].set_title('Shape Distribution')
    
    plt.tight_layout()
    plt.savefig('diagnostic_histograms.png', dpi=300, bbox_inches='tight')
    plt.show()

def plot_point_diagnostics(raw_data, location, scale, shape, points):
    """Generates PDF overlays and Q-Q plots for specific grid cells."""
    print("Generating point-wise diagnostics...")
    
    # squeeze=False ensures 'axes' is always a 2D array, even if len(points) == 1
    fig, axes = plt.subplots(len(points), 2, figsize=(12, 4 * len(points)), squeeze=False)
        
    for idx, (y, x) in enumerate(points):
        # Extract data for this cell
        ts = raw_data[:, y, x]
        valid_ts = ts[~np.isnan(ts)]
        
        loc = location[y, x]
        sc = scale[y, x]
        sh = shape[y, x] 
        
        ax_pdf = axes[idx, 0]
        ax_qq = axes[idx, 1]
        
        if np.isnan(loc) or len(valid_ts) < 5:
            ax_pdf.text(0.5, 0.5, "Data/Fit missing", ha='center')
            ax_pdf.set_title(f"Grid [{y}, {x}]")
            continue
            
        # ----------------------------------------------------
        # 1. PDF Overlay
        # ----------------------------------------------------
        ax_pdf.hist(valid_ts, bins=10, density=True, alpha=0.6, color='gray', label='Empirical Data')
        
        x_theo = np.linspace(min(valid_ts)*0.8, max(valid_ts)*1.2, 100)
        pdf_theo = genextreme.pdf(x_theo, c=sh, loc=loc, scale=sc)
        
        ax_pdf.plot(x_theo, pdf_theo, 'r-', lw=2, label='GEV MLE Fit')
        ax_pdf.set_title(f"Grid [{y}, {x}] - PDF\n$\mu$={loc:.1f}, $\sigma$={sc:.1f}, $c$={sh:.2f}")
        ax_pdf.legend()
        
        # ----------------------------------------------------
        # 2. Corrected Q-Q Plot (Testing your exact parameters)
        # ----------------------------------------------------
        n = len(valid_ts)
        empirical_quantiles = np.sort(valid_ts)
        
        # Calculate theoretical plotting positions using Weibull formula i/(n+1)
        plotting_positions = np.arange(1, n + 1) / (n + 1)
        
        # Calculate theoretical quantiles using your exact MLE parameters
        theoretical_quantiles = genextreme.ppf(plotting_positions, c=sh, loc=loc, scale=sc)
        
        ax_qq.scatter(theoretical_quantiles, empirical_quantiles, color='#4575b4', alpha=0.7, edgecolor='k')
        
        # Draw 1:1 Perfect Fit Reference Line
        min_val = min(np.min(theoretical_quantiles), np.min(empirical_quantiles))
        max_val = max(np.max(theoretical_quantiles), np.max(empirical_quantiles))
        ax_qq.plot([min_val, max_val], [min_val, max_val], 'r--', lw=2, label='1:1 Perfect Fit')
        
        ax_qq.set_title(f"Grid [{y}, {x}] - Q-Q Plot")
        ax_qq.set_xlabel("Theoretical Quantiles (GEV)")
        ax_qq.set_ylabel("Empirical Quantiles (Data)")
        ax_qq.legend()
        
    plt.tight_layout()
    plt.savefig('diagnostic_points.png', dpi=300, bbox_inches='tight')
    plt.show()

def main():
    base_dir = r'c:\Users\ajj4p\Documents\GitHub\CONUS404_Processing\output'
    params_file = os.path.join(base_dir, 'gev_parameters.h5')
    raw_data_file = os.path.join(base_dir, 'validated_annual_max_data.h5')

    if not os.path.exists(params_file):
        print(f"Error: Could not find {params_file}")
        return

    # Load parameters
    print("Loading HDF5 data...")
    with h5py.File(params_file, 'r') as f:
        loc_grid = f['location'][:]
        scale_grid = f['scale'][:]
        shape_grid = f['shape'][:]
        conv_grid = f['converged'][:]
        
        south_north = f.attrs['south_north']
        west_east = f.attrs['west_east']

    # Load raw data for point diagnostics
    with h5py.File(raw_data_file, 'r') as f:
        raw_data = f['spduv10max'][:]

    # 1. Run Heatmaps
    plot_spatial_heatmaps(loc_grid, scale_grid, shape_grid)
    
    # 2. Run Convergence Map
    plot_convergence_map(conv_grid)
    
    # 3. Run Histograms
    plot_parameter_histograms(loc_grid, scale_grid, shape_grid)
    
    # 4. Run Point Diagnostics
    # Pick 3 arbitrary points distributed across the grid.
    # Adjust these indices to target specific locations of interest!
    y_mid = south_north // 2
    x_mid = west_east // 2
    
    test_points = [
        (y_mid, x_mid),                        # Center of domain
        (south_north // 4, west_east // 4),    # Bottom-left quadrant
        (int(south_north * 0.75), int(west_east * 0.75)) # Top-right quadrant
    ]
    
    plot_point_diagnostics(raw_data, loc_grid, scale_grid, shape_grid, test_points)

if __name__ == '__main__':
    main()