# SPDX-License-Identifier: LGPL-2.1-or-later
# ***************************************************************************
# *   Arxio AI - test suite                                                 *
# *   Copyright (c) 2026 Arxio AI                                           *
# ***************************************************************************

"""Unit tests for the Arxio AI workbench.

These tests run inside a FreeCAD Python console and validate the
non-Gui helpers. GUI tests are not executed in headless CI runs.
"""

from __future__ import annotations

import math
import unittest

import FreeCAD


class TestArxioUtils(unittest.TestCase):
    def test_brand_constants(self):
        import ArxioUtils as U
        self.assertEqual(U.BRAND_NAME, "Arxio AI")
        self.assertTrue(U.BRAND_VERSION)

    def test_quantity_returns_freecad_quantity(self):
        import ArxioUtils as U
        q = U.quantity(3000, "mm")
        self.assertAlmostEqual(float(q.getValueAs("mm")), 3000.0)

    def test_material_cost_m3(self):
        import ArxioUtils as U
        cost = U.material_cost("Concrete block", 2.0)
        self.assertAlmostEqual(cost, 370.0, places=2)

    def test_material_cost_m2(self):
        import ArxioUtils as U
        cost = U.material_cost("Tile roofing", 100.0)
        self.assertAlmostEqual(cost, 8500.0, places=2)

    def test_material_cost_unknown(self):
        import ArxioUtils as U
        self.assertEqual(U.material_cost("Unobtainium", 10), 0.0)

    def test_ensure_document_creates_when_missing(self):
        import ArxioUtils as U
        FreeCAD.closeDocument(
            FreeCAD.ActiveDocument.Name
        ) if FreeCAD.ActiveDocument else None
        doc = U.ensure_document()
        self.assertIsNotNone(doc)
        FreeCAD.closeDocument(doc.Name)


class TestSunVector(unittest.TestCase):
    def test_noon_north_hemisphere_points_south_and_up(self):
        from ArxioCommands import _solar_vector
        v = _solar_vector(48.86, 2.35, 6, 21, 12.0)
        # At Paris summer noon the sun is high and roughly south-ish.
        self.assertGreater(v.z, 0.5, "Sun should be above the horizon at noon")
        self.assertLess(v.y, 0.3,
                        "Sun should be south of the building at solar noon")

    def test_midnight_sun_below_horizon(self):
        from ArxioCommands import _solar_vector
        v = _solar_vector(48.86, 2.35, 12, 21, 0.5)
        self.assertLess(v.z, 0.0, "Sun should be below horizon near midnight")


if __name__ == "__main__":
    unittest.main()
