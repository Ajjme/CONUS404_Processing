# CONUS404_Processing

Processes CONUS404 WRF extreme (wrfxtrm) data by extracting annual maximum wind speeds from raw tar archives, fitting Generalized Extreme Value (GEV) distributions, and computing return period wind speeds across the CONUS domain.

**Data Source:** [USGS ScienceBase](https://www.sciencebase.gov/catalog/item/6372cd09d34ed907bf6c6ab1)  
**Globus Access Portal:** [File Manager](https://app.globus.org/file-manager?origin_id=12aeed7a-9693-4f99-9816-96911c1322d2&origin_path=%2F&two_pane=true)

---

## Overview

This project processes CONUS404 WRF extreme (wrfxtrm) data to:
1. Extract annual maximum daily wind speeds (SPDUV10MAX) from raw tar archives for each water year
2. Visualize annual maximum wind speed maps and compile them into an animated GIF
3. Validate and consolidate all annual maximum NetCDF files into a single analyzed dataset
4. Fit Generalized Extreme Value (GEV) distributions using the Block Maxima method (MLE)
5. Calculate return period wind speeds (10, 25, 50, 100, 200, 500 years) with 95% confidence intervals
6. Export results as both NetCDF (spatial) and CSV (tabular) formats
7. Generate diagnostic visualizations and validation plots

---

## Project Workflow

Scripts are numbered in execution order. Run them sequentially, or use `run_all_phases.py` for the core analysis pipeline (phases 2–4).

### Phase 0: Data Extraction
**Script:** `00_extract_max_wind_speed_yearly.py`

Extracts annual maximum SPDUV10MAX values from raw wrfxtrm tar archives for each water year.

- Opens each monthly wrfxtrm tar archive
- Finds all `wrfxtrm_d01_*` NetCDF files within
- Computes the per-grid-cell annual maximum of `SPDUV10MAX` across all days in the water year
- Computes lat/lon coordinates from the Lambert Conformal Conic (LCC) projection parameters
- Writes one output NetCDF per water year

**Input:** Raw tar archives (e.g., `wrfxtrm_conusii_YYYYMM.tar`)  
**Output:** `year_raw_data/water_year_YYYY/wrfxtrm_d01_max_spduv10max_YYYY.nc`

---

### Phase 1: Visualization & Animated GIF
**Scripts:** `10_image_creation.py`, `11_gif_creator.py`, `12_image_creation.py`

Generates spatial maps of annual maximum wind speed and compiles them into an animated GIF.

- **`10_image_creation.py`** — Full CONUS maps: renders one PNG per water year using the raw 4 km grid with a smooth CADENCE design system color ramp; loads US state boundaries from Natural Earth for basemap overlay.
- **`12_image_creation.py`** — Regional cropped maps: same as above but bounded to a user-defined lat/lon bounding box for zoomed-in regional focus.
- **`11_gif_creator.py`** — Compiles all per-year PNGs (sorted chronologically by year) into a single animated GIF (`conus_max_wind_speed_1980_2024.gif`, 500 ms/frame).

**Input:** `year_raw_data/water_year_*/wrfxtrm_d01_max_spduv10max_*.nc`  
**Output:** `output/max_wind_speed_conus_YYYY.png`, `output/conus_max_wind_speed_1980_2024.gif`

---

### Phase 2: Data Validation & Loading
**Script:** `20_validate_annual_max_files.py`

Consolidates all annual maximum NetCDF files into a single validated array for downstream statistical analysis.

- Scans `year_raw_data/water_year_*/` for all files matching `wrfxtrm_d01_max_spduv10max_YYYY.nc`
- Validates each file: checks `lat`/`lon` dimension presence, grid consistency, and SPDUV10MAX variable
- Loads all years into a single array of shape `(N_years, lat, lon)`
- Saves validated data as an intermediate HDF5 file

**Input:** `year_raw_data/water_year_*/wrfxtrm_d01_max_spduv10max_*.nc`  
**Output:** `output/validated_annual_max_data.h5`

---

### Phase 3: GEV Parameter Estimation
**Scripts:** `30_fit_gev_parameters.py`, `31_gev_validation.py`

Fits GEV distributions at every grid point using Maximum Likelihood Estimation with multiprocessing.

- **`30_fit_gev_parameters.py`** — For each of the ~1.4 M grid points:
  - Extracts the N-year time series
  - Fits `scipy.stats.genextreme` via MLE
  - Stores location (μ), scale (σ), shape (ξ), convergence flag, and any warnings
  - Parallelizes across all available CPU cores; saves intermediate `.npz` slices to prevent data loss
  - Aggregates all slices into a consolidated HDF5 file
- **`31_gev_validation.py`** — Diagnostic plots for the fitted parameters:
  - Spatial heatmaps of μ, σ, ξ
  - Convergence status map (failed vs. converged cells)
  - Parameter histograms and QQ-plots for sampled grid points

**Input:** `output/validated_annual_max_data.h5`  
**Output:** `output/gev_parameters.h5`; diagnostic PNGs (`diagnostic_heatmaps.png`, `diagnostic_convergence.png`, etc.)

---

### Phase 4: Return Period Calculation & Export
**Script:** `40_calculate_return_periods.py`

Computes wind speed return levels and 95% confidence intervals for all grid points and exports results.

- Loads GEV parameters from Phase 3
- For each return period R in [10, 25, 50, 100, 200, 500]:
  - Calculates return level via GEV inverse CDF: `x = μ + (σ/ξ) × [1 − (−log(1 − 1/R))^ξ]`
  - Computes 95% confidence intervals using the delta method
  - Verifies monotonic increase across return periods
- Exports results in two formats:
  - **NetCDF** (`gev_return_periods.nc`): spatial grids per return period with estimate, lower CI, and upper CI variables
  - **CSV** (`gev_return_periods.csv`): one row per grid point with all return period estimates and a `fit_status` column

**Input:** `output/gev_parameters.h5`  
**Output:** `output/return_periods/gev_return_periods.nc`, `output/return_periods/gev_return_periods.csv`

---

### Phase 5: Visualization & Validation
**Script:** `50_validation_return_periods.py`

Reads the Phase 4 NetCDF output and generates quality-assurance visualizations.

- **Spatial maps** (`spatial_map_XXXyr.png`): geographic distribution of return level estimates per return period
- **Uncertainty maps** (`uncertainty_map_XXXyr.png`): confidence interval widths per return period
- **Return level curves** (`return_level_curves.png`): multi-period curves with 95% CI bands for sampled grid points

Key validation checks documented in-script:
- Geographic coherence (meteorological/topographic patterns visible)
- Physical realism (100-yr levels typically 25–60+ m/s)
- Monotonic increase across return periods
- CI bands widen with longer return periods ("horn shape")

**Input:** `output/return_periods/gev_return_periods.nc`  
**Output:** PNG visualizations in `output/return_periods/visualizations/`

---

## File Structure

```
CONUS404_Processing/
├── 00_extract_max_wind_speed_yearly.py   # Phase 0: Extract annual max from tar archives
├── 10_image_creation.py                  # Phase 1: Full CONUS annual max maps
├── 11_gif_creator.py                     # Phase 1: Compile PNGs into animated GIF
├── 12_image_creation.py                  # Phase 1: Regional cropped maps
├── 20_validate_annual_max_files.py       # Phase 2: Validate & consolidate annual max data
├── 30_fit_gev_parameters.py              # Phase 3: Fit GEV at all grid points (multiprocessing)
├── 31_gev_validation.py                  # Phase 3: Diagnostic plots for GEV parameters
├── 40_calculate_return_periods.py        # Phase 4: Compute return levels & export
├── 50_validation_return_periods.py       # Phase 5: Visualize & validate return period outputs
├── run_all_phases.py                     # Orchestrator for phases 2–4
├── plotly_standard_graphic_engine.py     # Shared CADENCE Plotly theme template
├── CADENCE_Design_System.md             # Design system color & typography reference
├── SETUP_GUIDE.md                        # Quick-start setup guide
│
├── year_raw_data/                        # Per-water-year extracted NetCDF files
│   ├── water_year_1980/
│   │   └── wrfxtrm_d01_max_spduv10max_1980.nc
│   ├── water_year_1981/
│   │   └── wrfxtrm_d01_max_spduv10max_1981.nc
│   └── ...  (through water_year_2024)
│
├── output/                               # All generated outputs
│   ├── validated_annual_max_data.h5      # Phase 2 output
│   ├── gev_parameters.h5                 # Phase 3 output
│   ├── max_wind_speed_conus_YYYY.png     # Phase 1 per-year maps
│   ├── conus_max_wind_speed_1980_2024.gif # Phase 1 animated GIF
│   └── return_periods/
│       ├── gev_return_periods.nc         # Phase 4 NetCDF output
│       ├── gev_return_periods.csv        # Phase 4 CSV output
│       └── visualizations/              # Phase 5 PNG outputs
│
├── geo/                                  # Geospatial boundary files
│   ├── DCo_Boundary.geojson
│   └── North_Carolina_State_and_County_Boundary_Polygons.geojson
│
├── checks/                               # Utility inspection scripts
│   ├── checks.py
│   └── inspect_wrfxtrm.py
│
└── Archive/                              # Earlier prototype scripts
    └── ...
```

---

## Key Technical Details

### Fitting Method
- **Block Maxima:** Each "block" is one water year; the annual maximum SPDUV10MAX at each grid point is the block maximum
- **Distribution:** Generalized Extreme Value (GEV) — more flexible than Gumbel or Weibull alone
  - Parameters: location (μ), scale (σ), shape (ξ)
  - ξ < 0 → Weibull (bounded upper tail); ξ ≈ 0 → Gumbel; ξ > 0 → Fréchet (heavy tail)
- **Estimation:** Maximum Likelihood Estimation (MLE) via `scipy.stats.genextreme`

### Return Period Definition
- **Return Period R (years):** Expected recurrence interval for exceedance of a given wind speed
- **Return Level:** Wind speed x such that P(X > x) = 1/R
- **Inverse CDF formula** (GEV, ξ ≠ 0):

$$x = \mu + \frac{\sigma}{\xi} \left[1 - \left(-\ln\left(1 - \frac{1}{R}\right)\right)^\xi\right]$$

### Confidence Intervals
- **Method:** Delta method (95%)
- **Behavior:** Intervals widen significantly for longer return periods — this is statistically correct for a ~40-year record extrapolated to 200–500 year events

### Projection
- **Source CRS:** Lambert Conformal Conic (LCC) — TRUELAT1=30°, TRUELAT2=50°, CLAT=39.1°, CLON=−97.9°, dx=dy=4 km
- **Output CRS:** WGS84 (lat/lon)
- **Grid size:** 1,015 (south_north) × 1,367 (west_east) = 1,386,055 grid points

### Design System
All visualizations use the **CADENCE design system** color palette:
- Teal `#2F8F7F`, Blue `#205196`, Tan `#D9A341`, Red `#AA2634`, Light Blue `#6FA8DC`
- Shared Plotly template available via `plotly_standard_graphic_engine.py`

---

## Data Specifications

| Attribute | Value |
|-----------|-------|
| Spatial grid | 1,015 × 1,367 = 1,386,055 grid points |
| Spatial resolution | 4 km |
| Temporal coverage | Water years 1980–2024 (up to 45 years) |
| Variable | SPDUV10MAX — daily maximum 10-m wind speed (m/s) |
| Return periods | 10, 25, 50, 100, 200, 500 years |
| Confidence level | 95% |
| Data units | m/s |

---

## Quick Start

```bash
# 1. Set up the virtual environment
python -m venv .venv
source .venv/bin/activate          # macOS/Linux
# .venv\Scripts\activate           # Windows

# 2. Install dependencies
pip install netCDF4 numpy scipy h5py xarray matplotlib geopandas pyproj imageio pandas plotly

# 3. Run the full analysis pipeline (phases 2–4)
python run_all_phases.py

# Or run phases individually:
python 20_validate_annual_max_files.py   # Phase 2
python 30_fit_gev_parameters.py          # Phase 3
python 40_calculate_return_periods.py    # Phase 4
python 50_validation_return_periods.py   # Phase 5 (validation)
```

> **Note:** `run_all_phases.py` currently contains a hardcoded Windows path. Update the `script_path` base directory in that file to your local workspace path before running.

---

## Troubleshooting

### MLE Convergence Issues
- **Symptom:** Fit fails to converge at some grid points
- **Cause:** Extreme outliers or degenerate wind speed patterns (e.g., constant values)
- **Solution:** Check `fit_status` column in CSV output; review `diagnostic_convergence.png` from `31_gev_validation.py`

### Memory Usage (Large Dataset)
- **Symptom:** Script runs out of RAM during multiprocessing
- **Cause:** Too many worker processes sharing the full grid in memory
- **Solution:** Reduce `num_processes` in `30_fit_gev_parameters.py`, or process latitude slices sequentially

### Confidence Intervals Very Wide
- **Symptom:** CIs for 200+ year return periods are unrealistically broad
- **Cause:** Expected statistical behavior when extrapolating a 40-year record to rare events
- **Solution:** This is mathematically correct; prefer ≤100-year return periods for higher-confidence results

### GIF Not Generating
- **Symptom:** `11_gif_creator.py` reports no PNG files found
- **Cause:** `10_image_creation.py` has not been run yet, or output PNGs are in the wrong directory
- **Solution:** Run `10_image_creation.py` first; verify PNGs exist in `output/`

---

## References

- **GEV Theory:** Coles, S. (2001). *An Introduction to Statistical Modeling of Extreme Values.* Springer.
- **scipy.stats.genextreme:** https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.genextreme.html
- **Block Maxima Method:** https://en.wikipedia.org/wiki/Extreme_value_theory#Block_maxima
- **CONUS404 Dataset:** https://www.sciencebase.gov/catalog/item/6372cd09d34ed907bf6c6ab1
