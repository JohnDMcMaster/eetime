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


def str2fw(s):
    return zlib.decompress(binascii.unhexlify(s))


def tnow():
    return datetime.datetime.utcnow().isoformat()


def check_erase(prog):
    read_buf = prog.read()["code"]
    erased, erase_percent = is_erased(read_buf, prog_dev=prog.device)

    signature = hash8(read_buf)
    print("is_erased %u w/ erase_percent % 8.3f%%, sig %s" %
          (erased, erase_percent, signature))


def wait_erased(fout,
                prog,
                erased_threshold=20.,
                interval=3.0,
                prog_time=None,
                passn=0,
                need_passes=0,
                timeout=None,
                test=False,
                verbose=False):
    """
    erased_threshold: stop when this percent contiguous into a successful erase
        Ex: if 99 iterations wasn't fully erased but 100+ was, stop at 120 iterations
    interval: how often, in seconds, to read the device
    """

    tstart = time.time()
    # Last iteration timestamp. Used to "frame lock" reads at set interval
    tlast = None
    # Timestamp when EPROM was first half erased
    dt_50 = None
    dt_100 = None
    iter = 0
    nerased = 0
    while True:
        if tlast is not None:
            while time.time() - tlast < interval:
                time.sleep(0.1)

        tlast = time.time()
        dt_this = tlast - tstart
        iter += 1

        if timeout and dt_this >= timeout:
            j = {
                "type": "timeout",
                'iter': iter,
                'seconds': dt_this,
            }
            fout.write(json.dumps(j) + '\n')
            fout.flush()
            raise Exception("Timed out")

        read_buf = prog.read()["code"]
        erased, erase_percent = is_erased(read_buf, prog_dev=prog.device)
        if erased or test:
            nerased += 1
            if not dt_100:
                dt_100 = tlast - tstart
        else:
            nerased = 0
            dt_100 = None
        # Declare done when we've been erased for some percentage of elapsed time
        complete_percent = 100.0 * nerased / iter
        # Convert to more human friendly 100% scale
        end_check = 100. * complete_percent / erased_threshold

        j = {
            "type": "read",
            'iter': iter,
            'seconds': dt_this,
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
            "pass %u / %u, iter % 3u @ %s: is_erased %u w/ erase_percent % 8.3f%%, sig %s, end_check: %0.1f%%"
            % (
                passn,
                need_passes,
                iter,
                util.time_str_sec(dt_this),
                erased,
                erase_percent,
                signature,
                #
                end_check))
        if dt_50 is None and erase_percent >= 50 or test:
            dt_50 = tlast - tstart
            print("50%% erased after %0.1f sec" % (dt_50, ))
        if end_check >= 100.0 or test:
            break
    dt_120 = tlast - tstart
    print("Erased 100%% after %0.1f sec" % (dt_100, ))
    print("Erased 120%% after %0.1f sec" % (dt_120, ))

    j = {
        "type": "footer",
        "erase_time": dt_100,
        "run_time": dt_120,
        "half_erase_time": dt_50
    }
    if prog_time is not None:
        j["prog_time"] = prog_time
    fout.write(json.dumps(j) + '\n')
    fout.flush()
    return dt_100, dt_50


def run(dout,
        prog_dev,
        erased_threshold=20.,
        interval=3.0,
        passes=1,
        read_init=True,
        write_init=False,
        eraser=None,
        bulb=None,
        user=None,
        sn=None,
        test=False,
        timeout=None,
        verbose=False):
    if passes > 1 and not write_init:
        raise Exception("Must --write-init if > 1 pass")

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
        # 1 based indexing. At least make it match iter
        passn += 1
        fnout = '%s/iter_%02u.jl' % (dout, passn)
        print('')
        print('Writing to %s' % fnout)
        read_init_buf = None
        if read_init:
            print('Reading initial state')
            read_init_buf = prog.read()["code"]

        if write_init:
            print('Writing initial buffer...')
            tstart = time.time()
            prog.write(init_buf, verify=False)
            prog_time = time.time() - tstart
            print('Wrote in %0.1f sec' % prog_time)
        else:
            prog_time = None

        with open(fnout, "w") as fout:
            j = {
                "type": "header",
                "prog": "minipro",
                "prog_dev": prog.device,
                "datetime": tnow(),
                "interval": interval,
                "erased_threshold": erased_threshold,
            }
            if test:
                j['test'] = bool(test)
            if user:
                j['user'] = user
            if sn:
                j['sn'] = sn
            if eraser:
                j['eraser'] = eraser
            if bulb:
                j['bulb'] = bulb
            if read_init_buf:
                j['read'] = fw2str(read_init_buf)
            fout.write(json.dumps(j) + '\n')
            fout.flush()

            wait_erased(fout,
                        prog=prog,
                        erased_threshold=erased_threshold,
                        interval=interval,
                        prog_time=prog_time,
                        passn=passn,
                        need_passes=passes,
                        timeout=timeout,
                        test=test,
                        verbose=verbose)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Collect data on EPROM erasure time")
    parser.add_argument('--device',
                        required=True,
                        help='minipro device. See "minipro -l"')
    parser.add_argument(
        '--passes',
        type=int,
        default=1,
        help='Number of program-erase cycles. Requires --write-init')
    parser.add_argument('--dir', default=None, help='Output directory')
    parser.add_argument('--erased-threshold',
                        type=float,
                        default=20.,
                        help='Erase complete threshold (precent)')
    parser.add_argument('--interval',
                        type=float,
                        default=3.0,
                        help='Erase check interval (seconds)')
    parser.add_argument('--timeout',
                        type=float,
                        default=60 * 60,
                        help='Per pass timeout in seconds')
    parser.add_argument('--eraser',
                        type=str,
                        default=None,
                        help='Eraser metadata')
    parser.add_argument('--bulb', type=str, default=None, help='Bulb metadata')
    parser.add_argument('--user',
                        type=str,
                        default="mcmaster",
                        help='Contributor metadata')
    parser.add_argument('--sn', type=str, default=None, help='S/N metadata')
    parser.add_argument(
        '--postfix',
        default=None,
        help='Use default output dir, but add description postfix')
    util.add_bool_arg(parser,
                      "--read-init",
                      default=True,
                      help="Read device at beginning")
    util.add_bool_arg(parser,
                      "--write-init",
                      default=False,
                      help="Zero device at beginning. Only use on slow erases")
    util.add_bool_arg(parser,
                      "--test",
                      default=False,
                      help="Run full software quickly")
    util.add_bool_arg(parser, "--verbose", default=False)
    args = parser.parse_args()

    log_dir = args.dir
    if log_dir is None:
        postfix = args.postfix
        # keep a descriptive default name
        if postfix is None:
            postfix = "sn-%s_bulb-%s" % (args.sn, args.bulb)
        log_dir = util.default_date_dir("log", "", postfix)

    timeout = args.timeout
    if timeout < 1.0:
        timeout = None

    run(log_dir,
        args.device,
        passes=args.passes,
        erased_threshold=args.erased_threshold,
        interval=args.interval,
        read_init=args.read_init,
        write_init=args.write_init,
        eraser=args.eraser,
        bulb=args.bulb,
        user=args.user,
        sn=args.sn,
        timeout=timeout,
        test=args.test,
        verbose=args.verbose)
