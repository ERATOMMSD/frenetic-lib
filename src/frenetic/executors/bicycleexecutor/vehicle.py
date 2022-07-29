import numpy as np
import carla
import vec


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
        return np.sqrt((location.x - self.px)**2 + (location.y - self.py)**2)