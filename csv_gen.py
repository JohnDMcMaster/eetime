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
            for d2 in find_jl_dirs(d):
                yield d2


def write_header(f):
    l = "dir"
    l += ",sn"
    l += ",vendor,device"
    l += ",prog,prog_dev"
    l += ",eraser,bulb"
    l += ",N"
    l += ",t50_raw,t100_raw"
    l += ",t50_norm,t100_norm"
    f.write(l + "\n")
    f.flush()


def write_row(f, d, vendor, device, statj):
    h = statj["header"]
    l = "%s" % d
    l += ",%s" % (h["sn"])
    l += ",%s,%s" % (vendor, device)
    l += ",%s,%s" % (h["prog"], h["prog_dev"])
    l += ",%s,%s" % (h["eraser"], h["bulb"])
    l += ",%s" % (statj["n"])
    l += ",%0.1f,%0.1f" % (statj["t50"], statj["t100"])
    l += ",%0.1f,%0.1f" % (statj["t50_adj"], statj["t100_adj"])
    f.write(l + "\n")
    f.flush()


def load_sns(fn):
    "sn to (vendor, model)"
    # FIXME
    ret = {}

    f = open(fn, "r")
    _header = f.readline()
    for l in f:
        l = l.strip()
        sn, vendor, model = l.split(",")
        ret[sn] = (vendor, model)
    return ret


def normalize_txx(statj):
    """
    Compute normalized erasure sensitivities

    Baseline is:
    -New USHIO G4T5 bulb
    -Bulb to chip: based on PE-140T EPROM eraser
        Chip at factory tray height
        TODO: calculate distance from bulb


    Bulb 2 vs 3

    ./stats.py prod/log_05_ee2x_bulbs/bulb2/2022-03-23_05_ee20/
        t50: 145.4 sec
        t100: 222.9 sec
    ./stats.py ./prod/log_05_ee2x_bulbs/bulb3/2022-03-24_03_ee20_bulb-3
        t50: 129.5 sec
        t100: 198.5 sec
    ratios
        t50: 0.89
        t100: 0.89

    ./stats.py prod/log_05_ee2x_bulbs/bulb2/2022-03-23_01_ee21
        t50: 137.0 sec
        t100: 192.5 sec
    ./stats.py prod/log_05_ee2x_bulbs/bulb3/2022-03-24_05_ee21_bulb-3
        t50: 125.3 sec
        t100: 175.8 sec
    ratios
        t50: 0.91
        t100: 0.91
    """

    # TODO: move this to a JSON or something
    bulb_scalars = {
        # bulb 1 broke
        # was used for early testing, ignore going forward
        # FIXME
        "1": 1.0,
        # See lec_2022-03-24.txt
        "2": 0.90,
        "3": 1.00,
        "4": 1.00,
    }
    assert "pe140t" in statj["header"]["eraser"]
    bulb = statj["header"]["bulb"]
    assert bulb in bulb_scalars, "Failed to find bulb %s" % bulb
    scalar = bulb_scalars[bulb]

    statj["t50_adj"] = statj["t50"] * scalar
    statj["t100_adj"] = statj["t100"] * scalar


def run(root_dir, csv_fn, sns_fn=None, strict=True):
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
                    raise Exception("skipping bad dir %s" % d)
                continue
            sn = statj["header"]["sn"]
            if sn not in sns:
                print("WARNING: failed to find sn: %s" % sn)
                if strict:
                    raise Exception("failed to find sn: %s" % sn)
                vendor = ""
                device = ""
            else:
                vendor, device = sns[sn]

            normalize_txx(statj)

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

    run(root_dir=args.root_dir, csv_fn=args.csv, sns_fn=args.sns)


if __name__ == "__main__":
    main()
