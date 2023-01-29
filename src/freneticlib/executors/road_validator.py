"""
.. note::
    Note, the code in this module code is an adaptation of the file code_pipeline/validation.py
    as provided by the CPS-Tool-Competition repository.
    https://github.com/sbft-cps-tool-competition/cps-tool-competition

    It has been licensed under the GNU General Public License.
    Thus, this file is also made available under GPL.
"""

# DISCLAIMER:
# Note, this code is an adaptation of the file code_pipeline/validation.py
# as provided by the CPS-Tool-Competition repository.
# https://github.com/sbft-cps-tool-competition/cps-tool-competition
#
from typing import Tuple

import numpy as np
import shapely
from shapely import geometry, BufferCapStyle, BufferJoinStyle

from freneticlib.core.core import TestIndividual
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
    """Finds the smallest curvature radius within the road."""
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

    return mr * 3.280839895


class RoadValidator(object):
    """Performs several checks to assert the road is valid.

    This means that the road has to be inside a square map,
    cannot contain too sharp turns or be self-intersecting, or have a certain minimum length, etc.

    .. note:
        Note, the code in this module code is an adaptation of the file code_pipeline/validation.py
        as provided by the CPS-Tool-Competition repository.
        https://github.com/sbft-cps-tool-competition/cps-tool-competition

        It has been licensed under the GNU General Public License.
        Thus, this file is also made available under GPL.
    """

    def __init__(self, map_size: int = 200, road_min_length: float = 20):
        """
        Args:
            map_size (int): The side length of the map.
            road_min_length (float): The minimum length of the road.
        """
        self.map_size = map_size
        self.road_min_length = road_min_length

    def is_valid(self, test: TestIndividual, executor) -> Tuple[bool, str]:
        """Perform the checks.

            Specifically:
            - road has an acceptable number of points
            - road is not self-intersecting
            - the road polygon is inside the map
            - the road meets the :attr:`self.road_min_length`
            - the road is not too sharp

        Returns:
            (Tuple[bool,str]): A boolean indicating the validity and a string explanation of which check failed

        """

        cartesian = executor.representation.to_cartesian(test)
        original_line = geometry.LineString(np.array(cartesian))
        interpolated_line = geometry_utils.cubic_spline(original_line)

        road_polygon = interpolated_line.buffer(executor.road_width,
                                                cap_style=BufferCapStyle.flat.value,
                                                join_style=BufferJoinStyle.round.value)

        # Not enough or too many points
        if len(test) < 2 or len(test) >= 500:
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
        if self._is_too_sharp(cartesian):
            return False, "Too sharp"

        return True, ""

    def _is_too_sharp(self, the_test, TSHD_RADIUS=47) -> bool:
        """Checks if the road is not too sharp.

        Args:
            the_test: The road (in cartesian coordinates) to be evaluated
            TSHD_RADIUS (float): The maximum acceptable radius.

        Returns:
            (bool): Whether the road sharpness is acceptable.
        """
        return TSHD_RADIUS > min_radius(the_test) > 0.0
