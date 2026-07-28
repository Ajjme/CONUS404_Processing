"""Backfill authoritative coordinates into existing CONUS404 HDF5 products."""

import argparse
import shutil
from pathlib import Path

import h5py
import netCDF4 as nc

from coordinate_utils import (
    read_hdf5_coordinates,
    read_netcdf_coordinates,
    validate_matching_coordinates,
    write_hdf5_coordinates,
)


def get_hdf5_grid_shape(hdf5_file):
    """Return the declared spatial shape of a pipeline HDF5 file."""
    if "south_north" in hdf5_file.attrs and "west_east" in hdf5_file.attrs:
        return (
            int(hdf5_file.attrs["south_north"]),
            int(hdf5_file.attrs["west_east"]),
        )

    for dataset_name in ("location", "spduv10max"):
        if dataset_name in hdf5_file:
            return tuple(hdf5_file[dataset_name].shape[-2:])

    raise ValueError("Cannot determine HDF5 spatial grid shape")


def backfill_hdf5(path, latitude, longitude, source, overwrite=False, backup=True):
    """Add validated coordinates to one existing HDF5 product."""
    path = Path(path)
    with h5py.File(path, "r") as hdf5_file:
        grid_shape = get_hdf5_grid_shape(hdf5_file)
        if latitude.shape != grid_shape or longitude.shape != grid_shape:
            raise ValueError(
                f"Coordinate shape {latitude.shape} does not match {path} grid "
                f"shape {grid_shape}"
            )

        has_coordinates = "lat_2d" in hdf5_file or "lon_2d" in hdf5_file
        if has_coordinates:
            existing_latitude, existing_longitude = read_hdf5_coordinates(
                hdf5_file, grid_shape
            )
            try:
                validate_matching_coordinates(
                    existing_latitude,
                    existing_longitude,
                    latitude,
                    longitude,
                )
            except ValueError:
                if not overwrite:
                    raise
            else:
                return False

    if backup:
        backup_path = path.with_suffix(path.suffix + ".coordinate-backup")
        if not backup_path.exists():
            shutil.copy2(path, backup_path)

    with h5py.File(path, "r+") as hdf5_file:
        write_hdf5_coordinates(hdf5_file, latitude, longitude, source)

    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=Path(
            "year_raw_data/water_year_1980/"
            "wrfxtrm_d01_max_spduv10max_1980.nc"
        ),
        help="Annual NetCDF containing authoritative 2D coordinates",
    )
    parser.add_argument(
        "--targets",
        type=Path,
        nargs="+",
        default=[
            Path("output/validated_annual_max_data.h5"),
            Path("output/gev_parameters.h5"),
        ],
        help="HDF5 files to enrich",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace conflicting coordinate datasets after validation",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Do not create a .coordinate-backup file before modification",
    )
    args = parser.parse_args()

    with nc.Dataset(args.source) as source_dataset:
        latitude, longitude, variable_source = read_netcdf_coordinates(
            source_dataset
        )
    provenance = f"{args.source} ({variable_source})"

    for target in args.targets:
        changed = backfill_hdf5(
            target,
            latitude,
            longitude,
            provenance,
            overwrite=args.overwrite,
            backup=not args.no_backup,
        )
        status = "updated" if changed else "already current"
        print(f"{target}: {status}")


if __name__ == "__main__":
    main()