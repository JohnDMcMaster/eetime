#!/usr/bin/env python3

import argparse
from sklearn.linear_model import LinearRegression
import numpy as np
import scipy.optimize
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
import eetime.jl
import statistics


def decode(reads):
    times = []
    percentages = []
    for aread in reads:
        times.append(aread["seconds"])
        percentages.append(aread["erase_percent"])
    return times, percentages


def sigmoid(p, x):
    x0, y0, c, k = p
    y = c / (1 + np.exp(-k * (x - x0))) + y0
    return y


def residuals(p, x, y):
    return y - sigmoid(p, x)


def resize(arr, lower=0.0, upper=1.0):
    arr = arr.copy()
    if lower > upper: lower, upper = upper, lower
    arr -= arr.min()
    arr *= (upper - lower) / arr.max()
    arr += lower
    return arr


def sigmoid_regression(x, y):

    xnp = np.asarray(x)
    ynp = np.asarray(y)

    xnp = resize(-xnp, lower=0.3)
    ynp = resize(ynp, lower=0.3)
    p_guess = (np.median(xnp), np.median(ynp), 1.0, 1.0)
    p, cov, infodict, mesg, ier = scipy.optimize.leastsq(residuals,
                                                         p_guess,
                                                         args=(xnp, ynp),
                                                         full_output=1)

    x0, y0, c, k = p
    print('''\
x0 = {x0}
y0 = {y0}
c = {c}
k = {k}'''.format(x0=x0, y0=y0, c=c, k=k))
    print("x0 estimate: %u" % x[int(x0 * len(x))])
    print("c estimate: %u" % x[int(c * len(x))])


def sigmoid_regression2(x, y):
    xnp = np.asarray(x)
    ynp = np.asarray(y)

    def sigmoid(x, k, x0):
        return 1.0 / (1 + np.exp(-k * (x - x0)))

    print("")
    popt, pcov = curve_fit(sigmoid, xnp, ynp)
    estimated_k, estimated_x0 = popt
    print(xnp)
    print(ynp)


def linear_regression(xs, ys):
    """
    Quick estimate of sigmoid center
    Drop everything not in middle 80%
    """
    xfilt = []
    yfilt = []
    for ax, ay in zip(xs, ys):
        if ay >= 30 and ay <= 70:
            xfilt.append(ax)
            yfilt.append(ay)

    # m, c = np.linalg.lstsq(xfilt, yfilt, rcond=None)[0]
    xfilt = np.asarray(xfilt)
    yfilt = np.asarray(yfilt)
    reg = LinearRegression().fit(xfilt.reshape(-1, 1), yfilt)
    m = reg.coef_[0]
    c = reg.intercept_
    print("%0.3f x + %0.3f" % (m, c))
    print("Regression test")
    for ax, ay in zip(xfilt, yfilt):
        est = m * ax + c
        print("  t=%u => %0.1f%%, est %0.1f%%" % (ax, ay, est))
    thalf = (50 - c) / m
    print("thalf: %0.1f" % thalf)
    return thalf


def poly_regression(xs, ys):
    xfilt = []
    yfilt = []
    for ax, ay in zip(xs, ys):
        if ay >= 5 and ay <= 95:
            xfilt.append(ax)
            yfilt.append(ay)

    # sigmoid should be third order
    cs = np.poly1d(np.polyfit(xfilt, yfilt, 3))
    print(cs)
    print(list(cs))

    print("Regression test")
    c3, c2, c1, c0 = cs
    for ax, ay in zip(xfilt, yfilt):
        est = c3 * ax * ax * ax + c2 * ax * ax + c1 * ax + c0
        print("  t=%u => %0.1f%%, est %0.1f%%" % (ax, ay, est))


def lin_interp_50p(xs, ys, thresh=50.0):
    """
    Linear interpolation to find the 50% erase mark
    In practice sets increase pretty rapidly around 50% so this should be reliable
    """

    for i, (ax, ay) in enumerate(zip(xs, ys)):
        if ay >= thresh:
            break
    else:
        raise Exception("Interpolation failed")

    x0 = xs[i - 1]
    x1 = xs[i]
    y0 = ys[i - 1]
    y1 = ys[i]

    cs = np.poly1d(np.polyfit([x0, x1], [y0, y1], 1))
    m, c = cs
    thalf = (50 - c) / m
    print("thalf: %0.1f" % thalf)
    print("  x=%u => y=%0.1f" % (x0, y0))
    print("  x=%u => y=%0.1f" % (x1, y1))
    return thalf


def find_t100(ts, ps):
    prevt = None
    # Move backwards until we find first entry not 100%
    # then report the last entry, which was the first stable 100%
    for t, p in zip(reversed(ts), reversed(ps)):
        if prevt is None:
            assert p == 100.0
        if p < 100.0:
            return prevt
        prevt = t


def main():
    parser = argparse.ArgumentParser(description='Help')
    parser.add_argument('jls', nargs="+", help='')
    args = parser.parse_args()

    t100s = []
    t50s = []
    for jli, (fn, header, _footer,
              reads) in enumerate(eetime.jl.load_jls_arg(args.jls)):
        print("")
        print(fn)
        times, percentages = decode(reads)
        t50s.append(lin_interp_50p(times, percentages))
        t100s.append(find_t100(times, percentages))

    print("")
    print("t50s")
    for t50 in t50s:
        print("  %0.1f" % t50)
    if 0:
        plt.plot(t50s)
        plt.show()

    print("")
    print("t100s")
    for t100 in t100s:
        print("  %0.1f" % t100)
    if 0:
        plt.plot(t100s)
        plt.show()

    print("")
    print("Summary:")
    print("  t50: %0.1f sec" % (statistics.median(t50s)))
    print("  t100: %0.1f sec" % (statistics.median(t100s)))


if __name__ == "__main__":
    main()
