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
    return 1.0 if flow == FLOW_CCW else -1.0


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
