import carlapidonbicycle as cpb
import numpy as np
import numpy.random as ra
import matplotlib.pyplot as pl


def frenet_to_cartesian(x0, y0, theta0, ss, kappas):
    """Trapezoidal integration to compute Cartesian coordinates from given curvature values."""
    xs = np.zeros(len(kappas))
    ys = np.zeros(len(kappas))
    thetas = np.zeros(len(kappas))
    xs[0] = x0
    ys[0] = y0
    thetas[0] = theta0
    for i in range(thetas.shape[0] - 1):
        ss_diff_half = (ss[i + 1] - ss[i]) / 2.0
        thetas[i + 1] = thetas[i] + (kappas[i + 1] + kappas[i]) * ss_diff_half
        xs[i + 1] = xs[i] + (np.cos(thetas[i + 1]) + np.cos(thetas[i])) * ss_diff_half
        ys[i + 1] = ys[i] + (np.sin(thetas[i + 1]) + np.sin(thetas[i])) * ss_diff_half
    return (xs, ys)


def plot(road_length=400, number_of_points=40):
    x0 = 0
    y0 = 0
    theta0 = 0
    n = number_of_points
    ss = np.linspace(0, road_length, n)
    kappas = ra.uniform(-0.1, 0.1, size=ss.shape[0])
    (xs, ys) = frenet_to_cartesian(x0, y0, theta0, ss, kappas)
    data = cpb.execute_carla_pid_on_bicycle(xs, ys)
    pl.figure()
    pl.subplot(221)
    pl.plot(xs, ys, label="Lane center", marker=".", markersize=5)
    pl.plot(data["pxs"], data["pys"], color="C1", label="Vehicle")
    pl.xlabel("$x$")
    pl.ylabel("$y$")
    pl.legend()
    pl.subplot(222)
    pl.plot(data["ts"], data["speed"])
    pl.xlabel("Time (seconds)")
    pl.ylabel("Vehicle speed (m/s)")
    pl.subplot(223)
    pl.plot(data["ts"], data["heading"])
    pl.xlabel("Time (seconds)")
    pl.ylabel("Vehicle heading angle")
    pl.subplot(224)
    pl.plot(data["ts"], data["acceleration"])
    pl.xlabel("Time (seconds)")
    pl.ylabel("Acceleration")
    pl.show()


plot()
