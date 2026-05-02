# encoding: utf-8
from __future__ import division, print_function, unicode_literals

import math
from dataclasses import dataclass


FLOW_CW = "cw"
FLOW_CCW = "ccw"
FLOWS = (FLOW_CW, FLOW_CCW)


@dataclass(frozen=True)
class Point:
    x: float
    y: float

    def add(self, other):
        return Point(self.x + other.x, self.y + other.y)

    def sub(self, other):
        return Point(self.x - other.x, self.y - other.y)

    def mul(self, factor):
        return Point(self.x * factor, self.y * factor)

    def length(self):
        return math.hypot(self.x, self.y)


@dataclass(frozen=True)
class GridNode:
    row: int
    col: int


@dataclass(frozen=True)
class TangentCandidate:
    node_a: GridNode
    node_b: GridNode
    flow_a: str
    flow_b: str
    point_a: Point
    point_b: Point
    center_a: Point
    center_b: Point
    angle_a: float
    angle_b: float

    @property
    def is_inner(self):
        return self.flow_a != self.flow_b


def grid_origin(width, ascender, descender, rows, cols, spacing, x_offset=0.0, y_offset=0.0):
    rows = max(1, int(rows))
    cols = max(1, int(cols))
    spacing = float(spacing)
    total_width = (cols - 1) * spacing
    total_height = (rows - 1) * spacing
    body_center_y = (float(ascender) + float(descender)) * 0.5
    return Point(
        (float(width) - total_width) * 0.5 + float(x_offset),
        body_center_y - total_height * 0.5 + float(y_offset),
    )


def node_point(origin, node, spacing):
    return Point(
        float(origin.x) + int(node.col) * float(spacing),
        float(origin.y) + int(node.row) * float(spacing),
    )


def _unit_vector(vector):
    length = vector.length()
    if length <= 0.0:
        return None
    return Point(vector.x / length, vector.y / length)


def _perpendicular(unit):
    return Point(-unit.y, unit.x)


def _flow_sign(flow):
    # Outer-tangent offset is placed so that travelling along the tangent in the
    # A->B direction matches the named rotation around each circle. With unit Y-up
    # geometry, CCW rotation needs the tangent point on the right of A->B (i.e.
    # opposite of `perp` which is +90 degree rotation of `unit`), and CW on the left.
    return -1.0 if flow == FLOW_CCW else 1.0


def _angle(center, point):
    return math.degrees(math.atan2(point.y - center.y, point.x - center.x))


def create_tangent_candidate(node_a, node_b, center_a, center_b, diameter, flow_a, flow_b):
    radius = float(diameter) * 0.5
    delta = center_b.sub(center_a)
    distance = delta.length()
    if radius <= 0.0 or distance <= 0.0:
        return None
    unit = _unit_vector(delta)
    perp = _perpendicular(unit)

    if flow_a == flow_b:
        offset = perp.mul(radius * _flow_sign(flow_a))
        point_a = center_a.add(offset)
        point_b = center_b.add(offset)
    else:
        half_distance = distance * 0.5
        if half_distance <= radius:
            return None
        local_x = (half_distance * half_distance - radius * radius) / half_distance
        local_y = radius * math.sqrt(half_distance * half_distance - radius * radius) / half_distance
        midpoint = Point(
            (center_a.x + center_b.x) * 0.5,
            (center_a.y + center_b.y) * 0.5,
        )
        point_a = midpoint.add(unit.mul(-local_x)).add(perp.mul(_flow_sign(flow_a) * local_y))
        point_b = midpoint.add(unit.mul(local_x)).add(perp.mul(_flow_sign(flow_b) * local_y))

    return TangentCandidate(
        node_a=node_a,
        node_b=node_b,
        flow_a=flow_a,
        flow_b=flow_b,
        point_a=point_a,
        point_b=point_b,
        center_a=center_a,
        center_b=center_b,
        angle_a=_angle(center_a, point_a),
        angle_b=_angle(center_b, point_b),
    )


