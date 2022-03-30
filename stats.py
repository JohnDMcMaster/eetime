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

    if len(xs) < 2:
        print("WARNING: interpolation failed (insufficient entries)")
        return 0.0

    for i, (ax, ay) in enumerate(zip(xs, ys)):
        if ay >= thresh:
            break
    else:
        raise Exception("Interpolation failed (failed to hit thresh)")

    if i == 0:
        i = 1

    # on the off chance we land at a stable point bump around
    while True:
        if ys[i - 1] == ys[i]:
            print("WARNING: searching for better 50p point")
            i += 1
        else:
            break

    x0 = xs[i - 1]
    x1 = xs[i]
    y0 = ys[i - 1]
    y1 = ys[i]

    m = (y1 - y0) / (x1 - x0)
    c = y0 - x0 * m
    # c = y1 - x1 * m

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
            if prevt is None:
                return 0.0
            else:
                return prevt
        prevt = t
    return 0.0


def run(jls=None, d=None):
    # TODO: make explicit dir load
    if d:
        jls = [d]

    t100s = []
    t50s = []
    ref_header = None
    ref_footer = None
    for jli, (fn, header, footer,
              reads) in enumerate(eetime.jl.load_jls_arg(jls)):
        print("")
        print(fn)
        if ref_header is None:
            ref_header = header
            ref_footer = footer
        times, percentages = decode(reads)
        print("%u entries" % len(times))
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
    j = {
        "header": ref_header,
        "footer": ref_footer,
        "n": len(t100s),
    }
    if t50s:
        est_t50 = statistics.median(t50s)
        print("  t50: %0.1f sec" % (est_t50))
        j["t50"] = est_t50
    if t100s:
        est_t100 = statistics.median(t100s)
        print("  t100: %0.1f sec" % (est_t100))
        j["t100"] = est_t100

    return j


def main():
    parser = argparse.ArgumentParser(description='Help')
    parser.add_argument('jls', nargs="+", help='')
    args = parser.parse_args()
    run(args.jls)


if __name__ == "__main__":
    main()
