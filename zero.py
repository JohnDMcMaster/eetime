#!/usr/bin/env python3

from eetime.minipro import Minipro
from eetime import util


def run(prog_dev, verbose=False):
    prog = Minipro(device=prog_dev, verbose=verbose)
    print("Checking programmer...")
    size = len(prog.read()["code"])
    print("Device is %u bytes" % size)
    # Write 0's at the beginning of every pass
    prog.write(bytearray(size))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='Write all bits to 0 of given device')
    parser.add_argument('--device',
                        required=True,
                        help='minipro device. See "minipro -l"')
    util.add_bool_arg(parser, "--verbose", default=False)
    args = parser.parse_args()

    run(args.device, verbose=args.verbose)
