# encoding: utf-8
from __future__ import division, print_function, unicode_literals

import os
import sys
import objc

from GlyphsApp import Glyphs, GSPath, GSNode, LINE, CURVE, OFFCURVE
from GlyphsApp.plugins import SelectTool
from AppKit import (
    NSAttributedString,
    NSBezierPath,
    NSColor,
    NSFont,
    NSFontAttributeName,
    NSForegroundColorAttributeName,
    NSMakePoint,
    NSMakeRect,
)
from Foundation import NSString

RESOURCE_DIR = os.path.dirname(os.path.abspath(__file__))
if RESOURCE_DIR not in sys.path:
    sys.path.insert(0, RESOURCE_DIR)

from hofmann_geometry import GridNode, grid_origin, node_point
from hofmann_geometry import Point, create_tangent_candidates, is_closed_contour
from hofmann_geometry import (
    arc_to_bezier_segments,
    candidate_radius,
)


PREF = "com.palf.HofmannTool"


def _bool_default(key, fallback):
    value = Glyphs.defaults.get(PREF + "." + key, fallback)
    return bool(value)


def _int_default(key, fallback):
    try:
        return int(Glyphs.defaults.get(PREF + "." + key, fallback))
    except Exception:
        return int(fallback)


def _float_default(key, fallback):
    try:
        return float(Glyphs.defaults.get(PREF + "." + key, fallback))
    except Exception:
        return float(fallback)


GSInspectorView = objc.lookUpClass("GSInspectorView")


class HofmannToolInspectorView(GSInspectorView):

    def acceptsFirstResponder(self):
        return True


