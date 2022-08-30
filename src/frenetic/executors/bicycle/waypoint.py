from . import vec


class WaypointTransform:
    def __init__(self, location):
        self.location = location


class Waypoint:
    def __init__(self, x, y):
        self.transform = WaypointTransform(vec.Vec(x, y))
