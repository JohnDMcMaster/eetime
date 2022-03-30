#!/usr/bin/env python3

import argparse
import glob
import json


def mk_header(j, user=None, sn=None, eraser=None, bulb=None):
    if user:
        j['user'] = user
    if sn:
        j['sn'] = sn
    if eraser:
        j['eraser'] = eraser
    if bulb:
        j['bulb'] = bulb
    return json.dumps(j) + '\n'


def process(fn, **kwargs):
    print("Opening %s" % (fn, ))
    out = ""
    f = open(fn, "r")
    orig_header = json.loads(f.readline())
    out += mk_header(orig_header, **kwargs)
    out += f.read()
    f.close()

    with open(fn, "w") as f:
        f.write(out)


def run(d, **kwargs):
    for fn in sorted(glob.glob(d + "/*.jl")):
        process(fn, **kwargs)


def main():
    parser = argparse.ArgumentParser(description="Munge metadata")
    parser.add_argument('--bulb')
    parser.add_argument('--user')
    parser.add_argument('--sn')
    parser.add_argument('--eraser')
    parser.add_argument('dir', help='Directory to annotate')
    args = parser.parse_args()

    run(
        args.dir,
        bulb=args.bulb,
        user=args.user,
        sn=args.sn,
        eraser=args.eraser,
    )


if __name__ == "__main__":
    main()
