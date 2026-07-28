import importlib.util
from pathlib import Path
import tempfile
import unittest

import h5py
import numpy as np


MODULE_PATH = Path(__file__).resolve().parents[1] / "25_backfill_coordinates.py"
SPEC = importlib.util.spec_from_file_location("backfill_coordinates", MODULE_PATH)
BACKFILL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BACKFILL)


class BackfillCoordinateTests(unittest.TestCase):
    def setUp(self):
        self.latitude = np.array(
            [[35.0, 35.2], [36.1, 36.4]], dtype=np.float32
        )
        self.longitude = np.array(
            [[-100.0, -98.9], [-100.3, -98.5]], dtype=np.float32
        )

    def create_target(self, directory, shape=(2, 2)):
        path = Path(directory) / "target.h5"
        with h5py.File(path, "w") as target:
            target.create_dataset("location", data=np.ones(shape))
            target.attrs["south_north"] = shape[0]
            target.attrs["west_east"] = shape[1]
        return path

    def test_backfills_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = self.create_target(temp_dir)

            changed = BACKFILL.backfill_hdf5(
                target,
                self.latitude,
                self.longitude,
                "annual.nc",
                backup=False,
            )
            changed_again = BACKFILL.backfill_hdf5(
                target,
                self.latitude,
                self.longitude,
                "annual.nc",
                backup=False,
            )

            self.assertTrue(changed)
            self.assertFalse(changed_again)
            with h5py.File(target) as result:
                np.testing.assert_array_equal(result["lat_2d"][:], self.latitude)
                np.testing.assert_array_equal(result["lon_2d"][:], self.longitude)
                self.assertEqual(result.attrs["coordinate_source"], "annual.nc")

    def test_rejects_shape_mismatch(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = self.create_target(temp_dir, shape=(3, 2))

            with self.assertRaisesRegex(ValueError, "does not match"):
                BACKFILL.backfill_hdf5(
                    target,
                    self.latitude,
                    self.longitude,
                    "annual.nc",
                    backup=False,
                )

    def test_rejects_conflicting_existing_coordinates(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = self.create_target(temp_dir)
            BACKFILL.backfill_hdf5(
                target,
                self.latitude,
                self.longitude,
                "annual.nc",
                backup=False,
            )
            changed_latitude = self.latitude.copy()
            changed_latitude[0, 0] += 0.1

            with self.assertRaisesRegex(ValueError, "differs from the reference"):
                BACKFILL.backfill_hdf5(
                    target,
                    changed_latitude,
                    self.longitude,
                    "different-annual.nc",
                    backup=False,
                )


if __name__ == "__main__":
    unittest.main()