'''
Python bindings for the minipro tool (TL866)
https://github.com/vdudouyt/minipro/
minipro version 0.1     A free and open TL866XX programmer
Usage: minipro [options]
options:
    -l        List all supported devices
    -r <filename>    Read memory
    -w <filename>    Write memory
    -e         Do NOT erase device
    -u         Do NOT disable write-protect
    -P         Do NOT enable write-protect
    -v        Do NOT verify after write
    -p <device>    Specify device (use quotes)
    -c <type>    Specify memory type (optional)
            Possible values: code, data, config
    -i        Use ICSP
    -I        Use ICSP (without enabling Vcc)
    -s        Do NOT error on file size mismatch (only a warning)
    -S        No warning message for file size mismatch (can't combine with -s)
    -y        Do NOT error on ID mismatch
'''

import subprocess
import os
from . import util


class Minipro:
    def __init__(self, device=None, verbose=False):
        self.verbose = verbose
        self.path = os.getenv("MINIPRO", 'minipro')
        self.device = device

    def subprocess(self, args):
        if self.verbose:
            subprocess.check_call(args)
        else:
            subp = subprocess.Popen(args,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT,
                                    shell=False)
            (stdout, _stderr) = subp.communicate()
            if subp.returncode:
                print("")
                print("minipro failed w/ rc %d" % subp.returncode)
                print(util.tostr(stdout))
                raise Exception("minipro failed w/ rc %d" % subp.returncode)

    def read(self, device=None, force=False):
        device = device or self.device
        if device is None:
            raise ValueError("Device required")
        tmpfn = '/tmp/eetime_r.bin'
        args = [self.path, '-p', device, '-r', tmpfn]
        if force:
            args.append("-y")
        self.subprocess(args)
        with open(tmpfn, 'rb') as f:
            code = f.read()
        return {"code": code}

    def write(self, code, device=None, force=False, verify=True):
        device = device or self.device
        if device is None:
            raise ValueError("Device required")
        tmpfn = '/tmp/eetime_w.bin'
        with open(tmpfn, 'wb') as f:
            f.write(code)
        args = [self.path, '-p', device, '-w', tmpfn]
        if not verify:
            args.append("--skip_verify")
        if force:
            args.append("-y")
        self.subprocess(args)
