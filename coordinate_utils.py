"""Utilities for preserving the CONUS404 curvilinear coordinate grid."""

import h5py
import numpy as np


COORDINATE_TOLERANCE = 1e-5


def normalize_coordinate_array(values, name, expected_shape=None):
    """Return a validated 2D float32 latitude or longitude array."""
    coordinate = np.ma.filled(values, np.nan)
    coordinate = np.asarray(coordinate)

    while coordinate.ndim > 2 and coordinate.shape[0] == 1:
        coordinate = coordinate[0]

    if coordinate.ndim != 2:
        raise ValueError(
            f"{name} must be 2D or have leading singleton dimensions; "
            f"got shape {coordinate.shape}"
        )
    if expected_shape is not None and coordinate.shape != tuple(expected_shape):
        raise ValueError(
            f"{name} shape {coordinate.shape} does not match grid shape "
            f"{tuple(expected_shape)}"
        )
    if not np.isfinite(coordinate).all():
        raise ValueError(f"{name} contains non-finite values")

    minimum, maximum = (-90.0, 90.0) if name == "latitude" else (-180.0, 180.0)
    if np.any((coordinate < minimum) | (coordinate > maximum)):
        raise ValueError(f"{name} values must be between {minimum} and {maximum}")

    return coordinate.astype(np.float32, copy=False)


def read_netcdf_coordinates(dataset, expected_shape=None):
    """Read the preferred 2D coordinate pair from an open NetCDF dataset."""
    variable_pairs = (
        ("lat_2d", "lon_2d", "lat_2d/lon_2d"),
        ("XLAT", "XLONG", "XLAT/XLONG"),
        ("lat", "lon", "lat/lon"),
    )

    for lat_name, lon_name, source in variable_pairs:
        if lat_name not in dataset.variables and lon_name not in dataset.variables:
            continue
        if lat_name not in dataset.variables or lon_name not in dataset.variables:
            raise ValueError(f"Coordinate variables must include both {lat_name} and {lon_name}")

        latitude = normalize_coordinate_array(
            dataset.variables[lat_name][:], "latitude", expected_shape
        )
        longitude = normalize_coordinate_array(
            dataset.variables[lon_name][:], "longitude", expected_shape
        )
        return latitude, longitude, source

    raise ValueError(
        "No usable 2D coordinate pair found; expected lat_2d/lon_2d, "
        "lat/lon, or XLAT/XLONG"
    )


def validate_matching_coordinates(
    reference_latitude,
    reference_longitude,
    latitude,
    longitude,
    tolerance=COORDINATE_TOLERANCE,
):
    """Raise when two coordinate grids differ in shape or values."""
    if reference_latitude.shape != latitude.shape or reference_longitude.shape != longitude.shape:
        raise ValueError("Coordinate grid shapes do not match the reference grid")

    latitude_difference = float(np.max(np.abs(reference_latitude - latitude)))
    longitude_difference = float(np.max(np.abs(reference_longitude - longitude)))
    if latitude_difference > tolerance or longitude_difference > tolerance:
        raise ValueError(
            "Coordinate grid differs from the reference grid: "
            f"max latitude difference={latitude_difference:.8f}, "
            f"max longitude difference={longitude_difference:.8f}"
        )


def read_hdf5_coordinates(hdf5_file, expected_shape=None):
    """Read and validate coordinates from an open HDF5 file."""
    if "lat_2d" not in hdf5_file or "lon_2d" not in hdf5_file:
        raise ValueError("HDF5 file is missing lat_2d and lon_2d datasets")

    latitude = normalize_coordinate_array(
        hdf5_file["lat_2d"][:], "latitude", expected_shape
    )
    longitude = normalize_coordinate_array(
        hdf5_file["lon_2d"][:], "longitude", expected_shape
    )
    return latitude, longitude


def write_hdf5_coordinates(hdf5_file, latitude, longitude, source):
    """Write a self-describing 2D coordinate pair to an open HDF5 file."""
    for name, values, standard_name, units in (
        ("lat_2d", latitude, "latitude", "degrees_north"),
        ("lon_2d", longitude, "longitude", "degrees_east"),
    ):
        if name in hdf5_file:
            del hdf5_file[name]
        coordinate = hdf5_file.create_dataset(
            name, data=values, compression="gzip", compression_opts=4
        )
        coordinate.attrs["standard_name"] = standard_name
        coordinate.attrs["long_name"] = f"CONUS404 2D {standard_name}"
        coordinate.attrs["units"] = units

    hdf5_file.attrs["coordinate_source"] = str(source)
    hdf5_file.attrs["coordinate_grid"] = "curvilinear"