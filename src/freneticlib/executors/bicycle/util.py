class Vec:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def update(self, x, y):
        self.x = x
        self.y = y


class WaypointTransform:
    def __init__(self, location):
        self.location = location


class Waypoint:
    def __init__(self, x, y):
        self.transform = WaypointTransform(Vec(x, y))
