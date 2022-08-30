import numpy as np

from . import controller as co
from . import vehicle as ve
from . import waypoint


def go_to_waypoint(vehicle, pid_controller, wp, desired_speed, dt):
    while vehicle.distance_to(wp.transform.location) > desired_speed * dt:
        control = pid_controller.run_step(desired_speed, wp)
        vehicle.iterate(control, dt)


def go_to_waypoints(vehicle, pid_controller, wps, desired_speed, dt):
    for wp in wps:
        go_to_waypoint(vehicle, pid_controller, wp, desired_speed, dt)


def execute_carla_pid_on_bicycle(
    xs,
    ys,
    desired_speed=20,
    dt=0.1,
    pid_gains_lat={"K_P": 0.5, "K_D": 0.01, "K_I": 0.01},
    pid_gains_long={"K_P": 2, "K_D": 0.01, "K_I": 0.01},
):
    """Returns all collected data as a dictionary."""
    pid_gains_lat["dt"] = dt
    pid_gains_long["dt"] = dt

    px0 = xs[0]
    py0 = ys[0]
    psi0 = np.arctan2(ys[1] - ys[0], xs[1] - xs[0])
    v0 = 0

    vehicle = ve.Vehicle(px0, py0, psi0, v0)
    pid_controller = co.VehiclePIDController(vehicle, pid_gains_lat, pid_gains_long)
    waypoints = []
    for i in range(len(xs)):
        waypoints.append(waypoint.Waypoint(xs[i], ys[i]))

    go_to_waypoints(vehicle, pid_controller, waypoints, desired_speed, dt)
    return vehicle.data()
