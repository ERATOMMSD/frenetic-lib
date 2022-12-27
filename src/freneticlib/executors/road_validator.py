# DISCLAIMER:
# Note, this code is an adaptation of the file code_pipeline/validation.py
# as provided by the CPS-Tool-Competition repository.
# https://github.com/sbft-cps-tool-competition/cps-tool-competition
#
# It has been licensed under the GNU General Public License.
# Thus, this file is also made available under GPL.
from typing import Tuple

import numpy as np
import shapely
from shapely import geometry, BufferCapStyle, BufferJoinStyle
from freneticlib.utils import geometry_utils


def find_circle(p1, p2, p3):
    """
    Returns the center and radius of the circle passing the given 3 points.
    In case the 3 points form a line, returns (None, infinity).
    """
    temp = p2[0] * p2[0] + p2[1] * p2[1]
    bc = (p1[0] * p1[0] + p1[1] * p1[1] - temp) / 2
    cd = (temp - p3[0] * p3[0] - p3[1] * p3[1]) / 2
    det = (p1[0] - p2[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p2[1])

    if abs(det) < 1.0e-6:
        return np.inf

    # Center of circle
    cx = (bc*(p2[1] - p3[1]) - cd*(p1[1] - p2[1])) / det
    cy = ((p1[0] - p2[0]) * cd - (p2[0] - p3[0]) * bc) / det

    radius = np.sqrt((cx - p1[0])**2 + (cy - p1[1])**2)
    return radius


def min_radius(x, w=5):
    mr = np.inf
    nodes = x
    for i in range(len(nodes) - w):
        p1 = nodes[i]
        p2 = nodes[i + int((w-1)/2)]
        p3 = nodes[i + (w-1)]
        radius = find_circle(p1, p2, p3)
        if radius < mr:
            mr = radius
    if mr == np.inf:
        mr = 0

    return mr * 3.280839895  #, mincurv


class RoadValidator(object):

    def __init__(self, executor: "Exectutor"):
        self.executor = executor
        self.map_size = 200
        self.road_min_length = 20

    def is_valid(self, test) -> Tuple[bool,str]:
        cartesian = self.executor.representation.to_cartesian(test)
        original_line = geometry.LineString(np.array(cartesian))
        interpolated_line = geometry_utils.cubic_spline(original_line)

        road_polygon = interpolated_line.buffer(self.executor.road_width,
                                                cap_style=BufferCapStyle.flat.value,
                                                join_style=BufferJoinStyle.round.value)

        # Not enough or too many points
        if len(test) <= 1 or len(test) >= 500:
            return False, "Not enough or too many points"

        # check self-intersection
        if not road_polygon.is_valid:
            return False, "Invalid Road-Polygon"

        # check map-containment
        map_poly = shapely.Polygon([(0, 0), (0, self.map_size), (self.map_size, self.map_size), (self.map_size, 0)])
        if not map_poly.contains(road_polygon):
            return False, "Not in Map"

        # check minimum length of road
        if interpolated_line.length < self.road_min_length:
            return False, "Too short"

        # check road sharpness
        if self.is_too_sharp(cartesian):
            return False, "Too sharp"

        return True, ""

    def is_too_sharp(self, the_test, TSHD_RADIUS=47):
        return TSHD_RADIUS > min_radius(the_test.interpolated_points) > 0.0
