# This code is used in the paper
# "Model-based exploration of the frontier of behaviours for deep learning system testing"
# by V. Riccio and P. Tonella
# https://doi.org/10.1145/3368089.3409730

import math
from typing import List, Tuple

import numpy as np
from shapely import geometry

from freneticlib.utils.random import seeded_rng


def catmull_rom_spline(p0, p1, p2, p3, num_points=20):
    """p0, p1, p2, and p3 should be (x,y) point pairs that define the Catmull-Rom spline.
    num_points is the number of points to include in this curve segment."""
    # Convert the points to numpy so that we can do array multiplication
    p0, p1, p2, p3 = map(np.array, [p0, p1, p2, p3])

    # Calculate t0 to t4
    # For knot parametrization
    alpha = 0.5

    def tj(ti, p_i, p_j):
        xi, yi = p_i
        xj, yj = p_j
        return (((xj - xi) ** 2 + (yj - yi) ** 2) ** 0.5) ** alpha + ti

    # Knot sequence
    t0 = 0
    t1 = tj(t0, p0, p1)
    t2 = tj(t1, p1, p2)
    t3 = tj(t2, p2, p3)

    # Only calculate points between p1 and p2
    t = np.linspace(t1, t2, num_points)

    # Reshape so that we can multiply by the points p0 to p3
    # and get a point for each value of t.
    t = t.reshape(len(t), 1)

    a1 = (t1 - t) / (t1 - t0) * p0 + (t - t0) / (t1 - t0) * p1
    a2 = (t2 - t) / (t2 - t1) * p1 + (t - t1) / (t2 - t1) * p2
    a3 = (t3 - t) / (t3 - t2) * p2 + (t - t2) / (t3 - t2) * p3

    b1 = (t2 - t) / (t2 - t0) * a1 + (t - t0) / (t2 - t0) * a2
    b2 = (t3 - t) / (t3 - t1) * a2 + (t - t1) / (t3 - t1) * a3

    c = (t2 - t) / (t2 - t1) * b1 + (t - t1) / (t2 - t1) * b2
    return c


def catmull_rom_chain(points: List[Tuple], num_spline_points=20) -> List:
    """Calculate Catmull-Rom for a chain of points and return the combined curve."""
    # The curve cr will contain an array of (x, y) points.
    cr = []
    for i in range(len(points) - 3):
        c = catmull_rom_spline(points[i], points[i + 1], points[i + 2], points[i + 3], num_spline_points)
        if i > 0:
            c = np.delete(c, [0], axis=0)
        cr.extend(c)
    return cr


def catmull_rom_2d(points: List[Tuple], num_points=20) -> List[Tuple]:
    if len(points) < 4:
        raise ValueError("Need at least 4 points (elements) to calculate catmull_rom")
    np_points_array = catmull_rom_chain(points, num_points)
    return [(p[0], p[1]) for p in np_points_array]


def catmull_rom(points: List[Tuple], num_spline_points=20) -> List[Tuple]:
    if len(points) < 4:
        raise ValueError("Need at least 4 points (elements) to calculate catmull_rom")
    assert all(x[3] == points[0][3] for x in points)
    np_point_array = catmull_rom_chain([(p[0], p[1]) for p in points], num_spline_points)
    z0 = points[0][2]
    width = points[0][3]
    return [(p[0], p[1], z0, width) for p in np_point_array]


Tuple2F = Tuple[float, float]


class ControlNodesGenerator:
    """Generate random roads given the configuration parameters"""

    NUM_INITIAL_SEGMENTS_THRESHOLD = 2
    NUM_UNDO_ATTEMPTS = 20

    def __init__(
        self,
        num_control_nodes: int = 15,
        max_angle: int = None,
        seg_length=None,
        num_spline_nodes: int = None,
        initial_node: Tuple2F = (10.0, 0.0),
    ):
        assert num_control_nodes > 1 and num_spline_nodes > 0
        assert 0 <= max_angle <= 360
        assert seg_length > 0
        assert len(initial_node) == 2
        self.num_control_nodes = num_control_nodes
        self.num_spline_nodes = num_spline_nodes
        self.initial_node = initial_node
        self.max_angle = max_angle
        self.seg_length = seg_length

    def generate_control_nodes(self, num_control_nodes: int = None) -> List[Tuple2F]:
        if not num_control_nodes:
            num_control_nodes = self.num_control_nodes

        nodes = [self._get_initial_control_node(), self.initial_node]

        # +2 is added to reflect the two initial nodes that are necessary for catmull_rom
        while len(nodes) < num_control_nodes + 2:
            nodes.append(self._get_next_node(nodes[-2], nodes[-1], self._get_next_max_angle(len(nodes) - 2)))

        return nodes

    def generate(self, num_control_nodes=None):
        control_nodes = self.generate_key_control_nodes(num_control_nodes)
        return self.control_nodes_to_road(control_nodes)

    def generate_key_control_nodes(self, num_control_nodes):
        # original call to is_valid and loop was removed since the pipeline is in charge of testing that
        control_nodes = self.generate_control_nodes(num_control_nodes=num_control_nodes)
        control_nodes = control_nodes[2:]
        return control_nodes

    def control_nodes_to_road(self, control_nodes):
        nodes = [self.initial_node] + control_nodes
        sample_nodes = catmull_rom_2d(nodes, self.num_spline_nodes)
        road = [(node[0], node[1]) for node in sample_nodes]
        return road

    def _get_initial_point(self) -> geometry.Point:
        return geometry.Point(self.initial_node[0], self.initial_node[1])

    def _get_initial_control_node(self) -> Tuple2F:
        x0, y0 = self.initial_node
        x, y = self._get_next_xy(x0, y0, 270)
        return x, y

    def _get_next_node(self, first_node, second_node: Tuple2F, max_angle) -> Tuple2F:
        v = np.subtract(second_node, first_node)
        start_angle = int(np.degrees(np.arctan2(v[1], v[0])))
        angle = seeded_rng().integers(start_angle - max_angle, start_angle + max_angle + 1)
        x0, y0 = second_node
        return self._get_next_xy(x0, y0, angle)

    def _get_next_xy(self, x0: float, y0: float, angle: float) -> Tuple2F:
        angle_rad = math.radians(angle)
        return x0 + self.seg_length * math.cos(angle_rad), y0 + self.seg_length * math.sin(angle_rad)

    def _get_next_max_angle(self, i: int, threshold=NUM_INITIAL_SEGMENTS_THRESHOLD) -> float:
        if i < threshold or i == self.num_control_nodes - 1:
            return 0
        else:
            return self.max_angle
