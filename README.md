# CONUS404_Processing

Opening Tar files and turning data into 40 max yearly points for every geo-location, then computing extreme value statistics (GEV) to determine wind speed return periods.

---

## Overview

This project processes CONUS404 WRF extreme (wrfxtrm) data to:
1. Extract annual maximum daily wind speeds (SPDUV10MAX) for each year
2. Fit Generalized Extreme Value (GEV) distributions using 40 years of annual maxima (Block Maxima method)
3. Calculate return period wind speeds (10, 25, 50, 100, 200, 500 years) with 95% confidence intervals
4. Export results as both NetCDF (spatial) and CSV (tabular) formats

---

## Project Workflow

### Phase 1: Data Validation & Loading
**Goal:** Consolidate 40 years of annual maximum wind speed data into a single validated array.

- Scan `raw_data/annual_max/` for all files matching pattern `wrfxtrm_d01_max_spduv10max_YYYY.nc`
- Validate each file:
  - Check grid consistency (1015 × 1367 lat/lon)
  - Verify SPDUV10MAX variable exists
  - Flag years with missing or incomplete data
- Load all 40 years into single array: shape (40, 1015, 1367)
- Create metadata mapping (year → file, grid info, data quality flags)

**Output:** Validated data array, year list, grid info dictionary

**Script:** `validate_annual_max_files.py`

---

### Phase 2: GEV Parameter Estimation (Multiprocessing)
**Goal:** Fit Generalized Extreme Value distributions at each grid point using Maximum Likelihood Estimation.

- For each grid point (1,366,055 total cells):
  - Extract 40-year time series: `data[:, lat_i, lon_j]`
  - Fit GEV distribution using MLE (via `scipy.stats.genextreme` or `pyextremes`)
  - Extract and store parameters: location (μ), scale (σ), shape (ξ)
  - Flag convergence failures and warning conditions
- Parallelize across all available CPU cores for efficiency
- Save intermediate results to prevent re-computation:
  - One file per 100 lat slices (10–15 files total)
  - Format: HDF5 or NumPy .npz with shape (100 or fewer, 1367, 3 params)
- Aggregate all results into unified parameter grids

**Output:** GEV parameter grids (μ, σ, ξ) saved as NetCDF interim files

**Script:** `fit_gev_parameters.py`

---

### Phase 3: Return Period Calculation
**Goal:** Compute wind speed return levels and confidence intervals for specified return periods.

- Load GEV parameters for all grid points
- For each return period R in [10, 25, 50, 100, 200, 500]:
  - Calculate return level using GEV inverse CDF (quantile function): `x = μ + (σ/ξ) × [1 - (-log(1 - 1/R))^ξ]`
  - Calculate 95% confidence interval (lower & upper bounds) via profile likelihood or delta method
  - Handle cases where fitting failed: interpolate from neighbors or mark as NaN
- Verify monotonic increase (RP_10 < RP_25 < … < RP_500)
- Create output arrays per return period: (1015, 1367) grids for estimate, lower CI, upper CI

**Output:** Return period estimates and confidence intervals for all grid points

**Script:** `calculate_return_periods.py` (handles both Phase 3 and Phase 4 below)

---

### Phase 4: Output Generation
**Goal:** Export results in spatial (NetCDF) and tabular (CSV) formats for analysis and visualization.

#### NetCDF Output (`gev_return_periods.nc`)
- **Dimensions:** south_north (1015), west_east (1367)
- **Variables per return period:** `rp_10_estimate`, `rp_10_lower_ci`, `rp_10_upper_ci`, …, `rp_500_estimate`, `rp_500_lower_ci`, `rp_500_upper_ci`
- **Coordinates:** XLONG, XLAT (if available from source files)
- **Global Attributes:**
  - Fitting method: Maximum Likelihood Estimation (MLE)
  - Confidence level: 95%
  - Number of years: 40
  - Data source: CONUS404 wrfxtrm files
  - Date generated: timestamp

#### CSV Output (`gev_return_periods.csv`)
- **Rows:** 1,366,055 (one per grid point) + header
- **Columns:** lat_idx, lon_idx, rp_10, rp_10_lower, rp_10_upper, rp_25, …, rp_500, rp_500_lower, rp_500_upper, fit_status
- **fit_status:** success, failed, flagged (for traceability)
- Facilitates import into GIS, data analysis tools, or statistical software

**Output Location:** `raw_data/return_periods/`

**Script:** `calculate_return_periods.py`

---

## File Structure

```
raw_data/
├── wrfxtrm_conusii_202310.tar              # Original tar archive (Oct 2023 sample)
├── annual_max/
│   ├── wrfxtrm_d01_max_spduv10max_2023.nc  # Annual max for 2023
│   ├── wrfxtrm_d01_max_spduv10max_2022.nc  # Annual max for 2022
│   ├── ...
│   └── wrfxtrm_d01_max_spduv10max_1984.nc  # Annual max for 1984 (40-year span)
└── return_periods/
    ├── gev_return_periods.nc               # NetCDF with return period grids
    └── gev_return_periods.csv              # CSV with tabular results
```

---

## Key Technical Details

### Fitting Method
- **Block Maxima:** Each "block" is one calendar year; we take the annual maximum SPDUV10MAX at each grid point
- **Distribution:** Generalized Extreme Value (GEV), more flexible than Gumbel or Weibull
  - Handles different tail behaviors (bounded, unbounded, heavy-tailed)
  - Parameters: location (μ), scale (σ), shape (ξ)
- **Estimation:** Maximum Likelihood Estimation (MLE)
  - Industry standard for ~40 data points
  - Automatically handled by `scipy.stats.genextreme` or `pyextremes`

