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


class Minipro:
    def __init__(self, device=None):
        self.path = os.getenv("MINIPRO", 'minipro')
        self.device = device

    def files(self):
        # if self.verbose:
        if 0:
            return subprocess.STDOUT, subprocess.STDOUT
        else:
            return subprocess.DEVNULL, subprocess.DEVNULL
            #return open(os.devnull, 'wb'), open(os.devnull, 'wb')

    def read(self, device=None, force=False):
        device = device or self.device
        if device is None:
            raise ValueError("Device required")
        tmpfn = '/tmp/uvminipror.bin'
        stdout, stderr = self.files()
        args = [self.path, '-p', device, '-r', tmpfn]
        if force:
            args.append("-y")
        subprocess.check_call(args, stdout=stdout, stderr=stderr)
        code = open(tmpfn, 'rb').read()
        return {"code": code}

    def write(self, code, device=None, force=False):
        device = device or self.device
        if device is None:
            raise ValueError("Device required")
        tmpfn = '/tmp/uvminiprow.bin'
        open(tmpfn, 'wb').write(code)
        args = [self.path, '-p', device, '-w', tmpfn]
        if force:
            args.append("-y")
        subprocess.check_call(args)
