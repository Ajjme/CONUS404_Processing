"""
Setup guide for running the GEV Return Period Analysis.

This file provides quick reference for running the multi-phase workflow.
"""

# ============================================================================
# QUICK START
# ============================================================================

INSTRUCTIONS = """

STEP 1: Prepare Your Data
==========================
Create the directory structure:
  raw_data/
    └── annual_max/
        ├── wrfxtrm_d01_max_spduv10max_2023.nc
        ├── wrfxtrm_d01_max_spduv10max_2022.nc
        ├── wrfxtrm_d01_max_spduv10max_2021.nc
        ...
        └── wrfxtrm_d01_max_spduv10max_1984.nc  (40 years total)

STEP 2: Run the Workflow
=========================
Option A - Run all phases at once (RECOMMENDED):
  python run_all_phases.py

Option B - Run phases individually:
  1. python validate_annual_max_files.py       (Phase 1)
  2. python fit_gev_parameters.py               (Phase 2)
  3. python calculate_return_periods.py         (Phases 3 & 4)

STEP 3: Check Output
=====================
After completion, output files will be in:
  raw_data/return_periods/
    ├── gev_return_periods.nc  (NetCDF for GIS/mapping)
    └── gev_return_periods.csv (CSV for data analysis)

Return periods calculated: 10, 25, 50, 100, 200, 500 years
Grid points: 1,015 × 1,367 = 1,386,055 cells
Confidence level: 95%


DETAILED PHASE INFORMATION
==========================

PHASE 1: validate_annual_max_files.py
--------------------------------------
Time: 1-2 minutes (depends on disk speed)
Memory: ~1 GB

Actions:
  - Finds all wrfxtrm_d01_max_spduv10max_YYYY.nc files
  - Validates grid consistency (1015 × 1367)
  - Checks for missing/invalid data
  - Loads all years into single consolidated array
  - Saves validated data to: raw_data/validated_annual_max_data.h5

Output: validated_annual_max_data.h5 (~2 GB)


PHASE 2: fit_gev_parameters.py
-------------------------------
Time: 30-60 minutes (depends on CPU cores)
Memory: 2-4 GB (varies with multiprocessing degree)

Actions:
  - Loads validated data from Phase 1
  - Uses all available CPU cores for parallel fitting
  - Fits GEV distributions at 1,386,055 grid points via MLE
  - Extracts location (μ), scale (σ), and shape (ξ) parameters
  - Flags convergence failures and warnings
  - Saves parameters to: raw_data/gev_parameters.h5

Output: gev_parameters.h5 (~300 MB)
        Progress updates printed every 50,000 grid points


PHASE 3 & 4: calculate_return_periods.py
------------------------------------------
Time: 2-5 minutes
Memory: 1-2 GB

Actions:
  - Loads GEV parameters from Phase 2
  - Calculates return levels for: 10, 25, 50, 100, 200, 500 years
  - Computes 95% confidence intervals (delta method)
  - Verifies monotonic increase of return levels
  - Exports to NetCDF and CSV formats
  - Generates summary statistics

Output: gev_return_periods.nc (NetCDF, ~80 MB)
        gev_return_periods.csv (CSV, ~500 MB)


DEPENDENCIES
============

Python packages (all installed):
  - netCDF4 (read/write NetCDF files)
  - numpy (numerical arrays)
  - scipy (GEV fitting via scipy.stats.genextreme)
  - h5py (HDF5 file I/O)
  - pandas (CSV export)


TROUBLESHOOTING
===============

Q: Script hangs or uses too much memory during Phase 2
A: The multiprocessing pool is too large. Edit fit_gev_parameters.py:
   - Find: with Pool(processes=cpu_count(), ...)
   - Change to: with Pool(processes=4, ...)  (or smaller number)

Q: "File not found" error on startup
A: Check that the required input files exist:
   - Phase 1 needs files in: raw_data/annual_max/
   - Phase 2 needs: raw_data/validated_annual_max_data.h5
   - Phase 3 needs: raw_data/gev_parameters.h5

Q: Fit convergence failures at >5% of grid points
A: This is normal for some grid points (complex wind patterns)
   - Failed points are marked in output
   - Can interpolate from neighbors post-hoc if needed
   - Use the 'converged' column in CSV to filter

Q: NetCDF dimensions incorrect
A: Verify input data:
   - Each annual max file should have shape (1015, 1367)
   - Check with: ncdump -h wrfxtrm_d01_max_spduv10max_YYYY.nc


NEXT STEPS
==========

After running all phases:

1. VISUALIZE RESULTS (GIS Software)
   - Open gev_return_periods.nc in QGIS or ArcGIS
   - Layer options: rp_10_estimate, rp_50_estimate, rp_100_estimate, etc.
   - Create maps showing spatial patterns of extreme wind speeds

2. QUERY SPECIFIC LOCATIONS (Python)
   - Load CSV into pandas
   - df.iloc[lat_idx * 1367 + lon_idx] to get specific grid cell
   - Extract return period values for analysis

3. COMPARE RETURN PERIODS (Excel/R)
   - Import CSV and create pivot tables
   - Analyze spatial variations
   - Compare different return periods

4. VALIDATE RESULTS (Statistical)
   - Cross-check a few grid points with original data
   - Verify CIs are wider for longer return periods
   - Check for outliers or anomalies


EXAMPLE: Query Specific Grid Point
===================================

import pandas as pd
import h5py

# Load return period data
df = pd.read_csv('raw_data/return_periods/gev_return_periods.csv')

# Find grid point at latitude index 500, longitude index 700
grid_point = df[(df['lat_idx'] == 500) & (df['lon_idx'] == 700)]

# Print return periods with confidence intervals
print("10-year return level:", grid_point['rp_10'].values[0], "m/s")
print("  95% CI: [", grid_point['rp_10_lower'].values[0], 
      ",", grid_point['rp_10_upper'].values[0], "]")

print("100-year return level:", grid_point['rp_100'].values[0], "m/s")
print("  95% CI: [", grid_point['rp_100_lower'].values[0], 
      ",", grid_point['rp_100_upper'].values[0], "]")


REFERENCES
==========

GEV Distribution Theory:
  - https://en.wikipedia.org/wiki/Generalized_extreme_value_distribution
  - Coles, S. (2001). An Introduction to Statistical Modeling of Extreme Values.

Python Implementation:
  - scipy.stats.genextreme: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.genextreme.html
  - NetCDF4-python: https://unidata.github.io/netcdf4-python/

Return Period Analysis:
  - Block Maxima method: https://en.wikipedia.org/wiki/Extreme_value_theory
  - Return period definition: https://en.wikipedia.org/wiki/Return_period


CONTACT / FEEDBACK
==================

For questions or issues with the scripts:
  1. Check the troubleshooting section above
  2. Review the README.md in the project root
  3. Check intermediate output files for diagnostic info
"""

if __name__ == '__main__':
    print(INSTRUCTIONS)
