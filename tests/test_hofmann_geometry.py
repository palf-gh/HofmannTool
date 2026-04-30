import math
import os
import sys
import unittest


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESOURCES = os.path.join(ROOT, "HofmannTool.glyphsTool", "Contents", "Resources")
sys.path.insert(0, RESOURCES)

from hofmann_geometry import (  # noqa: E402
    FLOW_CCW,
    FLOW_CW,
    GridNode,
    Point,
    create_tangent_candidates,
    grid_origin,
    is_closed_contour,
    node_point,
)


class HofmannGeometryTests(unittest.TestCase):

    def assertPointAlmostEqual(self, actual, expected):
        self.assertAlmostEqual(actual.x, expected.x)
        self.assertAlmostEqual(actual.y, expected.y)

    def test_grid_origin_centers_grid_in_body_box(self):
        origin = grid_origin(width=600, ascender=800, descender=-200, rows=4, cols=3, spacing=100)
        self.assertPointAlmostEqual(origin, Point(200, 150))
        self.assertPointAlmostEqual(node_point(origin, GridNode(3, 2), 100), Point(400, 450))

    def test_horizontal_candidates_include_four_flows_when_diameter_is_valid(self):
        node_a = GridNode(0, 0)
        node_b = GridNode(0, 1)
        candidates = create_tangent_candidates(node_a, node_b, Point(0, 0), Point(100, 0), 80)
        self.assertEqual(len(candidates), 4)
        self.assertEqual({(c.flow_a, c.flow_b) for c in candidates}, {
            (FLOW_CW, FLOW_CW),
            (FLOW_CW, FLOW_CCW),
            (FLOW_CCW, FLOW_CW),
            (FLOW_CCW, FLOW_CCW),
        })

    def test_inner_candidates_are_hidden_when_diameter_reaches_distance(self):
        candidates = create_tangent_candidates(GridNode(0, 0), GridNode(0, 1), Point(0, 0), Point(100, 0), 100)
        self.assertEqual(len(candidates), 2)
        self.assertTrue(all(c.flow_a == c.flow_b for c in candidates))

    def test_vertical_same_flow_candidate_offsets_perpendicular_to_segment(self):
        candidates = create_tangent_candidates(
            GridNode(0, 0),
            GridNode(1, 0),
            Point(0, 0),
            Point(0, 100),
            40,
            required_flow_a=FLOW_CCW,
            required_flow_b=FLOW_CCW,
        )
        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertAlmostEqual(candidate.point_a.x, -20)
        self.assertAlmostEqual(candidate.point_b.x, -20)
        self.assertAlmostEqual(candidate.point_a.y, 0)
        self.assertAlmostEqual(candidate.point_b.y, 100)

    def test_diagonal_candidates_have_finite_angles(self):
        candidates = create_tangent_candidates(GridNode(0, 0), GridNode(1, 1), Point(0, 0), Point(100, 100), 60)
        self.assertEqual(len(candidates), 4)
        for candidate in candidates:
            self.assertTrue(math.isfinite(candidate.angle_a))
            self.assertTrue(math.isfinite(candidate.angle_b))

    def test_closed_contour_requires_contiguous_segments_returning_to_start(self):
        a = GridNode(0, 0)
        b = GridNode(0, 1)
        c = GridNode(1, 1)
        ab = create_tangent_candidates(a, b, Point(0, 0), Point(100, 0), 40, FLOW_CW, FLOW_CW)[0]
        bc = create_tangent_candidates(b, c, Point(100, 0), Point(100, 100), 40, FLOW_CW, FLOW_CW)[0]
        ca = create_tangent_candidates(c, a, Point(100, 100), Point(0, 0), 40, FLOW_CW, FLOW_CW)[0]
        self.assertTrue(is_closed_contour([ab, bc, ca]))
        self.assertFalse(is_closed_contour([ab, ca]))


if __name__ == "__main__":
    unittest.main()
