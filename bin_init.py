#!/usr/bin/env python3

"""
Did you put something important into the test fixture?
Just a hopeless data hoarder?
We might have saved it
"""

import argparse
import eetime.jl
from eetime import util
import glob
import os
import binascii
import collect


def main():
    parser = argparse.ArgumentParser(description='Display and write the initial ROM read')
    util.add_bool_arg(parser,
                      "--hexdump",
                      default=False,
                      help="Hexdump instead of writing")
    parser.add_argument('jl', help='.jl to extract (or first file if dir)')
    parser.add_argument('out',
                        nargs="?",
                        default="out.bin",
                        help='Output binary')
    args = parser.parse_args()

    fn = args.jl
    if os.path.isdir(fn):
        fn = sorted(list(glob.glob(fn + "/*.jl")))[0]

    print("Opening %s" % (fn, ))
    header, _footer, _reads = eetime.jl.load_jl(fn)
    if not "read" in header:
        raise Exception(".jl doesn't support initial read")
    buf = collect.str2fw(header["read"])
    if args.hexdump:
        util.hexdump(buf, terse=True)


if __name__ == "__main__":
    main()
