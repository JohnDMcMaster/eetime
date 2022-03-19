#!/usr/bin/env python3

from eetime.minipro import Minipro
from eetime import util
import collect


def run(prog_dev, loop=False, verbose=False):
    prog = Minipro(device=prog_dev, verbose=verbose)

    def check():
        read_buf = prog.read()["code"]
        erased, erase_percent = collect.is_erased(read_buf,
                                                  prog_dev=prog.device)

        print("is_erased %u w/ erase_percent % 8.3f%%" %
              (erased, erase_percent))

    if loop:
        while True:
            check()
    else:
        check()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='Write all bits to 0 of given device')
    parser.add_argument('--device',
                        required=True,
                        help='minipro device. See "minipro -l"')
    util.add_bool_arg(parser, "--verbose", default=False)
    util.add_bool_arg(parser, "--loop", default=False, help="Check forever")
    args = parser.parse_args()

    run(args.device, loop=args.loop, verbose=args.verbose)
