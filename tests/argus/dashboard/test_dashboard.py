"""Tests for M7 Dashboard Engine."""

from argus.dashboard.app import (
    _affine_from_graph,
    _cfg_critical_node_color,
    _cfg_flood_color,
    _cfg_road_color,
    _cfg_route_color,
    _heatmap_color,
)


class TestConfigLoading:
    """Dashboard.yaml config is loaded at module level and drives UI."""

    def test_road_color_from_config(self):
        color = _cfg_road_color()
        assert color.startswith("#")
        assert len(color) == 7

    def test_critical_node_color_from_config(self):
        color = _cfg_critical_node_color()
        assert len(color) == 3
        assert all(isinstance(c, int) for c in color)

    def test_flood_color_from_config(self):
        color = _cfg_flood_color()
        assert color.startswith("#")
        assert len(color) == 7

    def test_route_color_from_config(self):
        color = _cfg_route_color()
        assert color.startswith("#")
        assert len(color) == 7


class TestHeatmapColor:
    """heatmap_color produces valid hex gradient."""

    def test_zero_ratio_is_green(self):
        color = _heatmap_color(0.0)
        assert color.startswith("#")
        # At ratio 0, g is ~255, r is 0
        assert int(color[3:5], 16) > 200  # green channel high

    def test_one_ratio_is_red(self):
        color = _heatmap_color(1.0)
        assert color.startswith("#")
        assert int(color[1:3], 16) > 200  # red channel high

    def test_half_ratio_is_yellowish(self):
        color = _heatmap_color(0.5)
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        assert r > 100 and g > 100


class TestAffineTransform:
    """affine_from_graph extracts transform or returns identity."""

    class FakeGraph:
        def __init__(self, transform=None):
            self.metadata = {"transform": transform} if transform else {}

    def test_identity_fallback(self):
        result = _affine_from_graph(self.FakeGraph())
        assert result == (1.0, 0.0, 0.0, 0.0, -1.0, 0.0)

    def test_with_six_param_transform(self):
        a, b, c, d, e, f = _affine_from_graph(self.FakeGraph([1, 0, 100, 0, -1, 200]))
        assert a == 1.0
        assert c == 100.0
        assert e == -1.0
        assert f == 200.0

    def test_with_non_six_transform_ignored(self):
        a, b, c, d, e, f = _affine_from_graph(self.FakeGraph([1, 2, 3]))
        assert (a, b, c, d, e, f) == (1.0, 0.0, 0.0, 0.0, -1.0, 0.0)
