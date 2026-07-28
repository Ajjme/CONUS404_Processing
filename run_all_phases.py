"""
Orchestrator script to run all phases of the GEV return period analysis.

Runs in sequence:
1. Phase 1: Validate annual max files
2. Phase 2: Fit GEV parameters
3. Phases 3 & 4: Calculate return periods and export
"""

import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime

def run_phase(phase_num, script_name, description):
    """Run a phase script and handle errors."""
    print("\n" + "=" * 80)
    print(f"PHASE {phase_num}: {description}")
    print("=" * 80)
    print(f"Running: {script_name}\n")
    
    script_path = Path(__file__).resolve().parent / script_name
    
    if not os.path.exists(script_path):
        print(f"✗ ERROR: Script not found: {script_path}")
        return False
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=script_path.parent,
            timeout=3600  # 1 hour timeout
        )
        
        if result.returncode == 0:
            print(f"\n✓ Phase {phase_num} completed successfully")
            return True
        else:
            print(f"\n✗ Phase {phase_num} failed with return code {result.returncode}")
            return False
    
    except subprocess.TimeoutExpired:
        print(f"\n✗ Phase {phase_num} timed out (exceeded 1 hour)")
        return False
    except Exception as e:
        print(f"\n✗ Error running Phase {phase_num}: {str(e)}")
        return False

def main():
    start_time = datetime.now()
    
    print("=" * 80)
    print("GEV RETURN PERIOD ANALYSIS - FULL WORKFLOW")
    print("=" * 80)
    print(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    phases = [
        (1, '20_validate_annual_max_files.py', 'Validate Annual Max Files'),
        (2, '30_fit_gev_parameters.py', 'Fit GEV Parameters (Multiprocessing)'),
        (3, '40_calculate_return_periods.py', 'Calculate Return Periods & Export'),
    ]
    
    results = {}
    
    for phase_num, script_name, description in phases:
        success = run_phase(phase_num, script_name, description)
        results[phase_num] = success
        
        if not success:
            print(f"\n✗ Workflow stopped at Phase {phase_num}")
            print("Please review the error above and try again")
            return
    
    # All phases complete
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds() / 60
    
    print("\n" + "=" * 80)
    print("WORKFLOW COMPLETE")
    print("=" * 80)
    print(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"End time:   {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Duration:   {duration:.1f} minutes")
    print("\nAll phases completed successfully!")
    print("\nOutput files created:")
    print("  - output/return_periods/gev_return_periods.nc (NetCDF)")
    print("  - output/return_periods/gev_return_periods.csv (CSV)")
    
    print("\nNext steps:")
    print("  1. Review the output files")
    print("  2. Load the NetCDF in GIS software (QGIS, ArcGIS) for visualization")
    print("  3. Analyze the CSV in Excel, R, or Python for statistical insights")
    print("  4. Query specific lat/lon points for return period data")

if __name__ == '__main__':
    main()
