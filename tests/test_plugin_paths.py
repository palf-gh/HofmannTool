import importlib
import os
import sys
import types
import unittest


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESOURCES = os.path.join(ROOT, "HofmannTool.glyphsTool", "Contents", "Resources")


def install_glyphs_stubs():
    line = "line"
    curve = "curve"
    offcurve = "offcurve"
    smooth = "smooth"

    objc = types.ModuleType("objc")
    objc.IBOutlet = lambda: None
    objc.IBAction = lambda fn: fn
    objc.python_method = lambda fn: fn
    objc.lookUpClass = lambda _name: object
    objc.super = super
    sys.modules["objc"] = objc

    class NodeList(list):
        def __init__(self, path):
            super(NodeList, self).__init__()
            self.path = path

        def append(self, node):
            node.parentPath = self.path
            super(NodeList, self).append(node)

    class DummyPath:
        def __init__(self):
            self.closed = False
            self._nodes = NodeList(self)

        @property
        def nodes(self):
            return self._nodes

        @nodes.setter
        def nodes(self, values):
            nodes = NodeList(self)
            for node in values:
                nodes.append(node)
            self._nodes = nodes

        def makeNodeFirst_(self, node):
            index = self._nodes.index(node)
            self.nodes = list(self._nodes[index:]) + list(self._nodes[:index])

    class DummyNode:
        def __init__(self, position, **kwargs):
            self.position = types.SimpleNamespace(x=position[0], y=position[1])
            self.type = kwargs.get("type", line)
            self.connection = None
            self.parentPath = None

        def makeNodeFirst(self):
            self.parentPath.makeNodeFirst_(self)

    class DummyGlyphs:
        defaults = {}

        @staticmethod
        def redraw():
            pass

    glyphs_app = types.ModuleType("GlyphsApp")
    glyphs_app.Glyphs = DummyGlyphs
    glyphs_app.GSPath = DummyPath
    glyphs_app.GSNode = DummyNode
    glyphs_app.LINE = line
    glyphs_app.CURVE = curve
    glyphs_app.OFFCURVE = offcurve
    glyphs_app.GSSMOOTH = smooth
    sys.modules["GlyphsApp"] = glyphs_app

    plugins = types.ModuleType("GlyphsApp.plugins")
    plugins.SelectTool = object
    sys.modules["GlyphsApp.plugins"] = plugins

    appkit = types.ModuleType("AppKit")
    appkit.NSApplication = object
    appkit.NSBezierPath = object
    appkit.NSColor = object
    appkit.NSMakePoint = lambda x, y: (x, y)
    appkit.NSMakeRect = lambda x, y, width, height: (x, y, width, height)
    appkit.NSEventModifierFlagCommand = 1 << 20
    appkit.NSEventModifierFlagShift = 1 << 17
    sys.modules["AppKit"] = appkit

    foundation = types.ModuleType("Foundation")
    foundation.NSSelectorFromString = lambda value: value
    sys.modules["Foundation"] = foundation


class HofmannPluginPathTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        install_glyphs_stubs()
        if RESOURCES not in sys.path:
            sys.path.insert(0, RESOURCES)
        sys.modules.pop("plugin", None)
        cls.plugin = importlib.import_module("plugin")

    def path_area(self, path):
        points = [
            (node.position.x, node.position.y)
            for node in path.nodes
            if node.type != self.plugin.OFFCURVE
        ]
        area = 0.0
        for (x1, y1), (x2, y2) in zip(points, points[1:] + points[:1]):
            area += x1 * y2 - x2 * y1
        return area * 0.5

    def test_single_circle_has_explicit_first_oncurve_node(self):
        tool = self.plugin.HofmannTool()

        path = tool._build_single_circle_gs_path(self.plugin.Point(10, 20), 100)

        self.assertTrue(path.closed)
        self.assertEqual(len(path.nodes), 12)
        self.assertEqual(path.nodes[0].type, self.plugin.CURVE)
        self.assertEqual(path.nodes[0].connection, self.plugin.SMOOTH)
        self.assertAlmostEqual(path.nodes[0].position.x, 60.0)
        self.assertAlmostEqual(path.nodes[0].position.y, 20.0)

        curve_indices = [
            index for index, node in enumerate(path.nodes)
            if node.type == self.plugin.CURVE
        ]
        self.assertEqual(len(curve_indices), 4)
        for index in curve_indices:
            self.assertEqual(
                path.nodes[(index - 2) % len(path.nodes)].type,
                self.plugin.OFFCURVE,
            )
            self.assertEqual(
                path.nodes[(index - 1) % len(path.nodes)].type,
                self.plugin.OFFCURVE,
            )

    def test_single_circle_filled_uses_clockwise_direction(self):
        tool = self.plugin.HofmannTool()

        path = tool._build_single_circle_gs_path(self.plugin.Point(10, 20), 100)

        self.assertLess(self.path_area(path), 0.0)

    def test_single_circle_hole_uses_counterclockwise_direction(self):
        tool = self.plugin.HofmannTool()

        path = tool._build_single_circle_gs_path(self.plugin.Point(10, 20), 100, hole=True)

        self.assertGreater(self.path_area(path), 0.0)


if __name__ == "__main__":
    unittest.main()