class HofmannTool(SelectTool):

    inspectorDialog = objc.IBOutlet()
    inspectorDialogView = objc.IBOutlet()
    rowsLabel = objc.IBOutlet()
    colsLabel = objc.IBOutlet()
    spacingLabel = objc.IBOutlet()
    diameterLabel = objc.IBOutlet()
    xOffsetLabel = objc.IBOutlet()
    yOffsetLabel = objc.IBOutlet()
    rowsTextField = objc.IBOutlet()
    colsTextField = objc.IBOutlet()
    spacingTextField = objc.IBOutlet()
    diameterTextField = objc.IBOutlet()
    xOffsetTextField = objc.IBOutlet()
    yOffsetTextField = objc.IBOutlet()
    outputModeSegmentedControl = objc.IBOutlet()
    showGridCheckBox = objc.IBOutlet()
    showNodesCheckBox = objc.IBOutlet()
    showCandidatesCheckBox = objc.IBOutlet()
    showLabelsCheckBox = objc.IBOutlet()
    applyButton = objc.IBOutlet()
    undoButton = objc.IBOutlet()
    clearButton = objc.IBOutlet()

    @objc.python_method
    def settings(self):
        self.name = Glyphs.localize({
            "en": "Hofmann Tool",
            "ja": "Hofmann Tool",
        })
        self.keyboardShortcut = "h"
        self.loadNib("InspectorView", __file__)
        self._localize_ui()
        self._apply_readable_colours()
        self._load_settings_to_ui()

    @objc.python_method
    def start(self):
        self._preview_segments = []
        self._candidate_segments = []
        self._start_node = None
        self._active_node = None
        self._closed = False

    def view(self):
        return self.inspectorDialogView

    @objc.python_method
    def activate(self):
        Glyphs.redraw()

    @objc.python_method
    def deactivate(self):
        Glyphs.redraw()

    @objc.python_method
    def _default_settings(self):
        return {
            "rows": 4,
            "cols": 4,
            "spacing": 120.0,
            "diameter": 80.0,
            "xOffset": 0.0,
            "yOffset": 0.0,
            "outputMode": "filled",
            "showGrid": True,
            "showNodes": True,
            "showCandidates": True,
            "showLabels": False,
        }

    @objc.python_method
    def _localize_ui(self):
        self._set_label(self.rowsLabel, {"en": "R", "ja": "行"})
        self._set_label(self.colsLabel, {"en": "C", "ja": "列"})
        self._set_label(self.spacingLabel, {"en": "Spacing", "ja": "間隔"})
        self._set_label(self.diameterLabel, {"en": "Dia", "ja": "直径"})
        self._set_label(self.xOffsetLabel, {"en": "X", "ja": "X"})
        self._set_label(self.yOffsetLabel, {"en": "Y", "ja": "Y"})
        self._set_button_title(self.showGridCheckBox, {"en": "Grid", "ja": "グリッド"})
        self._set_button_title(self.showNodesCheckBox, {"en": "Nodes", "ja": "ノード"})
        self._set_button_title(self.showCandidatesCheckBox, {"en": "Candidates", "ja": "候補"})
        self._set_button_title(self.showLabelsCheckBox, {"en": "Labels", "ja": "ラベル"})
        self._set_button_title(self.applyButton, {"en": "Apply", "ja": "適用"})
        self._set_button_title(self.undoButton, {"en": "Undo", "ja": "戻す"})
        self._set_button_title(self.clearButton, {"en": "Clear", "ja": "消去"})
        if self.outputModeSegmentedControl is not None:
            self.outputModeSegmentedControl.setLabel_forSegment_(Glyphs.localize({"en": "Filled", "ja": "塗り"}), 0)
            self.outputModeSegmentedControl.setLabel_forSegment_(Glyphs.localize({"en": "Line", "ja": "線"}), 1)

    @objc.python_method
    def _set_label(self, label, localized):
        if label is not None:
            label.setStringValue_(Glyphs.localize(localized))

    @objc.python_method
    def _set_button_title(self, button, localized):
        if button is not None:
            button.setTitle_(Glyphs.localize(localized))

    @objc.python_method
    def _apply_readable_colours(self):
        label_colour = NSColor.colorWithCalibratedWhite_alpha_(0.0, 0.78)
        field_colour = NSColor.colorWithCalibratedWhite_alpha_(0.0, 1.0)
        for label in (
            self.rowsLabel,
            self.colsLabel,
            self.spacingLabel,
            self.diameterLabel,
            self.xOffsetLabel,
            self.yOffsetLabel,
        ):
            if label is not None:
                label.setTextColor_(label_colour)

        for field in (
            self.rowsTextField,
            self.colsTextField,
            self.spacingTextField,
            self.diameterTextField,
            self.xOffsetTextField,
            self.yOffsetTextField,
        ):
            if field is not None:
                field.setTextColor_(field_colour)
                field.setBackgroundColor_(NSColor.whiteColor())

        for button in (
            self.showGridCheckBox,
            self.showNodesCheckBox,
            self.showCandidatesCheckBox,
            self.showLabelsCheckBox,
        ):
            self._set_button_title_colour(button, label_colour)
        # Action buttons (Apply/Undo/Clear) keep the system bezeled appearance -
        # don't override their title attributes or they look like flat labels.

    @objc.python_method
    def _set_button_title_colour(self, button, colour):
        if button is None:
            return
        font = button.font()
        if font is None:
            font = NSFont.systemFontOfSize_(NSFont.smallSystemFontSize())
        title = button.title()
        attrs = {
            NSForegroundColorAttributeName: colour,
            NSFontAttributeName: font,
        }
        attr_title = NSAttributedString.alloc().initWithString_attributes_(title, attrs)
        button.setAttributedTitle_(attr_title)

    @objc.python_method
    def _settings_from_defaults(self):
        s = self._default_settings()
        s["rows"] = max(1, _int_default("rows", s["rows"]))
        s["cols"] = max(1, _int_default("cols", s["cols"]))
        s["spacing"] = max(1.0, _float_default("spacing", s["spacing"]))
        s["diameter"] = max(1.0, _float_default("diameter", s["diameter"]))
        s["xOffset"] = _float_default("xOffset", s["xOffset"])
        s["yOffset"] = _float_default("yOffset", s["yOffset"])
        s["outputMode"] = Glyphs.defaults.get(PREF + ".outputMode", s["outputMode"])
        s["showGrid"] = _bool_default("showGrid", s["showGrid"])
        s["showNodes"] = _bool_default("showNodes", s["showNodes"])
        s["showCandidates"] = _bool_default("showCandidates", s["showCandidates"])
        s["showLabels"] = _bool_default("showLabels", s["showLabels"])
        if s["outputMode"] not in ("filled", "centerline"):
            s["outputMode"] = "filled"
        return s

    @objc.python_method
    def _load_settings_to_ui(self):
        s = self._settings_from_defaults()
        self._set_field_value(self.rowsTextField, s["rows"])
        self._set_field_value(self.colsTextField, s["cols"])
        self._set_field_value(self.spacingTextField, s["spacing"])
        self._set_field_value(self.diameterTextField, s["diameter"])
        self._set_field_value(self.xOffsetTextField, s["xOffset"])
        self._set_field_value(self.yOffsetTextField, s["yOffset"])
        if self.outputModeSegmentedControl:
            self.outputModeSegmentedControl.setSelectedSegment_(1 if s["outputMode"] == "centerline" else 0)
        self._set_checkbox_state(self.showGridCheckBox, s["showGrid"])
        self._set_checkbox_state(self.showNodesCheckBox, s["showNodes"])
        self._set_checkbox_state(self.showCandidatesCheckBox, s["showCandidates"])
        self._set_checkbox_state(self.showLabelsCheckBox, s["showLabels"])

    @objc.python_method
    def _save_settings_from_ui(self):
        s = self._default_settings()
        s["rows"] = max(1, self._read_int(self.rowsTextField, s["rows"]))
        s["cols"] = max(1, self._read_int(self.colsTextField, s["cols"]))
        s["spacing"] = max(1.0, self._read_float(self.spacingTextField, s["spacing"]))
        s["diameter"] = max(1.0, self._read_float(self.diameterTextField, s["diameter"]))
        s["xOffset"] = self._read_float(self.xOffsetTextField, s["xOffset"])
        s["yOffset"] = self._read_float(self.yOffsetTextField, s["yOffset"])
        if self.outputModeSegmentedControl and self.outputModeSegmentedControl.selectedSegment() == 1:
            s["outputMode"] = "centerline"
        s["showGrid"] = self._checkbox_on(self.showGridCheckBox, s["showGrid"])
        s["showNodes"] = self._checkbox_on(self.showNodesCheckBox, s["showNodes"])
        s["showCandidates"] = self._checkbox_on(self.showCandidatesCheckBox, s["showCandidates"])
        s["showLabels"] = self._checkbox_on(self.showLabelsCheckBox, s["showLabels"])

        d = Glyphs.defaults
        d[PREF + ".rows"] = s["rows"]
        d[PREF + ".cols"] = s["cols"]
        d[PREF + ".spacing"] = s["spacing"]
        d[PREF + ".diameter"] = s["diameter"]
        d[PREF + ".xOffset"] = s["xOffset"]
        d[PREF + ".yOffset"] = s["yOffset"]
        d[PREF + ".outputMode"] = s["outputMode"]
        d[PREF + ".showGrid"] = s["showGrid"]
        d[PREF + ".showNodes"] = s["showNodes"]
        d[PREF + ".showCandidates"] = s["showCandidates"]
        d[PREF + ".showLabels"] = s["showLabels"]
        return s

    @objc.python_method
    def _set_field_value(self, field, value):
        if field is not None:
            if isinstance(value, int):
                field.setStringValue_(str(value))
            else:
                field.setStringValue_("%g" % value)

    @objc.python_method
    def _set_checkbox_state(self, checkbox, value):
        if checkbox is not None:
            checkbox.setState_(1 if value else 0)

    @objc.python_method
    def _read_int(self, field, fallback):
        try:
            return int(float(field.stringValue()))
        except Exception:
            return int(fallback)

    @objc.python_method
    def _read_float(self, field, fallback):
        try:
            return float(field.stringValue())
        except Exception:
            return float(fallback)

    @objc.python_method
    def _checkbox_on(self, checkbox, fallback):
        if checkbox is None:
            return bool(fallback)
        return checkbox.state() == 1

    @objc.python_method
    def _layer_metrics(self, layer):
        master = layer.associatedFontMaster()
        if master is None:
            return 800.0, -200.0
        return float(master.ascender), float(master.descender)

    @objc.python_method
    def _grid_points(self, layer, s):
        ascender, descender = self._layer_metrics(layer)
        origin = grid_origin(
            float(layer.width),
            ascender,
            descender,
            s["rows"],
            s["cols"],
            s["spacing"],
            s["xOffset"],
            s["yOffset"],
        )
        points = []
        for row in range(s["rows"]):
            for col in range(s["cols"]):
                node = GridNode(row, col)
                points.append((node, node_point(origin, node, s["spacing"])))
        return origin, points

    @objc.python_method
    def _grid_point_map(self, layer, s):
        origin, points = self._grid_points(layer, s)
        return dict(points)

    def mouseDown_(self, event):
        loc = self.editViewController().graphicView().getActiveLocation_(event)
        layer = self.editViewController().graphicView().activeLayer()
        if layer is None:
            return
        s = self._save_settings_from_ui()
        point = Point(float(loc.x), float(loc.y))
        if self._candidate_segments:
            candidate = self._nearest_candidate(point, s)
            if candidate is not None:
                self._accept_candidate(candidate)
                Glyphs.redraw()
                return
        node = self._nearest_node(layer, point, s)
        if node is not None:
            self._handle_node_click(layer, node, s)
            Glyphs.redraw()
            return
        objc.super(HofmannTool, self).mouseDown_(event)

    @objc.python_method
    def _handle_node_click(self, layer, node, s):
        if self._active_node is None or self._closed:
            self._preview_segments = []
            self._candidate_segments = []
            self._start_node = node
            self._active_node = node
            self._closed = False
            return
        if node == self._active_node:
            return
        point_map = self._grid_point_map(layer, s)
        if self._active_node not in point_map or node not in point_map:
            self._preview_segments = []
            self._candidate_segments = []
            self._start_node = node
            self._active_node = node
            self._closed = False
            return
        required_flow_a = self._preview_segments[-1].flow_b if self._preview_segments else None
        required_flow_b = None
        if self._preview_segments and node == self._start_node:
            required_flow_b = self._preview_segments[0].flow_a
        self._candidate_segments = create_tangent_candidates(
            self._active_node,
            node,
            point_map[self._active_node],
            point_map[node],
            s["diameter"],
            required_flow_a=required_flow_a,
            required_flow_b=required_flow_b,
        )

    @objc.python_method
    def _accept_candidate(self, candidate):
        self._preview_segments.append(candidate)
        self._candidate_segments = []
        self._active_node = candidate.node_b
        self._closed = is_closed_contour(self._preview_segments)
        if self._closed:
            self._active_node = None

    @objc.python_method
    def _nearest_node(self, layer, point, s):
        try:
            scale = self.editViewController().graphicView().scale()
        except Exception:
            scale = 1.0
        threshold = max(8.0 / scale if scale else 8.0, min(s["spacing"] * 0.22, s["diameter"] * 0.35))
        nearest = None
        nearest_distance = None
        for node, center in self._grid_points(layer, s)[1]:
            distance = point.sub(center).length()
            if distance <= threshold and (nearest_distance is None or distance < nearest_distance):
                nearest = node
                nearest_distance = distance
        return nearest

    @objc.python_method
    def _nearest_candidate(self, point, s):
        threshold = max(5.0, min(s["spacing"] * 0.12, 12.0))
        nearest = None
        nearest_distance = None
        for candidate in self._candidate_segments:
            distance = self._distance_to_segment(point, candidate.point_a, candidate.point_b)
            if distance <= threshold and (nearest_distance is None or distance < nearest_distance):
                nearest = candidate
                nearest_distance = distance
        return nearest

    @objc.python_method
    def _distance_to_segment(self, point, start, end):
        segment = end.sub(start)
        length_sq = segment.x * segment.x + segment.y * segment.y
        if length_sq <= 0.0:
            return point.sub(start).length()
        t = ((point.x - start.x) * segment.x + (point.y - start.y) * segment.y) / length_sq
        t = max(0.0, min(1.0, t))
        projection = Point(start.x + segment.x * t, start.y + segment.y * t)
        return point.sub(projection).length()

    @objc.python_method
    def background(self, layer):
        s = self._settings_from_defaults()
        try:
            scale = self.editViewController().graphicView().scale()
        except Exception:
            scale = 1.0
        line_width = 1.0 / scale if scale else 1.0
        origin, points = self._grid_points(layer, s)
        if s["showGrid"]:
            self._draw_grid(points, s, line_width)
        if s["showNodes"]:
            self._draw_diameter_circles(points, s, line_width)
            self._draw_node_dots(points, scale)
        self._draw_active_circles(points, s, line_width)
        self._draw_preview_segments(line_width)
        if s["showCandidates"]:
            self._draw_candidate_segments(line_width)
        if s["showLabels"]:
            self._draw_labels(points, scale)

    @objc.python_method
    def _draw_grid(self, points, s, line_width):
        if not points:
            return
        NSColor.colorWithCalibratedWhite_alpha_(0.0, 0.18).set()
        path = NSBezierPath.alloc().init()
        path.setLineWidth_(line_width)
        by_row = {}
        by_col = {}
        for node, point in points:
            by_row.setdefault(node.row, []).append(point)
            by_col.setdefault(node.col, []).append(point)
        for row_points in by_row.values():
            row_points.sort(key=lambda p: p.x)
            self._append_polyline(path, row_points)
        for col_points in by_col.values():
            col_points.sort(key=lambda p: p.y)
            self._append_polyline(path, col_points)
        path.stroke()

    @objc.python_method
    def _append_polyline(self, path, points):
        if not points:
            return
        path.moveToPoint_(NSMakePoint(points[0].x, points[0].y))
        for point in points[1:]:
            path.lineToPoint_(NSMakePoint(point.x, point.y))

    @objc.python_method
    def _draw_diameter_circles(self, points, s, line_width):
        radius = max(0.5, float(s["diameter"]) * 0.5)
        NSColor.colorWithCalibratedWhite_alpha_(0.0, 0.28).set()
        path = NSBezierPath.alloc().init()
        path.setLineWidth_(max(line_width, 0.75))
        for node, center in points:
            rect = NSMakeRect(center.x - radius, center.y - radius, radius * 2.0, radius * 2.0)
            path.appendBezierPathWithOvalInRect_(rect)
        path.stroke()

    @objc.python_method
    def _draw_node_dots(self, points, scale):
        dot_radius = max(1.25 / scale if scale else 1.25, 1.0)
        NSColor.colorWithCalibratedWhite_alpha_(0.0, 0.45).set()
        for node, center in points:
            rect = NSMakeRect(center.x - dot_radius, center.y - dot_radius, dot_radius * 2.0, dot_radius * 2.0)
            NSBezierPath.bezierPathWithOvalInRect_(rect).fill()

    @objc.python_method
    def _draw_active_circles(self, points, s, line_width):
        if self._start_node is None and self._active_node is None:
            return
        point_map = dict(points)
        radius = max(0.5, float(s["diameter"]) * 0.5)
        for node, color in (
            (self._start_node, NSColor.colorWithCalibratedRed_green_blue_alpha_(0.1, 0.35, 1.0, 0.9)),
            (self._active_node, NSColor.colorWithCalibratedRed_green_blue_alpha_(1.0, 0.35, 0.1, 0.9)),
        ):
            if node is None or node not in point_map:
                continue
            center = point_map[node]
            color.set()
            path = NSBezierPath.alloc().init()
            path.setLineWidth_(max(line_width * 2.0, 1.5))
            rect = NSMakeRect(center.x - radius, center.y - radius, radius * 2.0, radius * 2.0)
            path.appendBezierPathWithOvalInRect_(rect)
            path.stroke()

    @objc.python_method
    def _draw_preview_segments(self, line_width):
        if not self._preview_segments:
            return
        NSColor.colorWithCalibratedRed_green_blue_alpha_(0.05, 0.25, 1.0, 0.9).set()
        path = NSBezierPath.alloc().init()
        path.setLineWidth_(max(line_width * 1.6, 1.0))
        self._build_segment_path(path, self._preview_segments, closed=self._closed)
        path.stroke()

    @objc.python_method
    def _draw_candidate_segments(self, line_width):
        if not self._candidate_segments:
            return
        NSColor.colorWithCalibratedRed_green_blue_alpha_(1.0, 0.35, 0.0, 0.7).set()
        path = NSBezierPath.alloc().init()
        path.setLineWidth_(max(line_width * 1.3, 1.0))
        last_preview = self._preview_segments[-1] if self._preview_segments else None
        first_preview = self._preview_segments[0] if self._preview_segments else None
        for candidate in self._candidate_segments:
            radius = candidate_radius(candidate)
            # Optional connecting arc on circle A from the last confirmed segment.
            if last_preview is not None:
                path.moveToPoint_(NSMakePoint(last_preview.point_b.x, last_preview.point_b.y))
                self._append_arc_to_path(
                    path,
                    candidate.center_a,
                    radius,
                    last_preview.angle_b,
                    candidate.angle_a,
                    candidate.flow_a,
                )
            else:
                path.moveToPoint_(NSMakePoint(candidate.point_a.x, candidate.point_a.y))
            path.lineToPoint_(NSMakePoint(candidate.point_b.x, candidate.point_b.y))
            # If this candidate would close the contour, also draw the closing arc.
            if (
                first_preview is not None
                and candidate.node_b == self._start_node
                and candidate.flow_b == first_preview.flow_a
            ):
                self._append_arc_to_path(
                    path,
                    candidate.center_b,
                    radius,
                    candidate.angle_b,
                    first_preview.angle_a,
                    candidate.flow_b,
                )
        path.stroke()

    @objc.python_method
    def _build_segment_path(self, path, segments, closed):
        if not segments:
            return
        first = segments[0]
        path.moveToPoint_(NSMakePoint(first.point_a.x, first.point_a.y))
        for index, seg in enumerate(segments):
            path.lineToPoint_(NSMakePoint(seg.point_b.x, seg.point_b.y))
            if index + 1 < len(segments):
                next_seg = segments[index + 1]
                self._append_arc_to_path(
                    path,
                    seg.center_b,
                    candidate_radius(seg),
                    seg.angle_b,
                    next_seg.angle_a,
                    seg.flow_b,
                )
        if closed:
            last = segments[-1]
            self._append_arc_to_path(
                path,
                last.center_b,
                candidate_radius(last),
                last.angle_b,
                first.angle_a,
                last.flow_b,
            )
            path.closePath()

    @objc.python_method
    def _append_arc_to_path(self, path, center, radius, start_angle_deg, end_angle_deg, flow):
        bez_segments = arc_to_bezier_segments(center, radius, start_angle_deg, end_angle_deg, flow)
        for (_p0, p1, p2, p3) in bez_segments:
            path.curveToPoint_controlPoint1_controlPoint2_(
                NSMakePoint(p3.x, p3.y),
                NSMakePoint(p1.x, p1.y),
                NSMakePoint(p2.x, p2.y),
            )

    @objc.python_method
    def _draw_labels(self, points, scale):
        font_size = max(7.0, 9.0 / scale if scale else 9.0)
        attrs = {
            NSFontAttributeName: NSFont.systemFontOfSize_(font_size),
            NSForegroundColorAttributeName: NSColor.colorWithCalibratedWhite_alpha_(0.0, 0.45),
        }
        offset = 5.0 / scale if scale else 5.0
        for node, point in points:
            text = NSString.stringWithString_("%d,%d" % (node.row, node.col))
            text.drawAtPoint_withAttributes_(NSMakePoint(point.x + offset, point.y + offset), attrs)

    @objc.IBAction
    def handleSettingsAction_(self, sender):
        self._save_settings_from_ui()
        Glyphs.redraw()

    @objc.IBAction
    def applyAction_(self, sender):
        s = self._save_settings_from_ui()
        layer = self._current_layer()
        if layer is None:
            print("HofmannTool: no active layer to apply to.")
            return
        if not self._preview_segments:
            print("HofmannTool: nothing to apply yet - pick at least one tangent.")
            return
        if s["outputMode"] == "filled" and not self._closed:
            print("HofmannTool: Filled mode requires a closed contour. Close the loop or switch to Line mode.")
            return
        path = self._build_gs_path_from_segments(
            self._preview_segments,
            include_closing_arc=self._closed,
            path_closed=(self._closed and s["outputMode"] == "filled"),
        )
        if path is None:
            return
        self._append_path_to_layer(layer, path)
        Glyphs.redraw()

    @objc.python_method
    def _current_layer(self):
        try:
            return self.editViewController().graphicView().activeLayer()
        except Exception:
            return None

    @objc.python_method
    def _build_gs_path_from_segments(self, segments, include_closing_arc=False, path_closed=False):
        if not segments:
            return None
        path = GSPath()
        first = segments[0]
        closing_bez_segments = None
        if include_closing_arc:
            last = segments[-1]
            closing_bez_segments = arc_to_bezier_segments(
                last.center_b,
                candidate_radius(last),
                last.angle_b,
                first.angle_a,
                last.flow_b,
            )
        # For filled closed paths, the first on-curve doubles as the closing-arc
        # endpoint. Line mode may still include that arc, but remains open.
        first_type = CURVE if path_closed and closing_bez_segments else LINE
        path.nodes.append(GSNode((float(first.point_a.x), float(first.point_a.y)), first_type))
        for index, seg in enumerate(segments):
            path.nodes.append(GSNode((float(seg.point_b.x), float(seg.point_b.y)), LINE))
            if index + 1 < len(segments):
                next_seg = segments[index + 1]
                self._append_bezier_arc_to_gs_path(
                    path,
                    seg.center_b,
                    candidate_radius(seg),
                    seg.angle_b,
                    next_seg.angle_a,
                    seg.flow_b,
                    final_curve=True,
                )
        if closing_bez_segments:
            # Filled paths land the closing arc at node[0]; open line-mode paths
            # emit the final curve endpoint explicitly and keep path.closed False.
            self._append_bezier_segments_to_gs_path(path, closing_bez_segments, final_curve=not path_closed)
        path.closed = bool(path_closed)
        return path

    @objc.python_method
    def _append_bezier_arc_to_gs_path(self, path, center, radius, start_angle, end_angle, flow, final_curve=True):
        bez_segments = arc_to_bezier_segments(center, radius, start_angle, end_angle, flow)
        self._append_bezier_segments_to_gs_path(path, bez_segments, final_curve=final_curve)

    @objc.python_method
    def _append_bezier_segments_to_gs_path(self, path, bez_segments, final_curve=True):
        last_index = len(bez_segments) - 1
        for index, (_p0, p1, p2, p3) in enumerate(bez_segments):
            path.nodes.append(GSNode((float(p1.x), float(p1.y)), OFFCURVE))
            path.nodes.append(GSNode((float(p2.x), float(p2.y)), OFFCURVE))
            if final_curve or index < last_index:
                path.nodes.append(GSNode((float(p3.x), float(p3.y)), CURVE))

    @objc.python_method
    def _append_path_to_layer(self, layer, path):
        began = False
        if hasattr(layer, "beginChanges"):
            try:
                layer.beginChanges()
                began = True
            except Exception:
                began = False
        try:
            layer.paths.append(path)
        finally:
            if began:
                try:
                    layer.endChanges()
                except Exception:
                    pass

    @objc.IBAction
    def undoStepAction_(self, sender):
        self._candidate_segments = []
        if self._preview_segments:
            self._preview_segments.pop()
        self._closed = is_closed_contour(self._preview_segments)
        if self._preview_segments:
            self._active_node = self._preview_segments[-1].node_b
        else:
            self._active_node = self._start_node
        Glyphs.redraw()

    @objc.IBAction
    def clearAction_(self, sender):
        self._preview_segments = []
        self._candidate_segments = []
        self._start_node = None
        self._active_node = None
        self._closed = False
        Glyphs.redraw()

    @objc.python_method
    def __file__(self):
        return __file__