### Return Period Definition
- **Return Period R (years):** Expected time between exceedances of a given wind speed
- **Return Level:** Wind speed x such that `P(X > x) = 1/R`
- **Inverse CDF formula:** For GEV with shape ξ ≠ 0:
  ```
  x = μ + (σ / ξ) × [1 - (-log(1 - 1/R))^ξ]
  ```

### Confidence Intervals
- **Method:** 95% profile likelihood or delta method
- **Interpretation:** Reflects uncertainty from fitting 40-year sample
  - Intervals widen significantly for long return periods (e.g., 200+ years)
  - Mathematically correct for small sample sizes
- **Access:** Available via `model.distribution.fit_result` if using `pyextremes`

### Data Quality Handling
- **Invalid values:** Kept as-is (no outlier removal)
- **Missing years:** Procedure proceeds with available years (no strict 40-year enforcement)
- **Failed fits:** Flagged in output; user can interpolate or analyze further if needed

---

## Scripts

### `extract_max_wind_speed.py` (Existing)
Processes tar archive of wrfxtrm files to create annual maximum NetCDF file.
- Input: `wrfxtrm_conusii_YYYYMM.tar`
- Output: `wrfxtrm_d01_max_spduv10max_YYYY.nc`
- Usage: `python extract_max_wind_speed.py`

### `validate_annual_max_files.py` (New)
Validates and loads 40 years of annual max files.
- Input: 40 files from `raw_data/annual_max/`
- Output: Validated data array (40, 1015, 1367), metadata, quality report
- Usage: `python validate_annual_max_files.py`

### `fit_gev_parameters.py` (New)
Fits GEV distributions using MLE at all grid points (multiprocessing).
- Input: Validated data array from Phase 1
- Output: GEV parameters (μ, σ, ξ) stored as .npz chunks and aggregated NetCDF
- Usage: `python fit_gev_parameters.py`
- **Note:** Run after `validate_annual_max_files.py`

### `calculate_return_periods.py` (New)
Calculates return period wind speeds and confidence intervals; exports to NetCDF and CSV.
- Input: GEV parameters from Phase 2
- Output: `raw_data/return_periods/gev_return_periods.nc`, `raw_data/return_periods/gev_return_periods.csv`
- Usage: `python calculate_return_periods.py`
- **Note:** Run after `fit_gev_parameters.py`

### `run_all_phases.py` (Optional)
Orchestrator script to run all phases in sequence (Phases 1–4).
- Usage: `python run_all_phases.py`

---

## Data Specifications

| Attribute | Value |
|-----------|-------|
| Spatial grid | 1,015 (south_north) × 1,367 (west_east) = 1,386,055 grid points |
| Temporal coverage | 40 years (user provides files for desired span) |
| Variable | SPDUV10MAX (Daily maximum wind speed at 10 meters, m/s) |
| Return periods | 10, 25, 50, 100, 200, 500 years |
| Confidence level | 95% |
| Data units | m/s (consistent with wrfxtrm metadata) |

---

## Verification & Quality Assurance

### Phase 1 Checks
- [ ] Print summary: file count, grid dimensions, missing data percentage
- [ ] Verify 40 files loaded successfully
- [ ] Inspect data ranges (wind speeds should be positive, typically < 50 m/s)

### Phase 2 Checks
- [ ] Spot-check 5–10 grid points with manual `scipy.stats` calculation
- [ ] Target fit success rate: >95% of grid points
- [ ] Verify intermediate .npz files exist and have correct shape
- [ ] Check for convergence warnings in log output

### Phase 3 Checks
- [ ] Verify return levels increase monotonically (RP_10 < RP_25 < … < RP_500)
- [ ] Check confidence intervals widen appropriately for longer return periods
- [ ] Spot-check 3–5 grid points against manual inverse CDF calculation

### Phase 4 Checks
- [ ] NetCDF dimensions match expected (1,015 × 1,367)
- [ ] CSV row count = 1,366,055 + 1 header row
- [ ] No unexpected NaN values in estimate columns (except for failed fits)
- [ ] fit_status column populated correctly (success/failed/flagged)

---

## Troubleshooting

### MLE Convergence Issues
- **Symptom:** Fit fails to converge at some grid points
- **Cause:** Extreme outliers or degenerative wind speed patterns
- **Solution:** Check data for physically impossible values; review flagged grid points in fit_status

### Memory Usage (Large Dataset)
- **Symptom:** Script runs out of RAM during multiprocessing
- **Cause:** Too many processes trying to load full grid simultaneously
- **Solution:** Reduce `num_processes` in script (see `fit_gev_parameters.py`), or process latitude slices sequentially

### Confidence Intervals Very Wide
- **Symptom:** CIs for 200+ year return periods are unrealistically broad
- **Cause:** Statistical reality of 40-year sample size extrapolating far into the tail
- **Solution:** This is expected; document the limitation and use lower return periods (e.g., ≤100 years) if higher precision needed

---

## Future Enhancements

- [ ] Add interactive mapping visualization (Folium or Plotly)
- [ ] Implement alternative distributions (Gumbel, Weibull, GEV + POT hybrid)
- [ ] Generate diagnostic plots (QQ-plots, return level plots per grid cell)
- [ ] Add support for other variables (T2MAX, precipitation, etc.)
- [ ] Database backend for querying return periods by lat/lon

---

## References

- **GEV Theory:** Coles, S. (2001). An Introduction to Statistical Modeling of Extreme Values.
- **scipy.stats.genextreme:** https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.genextreme.html
- **pyextremes:** https://georgebv.github.io/pyextremes/
- **Block Maxima:** https://en.wikipedia.org/wiki/Extreme_value_theory#Block_maxima
