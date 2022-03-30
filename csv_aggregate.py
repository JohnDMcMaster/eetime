#!/usr/bin/env python3

import argparse
import os
import statistics
import math


def write_header(f):
    l = "Vendor,Device"
    l += ",T50 (sec),T100 (sec)"
    l += ",N,S/Ns"
    f.write(l + "\n")
    f.flush()


def write_row(f, vendor, device, t50, t100, n, sns):
    l = "%s,%s" % (vendor, device)
    l += ",%0.1f,%0.1f" % (t50, t100)
    l += ",%u,%s" % (n, ', '.join(sns))
    f.write(l + "\n")
    f.flush()


def load_csv_as_j(fn):
    f = open(fn, "r")
    header = f.readline()
    fields = header.split(",")
    for l in f:
        l = l.strip()
        j = {}
        for k, v in zip(fields, l.split(",")):
            k = k.strip()
            v = v.strip()
            if k in ("t50_norm", "t100_norm"):
                v = float(v)
            j[k] = v
        yield j


# statistics.median
def rms(l):
    squared = sum([x**2 for x in l])
    return (squared / len(l))**0.5


def run(csv_in, csv_out):
    global stats

    f = open(csv_out, "w")
    write_header(f)

    # key as (vendor, device)
    products = {}

    for rowj in load_csv_as_j(csv_in):
        rows = products.setdefault((rowj["vendor"], rowj["device"]), [])
        rows.append(rowj)

    print("Found %u products" % len(products))

    for (entryk, rows) in sorted(products.items()):
        (vendor, device) = entryk
        sns = sorted([row["sn"] for row in rows])
        # Drop 0 (invalid) entries
        t50s = sorted([row["t50_norm"] for row in rows if row["t50_norm"]])
        t100s = sorted([row["t100_norm"] for row in rows if row["t100_norm"]])
        # maybe RMS or median?
        if t50s:
            t50 = rms(t50s)
        else:
            t50 = 0.0
        if t100s:
            t100 = rms(t100s)
        else:
            t100 = 0.0
        n = max(len(t50s), len(t100s))
        write_row(f, vendor, device, t50, t100, n, sns)

    f.close()
    print("Wrote %s" % csv_out)


def main():
    parser = argparse.ArgumentParser(description="")
    parser.add_argument('csv_in',
                        default="prod/out.csv",
                        nargs="?",
                        help='.csv in')
    parser.add_argument('csv_out',
                        default="prod/aggregate.csv",
                        nargs="?",
                        help='.csv out')
    args = parser.parse_args()

    run(args.csv_in, args.csv_out)


if __name__ == "__main__":
    main()
