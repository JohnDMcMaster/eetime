#!/usr/bin/env python3

from eetime.util import tostr
from eetime import util
from eetime.minipro import Minipro

import json
import datetime
import time
import zlib
import binascii
import hashlib
import os


def popcount(x):
    return bin(x).count("1")


def is_erased(fw, prog_dev):
    # for now assume all 1's is erased
    # on some devices like PIC this isn't true due to file 0 padding
    set_bits = sum([popcount(x) for x in bytearray(fw)])
    possible_bits = len(fw) * 8
    percent = 100.0 * set_bits / possible_bits
    return set_bits == possible_bits, percent


def hash8(buf):
    """Quick hash to visually indicator to user if data is still changing"""
    return tostr(binascii.hexlify(hashlib.md5(buf).digest())[0:8])


def fw2str(fw):
    return tostr(binascii.hexlify(zlib.compress(fw)))


def tnow():
    return datetime.datetime.utcnow().isoformat()


def wait_erased(fnout,
                prog,
                erased_threshold=20.,
                interval=3.0,
                prog_time=None,
                verbose=False):
    """
    erased_threshold: stop when this percent contiguous into a successful erase
        Ex: if 99 iterations wasn't fully erased but 100+ was, stop at 120 iterations
    interval: how often, in seconds, to read the device
    """

    with open(fnout, "w") as fout:
        j = {
            "type": "header",
            "prog": "minipro",
            "prog_dev": prog.device,
            "datetime": tnow(),
            "interval": interval,
            "erased_threshold": erased_threshold
        }
        fout.write(json.dumps(j) + '\n')
        fout.flush()

        tstart = time.time()
        # Last iteration timestamp. Used to "frame lock" reads at set interval
        tlast = None
        # Timestamp when EPROM was first half erased
        thalf = None
        passn = 0
        nerased = 0
        while True:
            if tlast is not None:
                while time.time() - tlast < interval:
                    time.sleep(0.1)

            tlast = time.time()
            now = tnow()
            passn += 1
            read_buf = prog.read()["code"]
            erased, erase_percent = is_erased(read_buf, prog_dev=prog.device)
            if erased:
                nerased += 1
            else:
                nerased = 0
            # Declare done when we've been erased for some percentage of elapsed time
            complete_percent = 100.0 * nerased / passn
            # Convert to more human friendly 100% scale
            end_check = 100. * complete_percent / erased_threshold

            j = {
                'iter': passn,
                'datetime': now,
                'read': fw2str(read_buf),
                'read_meta': "zlib",
                'complete_percent': complete_percent,
                'erase_percent': erase_percent,
                'erased': erased
            }
            fout.write(json.dumps(j) + '\n')
            fout.flush()

            signature = hash8(read_buf)
            print(
                "%s iter % 3u: is_erased %u w/ erase_percent % 8.3f%%, sig %s, end_check: %0.1f%%"
                % (
                    now,
                    passn,
                    erased,
                    erase_percent,
                    signature,
                    #
                    end_check))
            if thalf is None and erase_percent >= 50:
                thalf = tlast
                dt_half = thalf - tstart
                print("50%% erased after %0.1f sec" % (dt_half, ))
            if end_check >= 100.0:
                break
        dt = tlast - tstart
        print("Erased after %0.1f sec" % (dt, ))

        j = {"type": "footer", "erase_time": dt, "half_erase_time": dt_half}
        if prog_time is not None:
            j["prog_time"] = prog_time
        fout.write(json.dumps(j) + '\n')
        fout.flush()
    return dt, dt_half


def run(dout,
        prog_dev,
        erased_threshold=20.,
        interval=3.0,
        passes=10,
        write_init=True,
        verbose=False):
    if not os.path.exists(dout):
        os.makedirs(dout, exist_ok=True)

    print("")
    prog = Minipro(device=prog_dev, verbose=verbose)
    print("Checking programmer...")
    size = len(prog.read()["code"])
    print("Device is %u bytes" % size)
    # Write 0's at the beginning of every pass
    init_buf = bytearray(size)

    for passn in range(passes):
        fnout = '%s/iter_%02u.jl' % (dout, passn)
        print('')
        print('Writing to %s' % fnout)
        if write_init:
            print('Writing initial buffer...')
            tstart = time.time()
            prog.write(init_buf)
            prog_time = time.time() - tstart
            print('Wrote in %0.1f sec' % prog_time)
        else:
            prog_time = None
        wait_erased(fnout,
                    prog=prog,
                    erased_threshold=erased_threshold,
                    interval=interval,
                    prog_time=prog_time,
                    verbose=verbose)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Collect data on EPROM erasure time")
    parser.add_argument('--device',
                        required=True,
                        help='minipro device. See "minipro -l"')
    parser.add_argument('--passes',
                        type=int,
                        default=10,
                        help='Number of program-erase cycles')
    parser.add_argument('--dir', default=None, help='Output directory')
    parser.add_argument('--erased-threshold',
                        type=float,
                        default=20.,
                        help='Erase complete threshold (precent)')
    parser.add_argument('--interval',
                        type=float,
                        default=3.0,
                        help='Erase check interval (seconds)')
    parser.add_argument(
        '--postfix',
        default="",
        help='Use default output dir, but add description postfix')
    util.add_bool_arg(parser,
                      "--write-init",
                      default=True,
                      help="For debugging")
    util.add_bool_arg(parser, "--verbose", default=False)
    args = parser.parse_args()

    log_dir = args.dir
    if log_dir is None:
        log_dir = util.default_date_dir("log", "", args.postfix)

    run(log_dir,
        args.device,
        passes=args.passes,
        erased_threshold=args.erased_threshold,
        interval=args.interval,
        write_init=args.write_init,
        verbose=args.verbose)
