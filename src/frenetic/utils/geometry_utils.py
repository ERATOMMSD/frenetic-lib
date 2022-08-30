import numpy as np

from shapely import geometry as geom
from scipy import interpolate


def cubic_spline(line: geom.LineString, node_distance: float = 1, smoothness: int = 0, rounding_precision: int = 3, k=3, min_num_nodes: int = 20):
    # This is an approximation based on whatever input is given
    pos_tck, pos_u = interpolate.splprep(line.xy, s=smoothness, k=k)

    try:
        num_nodes = max(int(line.length / node_distance), min_num_nodes)
    except:
        breakpoint()
        pass
    step_size = 1 / num_nodes
    unew = np.arange(0, 1 + step_size, step_size)

    new_x_vals, new_y_vals = interpolate.splev(unew, pos_tck)
    return geom.LineString(zip(np.round(new_x_vals, rounding_precision), np.round(new_y_vals, rounding_precision)))
