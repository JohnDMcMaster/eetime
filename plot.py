#!/usr/bin/env python3

import argparse
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import numpy as np
import scipy.optimize
from scipy.optimize import curve_fit
import json
import glob
import os


def load_jl(fn):
    header = None
    footer = None
    reads = []
    for l in open(fn, "r"):
        j = json.loads(l)
        if j["type"] == "header":
            header = j
        elif j["type"] == "footer":
            footer = j
        elif j["type"] == "read":
            reads.append(j)
        else:
            assert 0, j["type"]
    return header, footer, reads


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


def linear_regression(x, y):
    """
    Quick estimate of sigmoid center
    Drop everything not in middle 80%
    """
    xnew = []
    ynew = []
    for ax, ay in zip(x, y):
        if ay >= 20 and ay <= 80:
            xnew.append(ax)
            ynew.append(ay)

    # m, c = np.linalg.lstsq(xnew, ynew, rcond=None)[0]
    xnew = np.asarray(xnew)
    ynew = np.asarray(ynew)
    reg = LinearRegression().fit(xnew.reshape(-1, 1), ynew)
    m = reg.coef_[0]
    c = reg.intercept_
    print("%0.3f x + %0.3f" % (m, c))
    thalf = (50 - c) / m
    print("thalf: %0.1f" % thalf)


def main():
    parser = argparse.ArgumentParser(description='Help')
    parser.add_argument('--save', default=None)
    parser.add_argument('jls', nargs="+", help='')
    args = parser.parse_args()

    plt.xlabel("t (sec)")
    plt.ylabel("% erased")

    if os.path.isdir(args.jls[0]):
        fns = glob.glob(args.jls[0] + "/*.jl")
    else:
        fns = args.jls

    for jli, jl in enumerate(sorted(fns)):
        print("")
        print(jl)
        header, _footer, reads = load_jl(jl)
        plt.title(header["prog_dev"])
        times, percentages = decode(reads)
        #half_est = sigmoid_regression(times, percentages)
        # half_est = sigmoid_regression2(times, percentages)
        half_est = linear_regression(times, percentages)

        plt.plot(times, percentages, label=str(jli))

    plt.legend()

    if args.save:
        plt.savefig(args.save)
    else:
        plt.show()


if __name__ == "__main__":
    main()
