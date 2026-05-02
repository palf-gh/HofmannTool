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
    arc_to_bezier_segments,
    candidate_radius,
    create_tangent_candidates,
    grid_origin,
    is_closed_contour,
    node_point,
)


class HofmannGeometryTests(unittest.TestCase):

    def assertPointAlmostEqual(self, actual, expected):
        self.assertAlmostEqual(actual.x, expected.x)
        self.assertAlmostEqual(actual.y, expected.y)

    def tangentUnit(self, center, point, flow):
        radial = point.sub(center)
        radius = radial.length()
        self.assertGreater(radius, 0)
        ux = radial.x / radius
        uy = radial.y / radius
        if flow == FLOW_CCW:
            return Point(-uy, ux)
        return Point(uy, -ux)

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

    def test_vertical_ccw_candidate_exits_on_right_side_of_segment(self):
        # Travelling A=(0,0) -> B=(0,100) along +Y, true CCW rotation around A
        # must exit on the +X side (angle 0 deg), not the -X side. Same for B.
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
        self.assertAlmostEqual(candidate.point_a.x, 20)
        self.assertAlmostEqual(candidate.point_b.x, 20)
        self.assertAlmostEqual(candidate.point_a.y, 0)
        self.assertAlmostEqual(candidate.point_b.y, 100)
        # angle_a/angle_b are 0 deg (right side) for both endpoints.
        self.assertAlmostEqual(candidate.angle_a, 0.0)
        self.assertAlmostEqual(candidate.angle_b, 0.0)

    def test_vertical_cw_candidate_exits_on_left_side_of_segment(self):
        candidates = create_tangent_candidates(
            GridNode(0, 0),
            GridNode(1, 0),
            Point(0, 0),
            Point(0, 100),
            40,
            required_flow_a=FLOW_CW,
            required_flow_b=FLOW_CW,
        )
        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertAlmostEqual(candidate.point_a.x, -20)
        self.assertAlmostEqual(candidate.point_b.x, -20)

    def test_diagonal_candidates_have_finite_angles(self):
        candidates = create_tangent_candidates(GridNode(0, 0), GridNode(1, 1), Point(0, 0), Point(100, 100), 60)
        self.assertEqual(len(candidates), 4)
        for candidate in candidates:
            self.assertTrue(math.isfinite(candidate.angle_a))
            self.assertTrue(math.isfinite(candidate.angle_b))

    def test_candidate_flow_matches_line_direction(self):
        candidates = create_tangent_candidates(GridNode(0, 0), GridNode(2, 3), Point(0, 0), Point(300, 200), 70)
        self.assertEqual(len(candidates), 4)
        for candidate in candidates:
            line = candidate.point_b.sub(candidate.point_a)
            line_unit = Point(line.x / line.length(), line.y / line.length())
            tangent_a = self.tangentUnit(candidate.center_a, candidate.point_a, candidate.flow_a)
            tangent_b = self.tangentUnit(candidate.center_b, candidate.point_b, candidate.flow_b)
            dot_a = line_unit.x * tangent_a.x + line_unit.y * tangent_a.y
            dot_b = line_unit.x * tangent_b.x + line_unit.y * tangent_b.y
            self.assertAlmostEqual(dot_a, 1.0)
            self.assertAlmostEqual(dot_b, 1.0)

    def test_candidate_radius_matches_input_diameter(self):
        candidate = create_tangent_candidates(
            GridNode(0, 0), GridNode(0, 1), Point(0, 0), Point(100, 0), 60,
            FLOW_CW, FLOW_CW,
        )[0]
        self.assertAlmostEqual(candidate_radius(candidate), 30.0)

    def test_arc_to_bezier_quarter_circle_uses_single_segment_with_correct_handles(self):
        segs = arc_to_bezier_segments(Point(0, 0), 100, 0, 90, FLOW_CCW)
        self.assertEqual(len(segs), 1)
        p0, p1, p2, p3 = segs[0]
        self.assertAlmostEqual(p0.x, 100)
        self.assertAlmostEqual(p0.y, 0)
        self.assertAlmostEqual(p3.x, 0)
        self.assertAlmostEqual(p3.y, 100)
        expected_k = 100.0 * (4.0 / 3.0) * math.tan(math.pi / 8.0)
        self.assertAlmostEqual(p1.x, 100)
        self.assertAlmostEqual(p1.y, expected_k)
        self.assertAlmostEqual(p2.x, expected_k)
        self.assertAlmostEqual(p2.y, 100)

    def test_arc_to_bezier_full_circle_splits_into_four_quarters(self):
        segs = arc_to_bezier_segments(Point(0, 0), 50, 0, 360, FLOW_CCW)
        self.assertEqual(len(segs), 4)
        # First segment endpoint at (50, 0); last segment endpoint back near (50, 0).
        self.assertAlmostEqual(segs[0][0].x, 50)
        self.assertAlmostEqual(segs[-1][3].x, 50)
        self.assertAlmostEqual(segs[-1][3].y, 0)

    def test_arc_to_bezier_splits_counterclockwise_arcs_at_extrema(self):
        segs = arc_to_bezier_segments(Point(0, 0), 100, 30, 210, FLOW_CCW)
        self.assertEqual(len(segs), 3)
        extrema_endpoints = [segs[0][3], segs[1][3]]
        self.assertAlmostEqual(extrema_endpoints[0].x, 0)
        self.assertAlmostEqual(extrema_endpoints[0].y, 100)
        self.assertAlmostEqual(extrema_endpoints[1].x, -100)
        self.assertAlmostEqual(extrema_endpoints[1].y, 0)

    def test_arc_to_bezier_splits_clockwise_arcs_at_extrema(self):
        segs = arc_to_bezier_segments(Point(0, 0), 100, 45, 225, FLOW_CW)
        self.assertEqual(len(segs), 3)
        extrema_endpoints = [segs[0][3], segs[1][3]]
        self.assertAlmostEqual(extrema_endpoints[0].x, 100)
        self.assertAlmostEqual(extrema_endpoints[0].y, 0)
        self.assertAlmostEqual(extrema_endpoints[1].x, 0)
        self.assertAlmostEqual(extrema_endpoints[1].y, -100)

    def test_arc_to_bezier_clockwise_handles_point_in_negative_tangent_direction(self):
        ccw = arc_to_bezier_segments(Point(0, 0), 100, 0, 90, FLOW_CCW)[0]
        cw_segments = arc_to_bezier_segments(Point(0, 0), 100, 0, 90, FLOW_CW)
        cw = cw_segments[0]
        # CW from 0 deg to 90 deg sweeps -270 deg via a three-segment split, but the first
        # segment for the original test still starts at (100, 0). The handle
        # direction differs between CW and CCW first quarters.
        self.assertEqual(len(cw_segments), 3)
        ccw_handle_dy = ccw[1].y - ccw[0].y
        cw_handle_dy = cw[1].y - cw[0].y
        self.assertGreater(ccw_handle_dy, 0)
        self.assertLess(cw_handle_dy, 0)

    def test_arc_to_bezier_segment_endpoints_stay_on_circle(self):
        segs = arc_to_bezier_segments(Point(10, -20), 75, -30, 200, FLOW_CCW)
        self.assertGreater(len(segs), 1)
        for p0, _p1, _p2, p3 in segs:
            self.assertAlmostEqual(math.hypot(p0.x - 10, p0.y + 20), 75)
            self.assertAlmostEqual(math.hypot(p3.x - 10, p3.y + 20), 75)

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
