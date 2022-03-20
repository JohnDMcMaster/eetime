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
import eetime.jl


def decode(reads):
    times = []
    percentages = []
    for aread in reads:
        times.append(aread["seconds"])
        percentages.append(aread["erase_percent"])
    return times, percentages


def main():
    parser = argparse.ArgumentParser(description='Help')
    parser.add_argument('--save', default=None)
    parser.add_argument('jls', nargs="+", help='')
    args = parser.parse_args()

    plt.xlabel("t (sec)")
    plt.ylabel("% erased")

    for jli, (fn, header, _footer,
              reads) in enumerate(eetime.jl.load_jls_arg(args.jls)):
        print("")
        print(fn)
        plt.title(header["prog_dev"])
        times, percentages = decode(reads)
        plt.plot(times, percentages, label=str(jli))

    plt.legend()

    if args.save:
        plt.savefig(args.save)
    else:
        plt.show()


if __name__ == "__main__":
    main()
