# encoding: utf-8
from __future__ import division, print_function, unicode_literals

import os
import sys
import objc

from GlyphsApp import Glyphs
from GlyphsApp.plugins import SelectTool
from AppKit import (
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

    inspectorDialogView = objc.IBOutlet()
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
        self._load_settings_to_ui()

    @objc.python_method
    def start(self):
        self._preview_segments = []
        self._candidate_segments = []
        self._selected_node = None
        self._target_node = None

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
    def background(self, layer):
        s = self._settings_from_defaults()
        if not (s["showGrid"] or s["showNodes"] or s["showLabels"]):
            return
        try:
            scale = self.editViewController().graphicView().scale()
        except Exception:
            scale = 1.0
        line_width = 1.0 / scale if scale else 1.0
        origin, points = self._grid_points(layer, s)
        if s["showGrid"]:
            self._draw_grid(points, s, line_width)
        if s["showNodes"]:
            self._draw_nodes(points, s, scale)
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
    def _draw_nodes(self, points, s, scale):
        radius = max(2.0 / scale if scale else 2.0, min(4.0, s["diameter"] * 0.04))
        NSColor.colorWithCalibratedWhite_alpha_(0.0, 0.28).set()
        for node, point in points:
            rect = NSMakeRect(point.x - radius, point.y - radius, radius * 2.0, radius * 2.0)
            NSBezierPath.bezierPathWithOvalInRect_(rect).fill()

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
        self._save_settings_from_ui()
        print("HofmannTool: Apply will be implemented in the MVP branch.")

    @objc.IBAction
    def undoStepAction_(self, sender):
        self._candidate_segments = []
        if self._preview_segments:
            self._preview_segments.pop()
        Glyphs.redraw()

    @objc.IBAction
    def clearAction_(self, sender):
        self._preview_segments = []
        self._candidate_segments = []
        self._selected_node = None
        self._target_node = None
        Glyphs.redraw()

    @objc.python_method
    def __file__(self):
        return __file__
