import numpy as np
import carla
import vec


def pinegpi(val):
    new_val = val % (2 * np.pi)
    if new_val > np.pi:
        new_val -= 2 * np.pi
    return new_val


class VehicleTransform:
    def __init__(self, location):
        self.location = location
        self.forward_vector = vec.Vec(0, 0)

    def update(self, x, y, psi):
        self.location.update(x, y)
        self.set_forward_vector(psi)

    def set_forward_vector(self, psi):
        self.forward_vector.update(np.cos(psi), np.sin(psi))

    def get_forward_vector(self):
        return self.forward_vector


class Vehicle:
    def __init__(self, px0, py0, psi0, v0):
        self.px = px0
        self.py = py0
        self.psi = psi0
        self.v = v0
        self.accel = 0
        self.t = 0
        self.pxs = []
        self.pys = []
        self.psis = []
        self.vs = []
        self.accels = []
        self.controls = []
        self.ts = []

        self.speed = self.v
        self.transform = VehicleTransform(vec.Vec(self.px, self.py))
        self.transform.set_forward_vector(self.psi)
        self.control = carla.VehicleControl()

        pass

    def record(self):
        self.pxs.append(self.px)
        self.pys.append(self.py)
        self.psis.append(self.psi)
        self.vs.append(self.v)
        self.accels.append(self.accel)
        self.controls.append(self.control)
        self.ts.append(self.t)

    def get_transform(self):
        return self.transform

    def get_world(self):
        return None

    def get_control(self):
        return self.control

    def get_speed(self):
        return self.speed

    def iterate(self, control, dt):
        self.control = control
        accel = control.throttle
        if control.brake > 0:
            accel = -control.brake
        self.accel = accel

        self.record()
        beta = control.steer
        self.px += dt * self.v * np.cos(self.psi + beta)
        self.py += dt * self.v * np.sin(self.psi + beta)
        self.psi += dt * self.v * np.sin(beta)

        # TODO: check this part
        self.psi %= 2 * np.pi
        if self.psi > np.pi:
            self.psi -= 2 * np.pi

        self.v += dt * accel
        self.t += dt
        self.speed = self.v
        self.transform.update(self.px, self.py, self.psi)

    def distance_to(self, location):
        return np.sqrt((location.x - self.px) ** 2 + (location.y - self.py) ** 2)

    def data(self):
        """ Returns a dictionary of all collected data across time."""
        accels = np.array(self.accels)
        dt = self.ts[1] - self.ts[0]
        jerks = (accels[1:] - accels[:-1]) / dt  # along longitudinal
        jerks_sq = jerks * jerks
        costs = dt * np.cumsum(jerks_sq)

        heading = np.array(self.psis)
        heading_diffs = np.vectorize(pinegpi)(heading[1:] - heading[:-1])

        # lateral with respect to heading of previous time instant
        lat_accels = np.cos(heading_diffs) * accels[1:]
        lat_jerks = (lat_accels[1:] - lat_accels[:-1]) / dt
        lat_jerks_sq = lat_jerks * lat_jerks
        lat_costs = dt * np.cumsum(lat_jerks_sq)

        return {'ts': np.array(self.ts),  # sampling time instants where data is collected
                'short_ts': np.array(self.ts[:-1]),  # time instants where jerks and costs are collected
                'short_short_ts': np.array(self.ts[:-1]),  # time instants where lat_jerks and lat_costs are collected
                'pxs': np.array(self.pxs),
                'pys': np.array(self.pys),
                'speed': np.array(self.vs),
                'acceleration': accels,
                'jerk': jerks,
                'jerk_squared': jerks_sq,
                'cost': costs,
                'lat_acceleration': lat_accels,
                'lat_jerk': lat_jerks,
                'lat_jerk_squared': lat_jerks_sq,
                'lat_cost': lat_costs,
                'heading': heading,
                'heading_diffs': heading_diffs,
                'steering_control': np.array([control.steer for control in self.controls]),
                'throttle_control': np.array([control.throttle for control in self.controls]),
                'brake_control': np.array([control.throttle for control in self.controls]),
                }
