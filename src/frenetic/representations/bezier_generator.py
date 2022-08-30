from frenetic.utils.catmull import ControlNodesGenerator
from frenetic.representations.abstract_generator import RoadGenerator
import numpy as np
import bezier


def points_to_deltas(control_points):
    x1, y1 = 0, 0
    res = []
    for x, y in control_points:
        res.append((x - x1, y - y1))
        x1 = x
        y1 = y
    return res


class BezierGenerator(RoadGenerator):
    def __init__(self, control_nodes: int, variation: int = 0, max_angle=35, interpolation_nodes=20, seg_length=10):
        self.generator = ControlNodesGenerator(
            num_control_nodes=control_nodes, max_angle=max_angle, seg_length=seg_length, num_spline_nodes=interpolation_nodes
        )

        self.interpolation_nodes = interpolation_nodes

        super().__init__(length=control_nodes, variation=variation)

    def generate(self):
        control_nodes = self.generator.generate_key_control_nodes(self.get_length())
        deltas_control_nodes = points_to_deltas(control_nodes)
        return deltas_control_nodes

    def to_cartesian(self, test):
        delta_xs, delta_ys = zip(*test)
        xs = np.cumsum(list(delta_xs))
        ys = np.cumsum(list(delta_ys))

        nodes = np.asfortranarray([xs, ys])

        # generate curve
        curve = bezier.Curve.from_nodes(nodes)

        # to cartesian
        cartesian = curve.evaluate_multi(np.linspace(0, 1.0, len(xs) * self.interpolation_nodes))
        road = list(zip(cartesian[0], cartesian[1]))

        return road

    def get_value(self, previous):
        raise Exception("This generator does not implement get value.")
