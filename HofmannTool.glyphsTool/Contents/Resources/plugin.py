# encoding: utf-8
from __future__ import division, print_function, unicode_literals

import os
import sys
import objc

from GlyphsApp import Glyphs, GSPath, GSNode, LINE, CURVE, OFFCURVE
from GlyphsApp.plugins import SelectTool
from AppKit import (
    NSApplication,
    NSBezierPath,
    NSColor,
    NSMakePoint,
    NSMakeRect,
)
from Foundation import NSSelectorFromString

try:
    from AppKit import NSEventModifierFlagCommand, NSEventModifierFlagShift
except Exception:
    NSEventModifierFlagShift = 1 << 17
    NSEventModifierFlagCommand = 1 << 20

RESOURCE_DIR = os.path.dirname(os.path.abspath(__file__))
if RESOURCE_DIR not in sys.path:
    sys.path.insert(0, RESOURCE_DIR)

from hofmann_geometry import GridNode, grid_origin, node_point
from hofmann_geometry import Point, create_tangent_candidate, create_tangent_candidates, is_closed_contour
from hofmann_geometry import (
    FLOW_CCW,
    FLOW_CW,
    arc_to_bezier_segments,
    candidate_radius,
)


PREF = "com.palf.HofmannTool"
MAX_HISTORY = 100


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
    applyButton = objc.IBOutlet()
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
        self._undo_stack = []
        self._redo_stack = []
        self._tool_is_active = False
        self._menu_override_records = []
        self._reset_interaction_state()

    def view(self):
        return self.inspectorDialogView

    @objc.python_method
    def activate(self):
        self._tool_is_active = True
        self._sync_edit_undo_menu_override()
        Glyphs.redraw()

    @objc.python_method
    def deactivate(self):
        self._tool_is_active = False
        self._restore_edit_undo_menu_override()
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
        }

    @objc.python_method
    def _localize_ui(self):
        self._set_label(self.rowsLabel, {"en": "R", "ja": "行"})
        self._set_label(self.colsLabel, {"en": "C", "ja": "列"})
        self._set_label(self.spacingLabel, {"en": "Spacing", "ja": "間隔"})
        self._set_label(self.diameterLabel, {"en": "Dia", "ja": "直径"})
        self._set_label(self.xOffsetLabel, {"en": "X", "ja": "X"})
        self._set_label(self.yOffsetLabel, {"en": "Y", "ja": "Y"})
        self._set_button_title(self.applyButton, {"en": "Apply", "ja": "適用"})
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

        # Action buttons keep the system bezeled appearance; overriding the
        # attributed title makes them look like flat labels in Glyphs.

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

        d = Glyphs.defaults
        d[PREF + ".rows"] = s["rows"]
        d[PREF + ".cols"] = s["cols"]
        d[PREF + ".spacing"] = s["spacing"]
        d[PREF + ".diameter"] = s["diameter"]
        d[PREF + ".xOffset"] = s["xOffset"]
        d[PREF + ".yOffset"] = s["yOffset"]
        d[PREF + ".outputMode"] = s["outputMode"]
        return s

    @objc.python_method
    def _set_field_value(self, field, value):
        if field is not None:
            if isinstance(value, int):
                field.setStringValue_(str(value))
            else:
                field.setStringValue_("%g" % value)

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

    @objc.python_method
    def _ensure_interaction_storage(self):
        if not hasattr(self, "_undo_stack"):
            self._undo_stack = []
        if not hasattr(self, "_redo_stack"):
            self._redo_stack = []
        if not hasattr(self, "_tool_is_active"):
            self._tool_is_active = False
        if not hasattr(self, "_menu_override_records"):
            self._menu_override_records = []
        if not hasattr(self, "_route_steps"):
            self._reset_interaction_state()

    @objc.python_method
    def _has_tool_undo(self):
        self._ensure_interaction_storage()
        return bool(self._undo_stack)

    @objc.python_method
    def _has_tool_redo(self):
        self._ensure_interaction_storage()
        return bool(self._redo_stack)

    @objc.python_method
    def _should_override_edit_undo(self):
        self._ensure_interaction_storage()
        return self._tool_is_active and (self._has_tool_undo() or self._has_tool_redo())

    @objc.python_method
    def _iter_menu_items(self, menu):
        if menu is None:
            return
        for index in range(menu.numberOfItems()):
            item = menu.itemAtIndex_(index)
            yield item
            submenu = item.submenu()
            if submenu is not None:
                for submenu_item in self._iter_menu_items(submenu):
                    yield submenu_item

    @objc.python_method
    def _undo_redo_menu_items(self):
        found = {"undo": None, "redo": None}
        try:
            main_menu = NSApplication.sharedApplication().mainMenu()
        except Exception:
            return found
        for item in self._iter_menu_items(main_menu):
            try:
                key = item.keyEquivalent().lower()
                mask = item.keyEquivalentModifierMask()
            except Exception:
                continue
            if key != "z" or not (mask & NSEventModifierFlagCommand):
                continue
            if mask & NSEventModifierFlagShift:
                found["redo"] = item
            else:
                found["undo"] = item
        return found

    @objc.python_method
    def _sync_edit_undo_menu_override(self):
        self._ensure_interaction_storage()
        if not self._should_override_edit_undo():
            self._restore_edit_undo_menu_override()
            return
        if self._menu_override_records:
            return
        items = self._undo_redo_menu_items()
        for key, selector_name in (("undo", "undo:"), ("redo", "redo:")):
            item = items.get(key)
            if item is None:
                continue
            self._menu_override_records.append((item, item.target(), item.action()))
            item.setTarget_(self)
            item.setAction_(NSSelectorFromString(selector_name))

    @objc.python_method
    def _restore_edit_undo_menu_override(self):
        if not hasattr(self, "_menu_override_records"):
            self._menu_override_records = []
            return
        for item, target, action in self._menu_override_records:
            try:
                item.setTarget_(target)
                item.setAction_(action)
            except Exception:
                pass
        self._menu_override_records = []

    @objc.python_method
    def _reset_interaction_state(self):
        self._route_steps = []
        self._preview_segments = []
        self._candidate_segments = []
        self._candidate_target_node = None
        self._start_node = None
        self._active_node = None
        self._closed = False

    @objc.python_method
    def _node_snapshot(self, node):
        if node is None:
            return None
        return (int(node.row), int(node.col))

    @objc.python_method
    def _node_from_snapshot(self, value):
        if value is None:
            return None
        return GridNode(int(value[0]), int(value[1]))

    @objc.python_method
    def _snapshot_state(self):
        self._ensure_interaction_storage()
        return {
            "route": [
                (
                    self._node_snapshot(step[0]),
                    self._node_snapshot(step[1]),
                    step[2],
                    step[3],
                )
                for step in self._route_steps
            ],
            "start": self._node_snapshot(self._start_node),
            "active": self._node_snapshot(self._active_node),
            "target": self._node_snapshot(self._candidate_target_node),
            "closed": bool(self._closed),
        }

    @objc.python_method
    def _restore_state(self, snapshot):
        self._ensure_interaction_storage()
        self._route_steps = [
            (
                self._node_from_snapshot(step[0]),
                self._node_from_snapshot(step[1]),
                step[2],
                step[3],
            )
            for step in snapshot.get("route", [])
        ]
        self._start_node = self._node_from_snapshot(snapshot.get("start"))
        self._active_node = self._node_from_snapshot(snapshot.get("active"))
        self._candidate_target_node = self._node_from_snapshot(snapshot.get("target"))
        self._closed = bool(snapshot.get("closed", False))
        self._preview_segments = []
        self._candidate_segments = []
        layer = self._current_layer()
        if layer is not None:
            self._refresh_geometry_from_settings(layer, self._save_settings_from_ui())

    @objc.python_method
    def _push_history(self):
        self._ensure_interaction_storage()
        snapshot = self._snapshot_state()
        if self._undo_stack and self._undo_stack[-1] == snapshot:
            return
        self._undo_stack.append(snapshot)
        if len(self._undo_stack) > MAX_HISTORY:
            del self._undo_stack[0]
        self._redo_stack = []
        self._sync_edit_undo_menu_override()

    @objc.python_method
    def _undo_history(self):
        self._ensure_interaction_storage()
        if not self._undo_stack:
            return False
        current = self._snapshot_state()
        previous = self._undo_stack.pop()
        self._redo_stack.append(current)
        if len(self._redo_stack) > MAX_HISTORY:
            del self._redo_stack[0]
        self._restore_state(previous)
        self._sync_edit_undo_menu_override()
        return True

    @objc.python_method
    def _redo_history(self):
        self._ensure_interaction_storage()
        if not self._redo_stack:
            return False
        current = self._snapshot_state()
        next_snapshot = self._redo_stack.pop()
        self._undo_stack.append(current)
        if len(self._undo_stack) > MAX_HISTORY:
            del self._undo_stack[0]
        self._restore_state(next_snapshot)
        self._sync_edit_undo_menu_override()
        return True

    @objc.python_method
    def _has_interaction_state(self):
        self._ensure_interaction_storage()
        return bool(self._route_steps or self._candidate_target_node or self._start_node or self._active_node)

    @objc.python_method
    def _route_step_for_candidate(self, candidate):
        return (candidate.node_a, candidate.node_b, candidate.flow_a, candidate.flow_b)

    @objc.python_method
    def _candidate_for_route_step(self, step, point_map, diameter):
        node_a, node_b, flow_a, flow_b = step
        if node_a not in point_map or node_b not in point_map:
            return None
        return create_tangent_candidate(
            node_a,
            node_b,
            point_map[node_a],
            point_map[node_b],
            diameter,
            flow_a,
            flow_b,
        )

    @objc.python_method
    def _refresh_geometry_from_settings(self, layer, s):
        self._ensure_interaction_storage()
        point_map = self._grid_point_map(layer, s)
        rebuilt_segments = []
        for step in self._route_steps:
            candidate = self._candidate_for_route_step(step, point_map, s["diameter"])
            if candidate is None:
                break
            rebuilt_segments.append(candidate)

        self._preview_segments = rebuilt_segments
        route_is_valid = len(self._preview_segments) == len(self._route_steps)
        self._closed = route_is_valid and is_closed_contour(self._preview_segments)
        if self._closed:
            self._active_node = None
            self._candidate_segments = []
            self._candidate_target_node = None
        elif self._preview_segments:
            self._active_node = self._preview_segments[-1].node_b
        elif self._start_node is not None:
            self._active_node = self._start_node

        if route_is_valid and self._candidate_target_node is not None and self._active_node is not None:
            self._candidate_segments = self._candidates_for_target(layer, self._candidate_target_node, s)
        else:
            self._candidate_segments = []

    @objc.python_method
    def _candidates_for_target(self, layer, node, s):
        if self._active_node is None or node == self._active_node:
            return []
        point_map = self._grid_point_map(layer, s)
        if self._active_node not in point_map or node not in point_map:
            return []
        required_flow_a = self._preview_segments[-1].flow_b if self._preview_segments else None
        required_flow_b = None
        if self._preview_segments and node == self._start_node:
            required_flow_b = self._preview_segments[0].flow_a
        return create_tangent_candidates(
            self._active_node,
            node,
            point_map[self._active_node],
            point_map[node],
            s["diameter"],
            required_flow_a=required_flow_a,
            required_flow_b=required_flow_b,
        )

    def mouseDown_(self, event):
        loc = self.editViewController().graphicView().getActiveLocation_(event)
        layer = self.editViewController().graphicView().activeLayer()
        if layer is None:
            return
        s = self._save_settings_from_ui()
        self._refresh_geometry_from_settings(layer, s)
        point = Point(float(loc.x), float(loc.y))
        try:
            modifiers = event.modifierFlags()
        except Exception:
            modifiers = 0
        if modifiers & NSEventModifierFlagCommand:
            node = self._nearest_node(layer, point, s)
            if node is not None:
                self._spawn_single_circle(layer, node, s)
                Glyphs.redraw()
                return
        if self._candidate_segments:
            candidate = self._nearest_candidate(point, s)
            if candidate is not None:
                self._accept_candidate(layer, candidate, s)
                Glyphs.redraw()
                return
        node = self._nearest_node(layer, point, s)
        if node is not None:
            self._handle_node_click(layer, node, s)
            Glyphs.redraw()
            return
        objc.super(HofmannTool, self).mouseDown_(event)

    def keyDown_(self, event):
        self._ensure_interaction_storage()
        try:
            chars = event.charactersIgnoringModifiers()
            chars = chars.lower() if chars is not None else ""
            flags = event.modifierFlags()
        except Exception:
            chars = ""
            flags = 0

        if chars == "z" and (flags & NSEventModifierFlagCommand):
            if flags & NSEventModifierFlagShift:
                handled = self._redo_history()
            else:
                handled = self._undo_history()
            if handled:
                Glyphs.redraw()
                return
        try:
            objc.super(HofmannTool, self).keyDown_(event)
        except AttributeError:
            pass

    def undo_(self, sender):
        if self._undo_history():
            Glyphs.redraw()

    def redo_(self, sender):
        if self._redo_history():
            Glyphs.redraw()

    def validateMenuItem_(self, menu_item):
        try:
            action_name = str(menu_item.action())
        except Exception:
            return True
        if "undo:" in action_name:
            return self._has_tool_undo()
        if "redo:" in action_name:
            return self._has_tool_redo()
        return True

    @objc.python_method
    def _handle_node_click(self, layer, node, s):
        if self._active_node is None or self._closed:
            self._push_history()
            self._route_steps = []
            self._preview_segments = []
            self._candidate_segments = []
            self._candidate_target_node = None
            self._start_node = node
            self._active_node = node
            self._closed = False
            return
        if node == self._active_node:
            return
        self._push_history()
        self._candidate_target_node = node
        self._candidate_segments = self._candidates_for_target(layer, node, s)

    @objc.python_method
    def _accept_candidate(self, layer, candidate, s):
        self._push_history()
        self._route_steps.append(self._route_step_for_candidate(candidate))
        self._candidate_segments = []
        self._candidate_target_node = None
        self._active_node = candidate.node_b
        self._refresh_geometry_from_settings(layer, s)

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
        self._refresh_geometry_from_settings(layer, s)
        try:
            scale = self.editViewController().graphicView().scale()
        except Exception:
            scale = 1.0
        line_width = 1.0 / scale if scale else 1.0
        origin, points = self._grid_points(layer, s)
        self._draw_grid(points, s, line_width)
        self._draw_diameter_circles(points, s, line_width)
        self._draw_node_dots(points, scale)
        self._draw_active_circles(points, s, line_width)
        self._draw_preview_segments(line_width)
        self._draw_candidate_segments(line_width)

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

    @objc.IBAction
    def handleSettingsAction_(self, sender):
        s = self._save_settings_from_ui()
        layer = self._current_layer()
        if layer is not None:
            self._refresh_geometry_from_settings(layer, s)
        Glyphs.redraw()

    @objc.IBAction
    def applyAction_(self, sender):
        self._ensure_interaction_storage()
        s = self._save_settings_from_ui()
        layer = self._current_layer()
        if layer is None:
            print("HofmannTool: no active layer to apply to.")
            return
        if not self._preview_segments:
            print("HofmannTool: nothing to apply yet - pick at least one tangent.")
            return
        if len(self._preview_segments) != len(self._route_steps):
            print("HofmannTool: current diameter/spacing makes part of the route invalid.")
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
        self._undo_stack = []
        self._redo_stack = []
        self._reset_interaction_state()
        self._sync_edit_undo_menu_override()
        Glyphs.redraw()

    @objc.python_method
    def _spawn_single_circle(self, layer, node, s):
        point_map = self._grid_point_map(layer, s)
        if node not in point_map:
            return
        path = self._build_single_circle_gs_path(point_map[node], s["diameter"])
        if path is None:
            return
        self._append_path_to_layer(layer, path)

    @objc.python_method
    def _build_single_circle_gs_path(self, center, diameter, flow=FLOW_CCW):
        radius = float(diameter) * 0.5
        if radius <= 0.0:
            return None
        bez_segments = arc_to_bezier_segments(center, radius, 0.0, 360.0, flow)
        if not bez_segments:
            return None
        path = GSPath()
        first_p0 = bez_segments[0][0]
        path.nodes.append(GSNode((float(first_p0.x), float(first_p0.y)), CURVE))
        last_index = len(bez_segments) - 1
        for index, (_p0, p1, p2, p3) in enumerate(bez_segments):
            path.nodes.append(GSNode((float(p1.x), float(p1.y)), OFFCURVE))
            path.nodes.append(GSNode((float(p2.x), float(p2.y)), OFFCURVE))
            if index < last_index:
                path.nodes.append(GSNode((float(p3.x), float(p3.y)), CURVE))
        path.closed = True
        return path

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
    def clearAction_(self, sender):
        if self._has_interaction_state():
            self._push_history()
            self._reset_interaction_state()
            self._sync_edit_undo_menu_override()
            Glyphs.redraw()

    @objc.python_method
    def __file__(self):
        return __file__
