#!/usr/bin/env python3
"""
TODO:
-Sort csv in some way?
    vendor, model?
    latest?
"""

import argparse
stats = None
import os
import glob


def find_jl_dirs(root_dir):
    if os.path.isdir(root_dir) and glob.glob(root_dir + "/*.jl"):
        yield root_dir

    # yield "prod/prod/2022-03-23_04_pe140t-2/2022-03-23_01_ee17/"
    for f in os.listdir(root_dir):
        d = os.path.join(root_dir, f)
        # A subdir with .jl files?
        if os.path.isdir(d):
            if glob.glob(d + "/*.jl"):
                yield d
            for d2 in find_jl_dirs(d):
                yield d2


def write_header(f):
    l = "dir"
    l += ",sn"
    l += ",vendor,device"
    l += ",prog,prog_dev"
    l += ",eraser,bulb"
    l += ",t50,t100"
    l += ",N"
    f.write(l + "\n")
    f.flush()


def write_row(f, d, vendor, device, statj):
    h = statj["header"]
    l = "%s" % d
    l += ",%s" % (h["sn"])
    l += ",%s,%s" % (vendor, device)
    l += ",%s,%s" % (h["prog"], h["prog_dev"])
    l += ",%s,%s" % (h["eraser"], h["bulb"])
    l += ",%0.1f,%0.1f" % (statj["t50"], statj["t100"])
    l += ",%s" % (statj["n"])
    f.write(l + "\n")
    f.flush()


def load_sns(fn):
    "sn to (vendor, model)"
    # FIXME
    ret = {}
    return ret

    f = open(fn, "r")
    _header = f.read()
    for l in f:
        l = l.strip()
        sn, vendor, model = l.split(",")
        ret[sn] = (vendor, model)
    return ret


def run(root_dir, csv_fn, sns_fn=None, strict=False):
    global stats

    sns = load_sns(sns_fn)

    f = open(csv_fn, "w")
    write_header(f)

    # takes a long time to import
    if stats is None:
        import stats

    processed = 0
    tries = 0
    for d in find_jl_dirs(root_dir):
        tries += 1
        try:
            statj = stats.run(d=d)
            if statj["n"] == 0:
                print("WARNING: skipping bad dir %s" % d)
                if strict:
                    raise Exception("strict")
                continue
            sn = statj["header"]["sn"]
            if sn not in sns:
                print("WARNING: failed to find sn: %s" % sn)
                if strict:
                    raise Exception("strict")
                vendor = ""
                device = ""
            else:
                vendor, device = sns[sn]
            write_row(f, d, vendor, device, statj)
            processed += 1
        except Exception as e:
            if strict:
                raise
            print(e)

    print("")
    print("")
    print("")
    f.close()
    print("Wrote %u / %u entries to %s" % (processed, tries, csv_fn))


def main():
    parser = argparse.ArgumentParser(
        description="Generate a .csv w/ high level stats")
    parser.add_argument('--sns', default="prod/sns.csv", help='S/N .csv in')
    parser.add_argument('root_dir',
                        default="prod/prod",
                        nargs="?",
                        help='Directory to look around in')
    parser.add_argument('csv',
                        default="prod/out.csv",
                        nargs="?",
                        help='.csv out')
    args = parser.parse_args()

    run(root_dir=args.root_dir, csv_fn=args.csv)


if __name__ == "__main__":
    main()