def create_tangent_candidates(node_a, node_b, center_a, center_b, diameter, required_flow_a=None, required_flow_b=None):
    candidates = []
    for flow_a in FLOWS:
        if required_flow_a is not None and flow_a != required_flow_a:
            continue
        for flow_b in FLOWS:
            if required_flow_b is not None and flow_b != required_flow_b:
                continue
            candidate = create_tangent_candidate(node_a, node_b, center_a, center_b, diameter, flow_a, flow_b)
            if candidate is not None:
                candidates.append(candidate)
    return candidates


def is_closed_contour(candidates):
    if not candidates:
        return False
    for previous, current in zip(candidates, candidates[1:]):
        if previous.node_b != current.node_a:
            return False
    return candidates[0].node_a == candidates[-1].node_b


def candidate_radius(candidate):
    return candidate.point_a.sub(candidate.center_a).length()


def _resolve_arc_end_angle(start_angle_deg, end_angle_deg, flow):
    start = float(start_angle_deg)
    end = float(end_angle_deg)
    if flow == FLOW_CCW:
        while end < start:
            end += 360.0
        while end - start > 360.0:
            end -= 360.0
    else:
        while end > start:
            end -= 360.0
        while start - end > 360.0:
            end += 360.0
    return end


def _arc_break_angles(start_angle_deg, end_angle_deg, flow, max_arc_deg=90.0):
    start = float(start_angle_deg)
    end = _resolve_arc_end_angle(start, float(end_angle_deg), flow)
    if abs(end - start) < 1e-9:
        return []

    max_arc = max(1e-6, abs(float(max_arc_deg)))
    lower = min(start, end)
    upper = max(start, end)
    first_k = int(math.floor(lower / 90.0)) - 1
    last_k = int(math.ceil(upper / 90.0)) + 1
    extrema = []
    for k in range(first_k, last_k + 1):
        angle = k * 90.0
        if flow == FLOW_CCW:
            if start + 1e-9 < angle < end - 1e-9:
                extrema.append(angle)
        else:
            if end + 1e-9 < angle < start - 1e-9:
                extrema.append(angle)
    extrema.sort(reverse=(flow == FLOW_CW))

    raw_breaks = [start] + extrema + [end]
    breaks = [start]
    for raw_start, raw_end in zip(raw_breaks, raw_breaks[1:]):
        sweep = raw_end - raw_start
        n_steps = max(1, int(math.ceil(abs(sweep) / max_arc)))
        for i in range(1, n_steps + 1):
            breaks.append(raw_start + sweep * (i / float(n_steps)))
    return breaks


def arc_to_bezier_segments(center, radius, start_angle_deg, end_angle_deg, flow, max_arc_deg=90.0):
    # Cubic Bezier approximation of a circular arc. Default splitting keeps
    # on-curve points at font-friendly extrema (0/90/180/270 degrees) and never
    # sweeps more than `max_arc_deg` per cubic segment.
    break_angles = _arc_break_angles(start_angle_deg, end_angle_deg, flow, max_arc_deg=max_arc_deg)
    if not break_angles:
        return []
    cx = float(center.x)
    cy = float(center.y)
    r = float(radius)
    segments = []
    for start_angle, end_angle in zip(break_angles, break_angles[1:]):
        a0 = math.radians(start_angle)
        a1 = math.radians(end_angle)
        delta = a1 - a0
        # k is signed; tan(delta/4) flips when sweeping CW so handles point the right way.
        k = (4.0 / 3.0) * math.tan(delta / 4.0) * r
        p0 = Point(cx + r * math.cos(a0), cy + r * math.sin(a0))
        p3 = Point(cx + r * math.cos(a1), cy + r * math.sin(a1))
        t0x = -math.sin(a0)
        t0y = math.cos(a0)
        t1x = -math.sin(a1)
        t1y = math.cos(a1)
        p1 = Point(p0.x + k * t0x, p0.y + k * t0y)
        p2 = Point(p3.x - k * t1x, p3.y - k * t1y)
        segments.append((p0, p1, p2, p3))
    return segments
