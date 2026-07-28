import unittest

import netCDF4 as nc
import numpy as np

from coordinate_utils import (
    normalize_coordinate_array,
    read_netcdf_coordinates,
    validate_matching_coordinates,
)


class CoordinateUtilsTests(unittest.TestCase):
    def test_normalizes_leading_singleton_dimension(self):
        values = np.array([[[35.0, 35.1], [36.0, 36.2]]])

        result = normalize_coordinate_array(values, "latitude", (2, 2))

        self.assertEqual(result.shape, (2, 2))
        self.assertEqual(result.dtype, np.float32)

    def test_rejects_invalid_shape_and_range(self):
        with self.assertRaisesRegex(ValueError, "grid shape"):
            normalize_coordinate_array(np.zeros((2, 3)), "longitude", (2, 2))
        with self.assertRaisesRegex(ValueError, "between"):
            normalize_coordinate_array(np.full((2, 2), 181.0), "longitude")

    def test_reads_wrf_coordinates(self):
        with nc.Dataset("memory", mode="w", diskless=True) as dataset:
            dataset.createDimension("Time", 1)
            dataset.createDimension("south_north", 2)
            dataset.createDimension("west_east", 2)
            latitude = dataset.createVariable(
                "XLAT", "f4", ("Time", "south_north", "west_east")
            )
            longitude = dataset.createVariable(
                "XLONG", "f4", ("Time", "south_north", "west_east")
            )
            latitude[:] = [[[35.0, 35.1], [36.0, 36.2]]]
            longitude[:] = [[[-100.0, -99.0], [-100.2, -98.8]]]

            lat_2d, lon_2d, source = read_netcdf_coordinates(dataset, (2, 2))

        self.assertEqual(source, "XLAT/XLONG")
        np.testing.assert_allclose(lat_2d, [[35.0, 35.1], [36.0, 36.2]])
        np.testing.assert_allclose(lon_2d, [[-100.0, -99.0], [-100.2, -98.8]])

    def test_rejects_coordinate_mismatch(self):
        reference = np.zeros((2, 2), dtype=np.float32)
        changed = reference.copy()
        changed[1, 1] = 0.01

        with self.assertRaisesRegex(ValueError, "differs from the reference"):
            validate_matching_coordinates(reference, reference, changed, reference)

    def test_rejects_incomplete_coordinate_pair(self):
        with nc.Dataset("memory", mode="w", diskless=True) as dataset:
            dataset.createDimension("south_north", 2)
            dataset.createDimension("west_east", 2)
            dataset.createVariable(
                "XLAT", "f4", ("south_north", "west_east")
            )

            with self.assertRaisesRegex(ValueError, "both XLAT and XLONG"):
                read_netcdf_coordinates(dataset, (2, 2))


if __name__ == "__main__":
    unittest.main()