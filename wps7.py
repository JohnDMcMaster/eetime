#!/usr/bin/env python3

import io
from io import BytesIO
import os
import pycurl
import time

import warnings
# ./wps7.py:53: DeprecationWarning: PY_SSIZE_T_CLEAN will be required for '#' formats
# c.perform()
warnings.filterwarnings("ignore", category=DeprecationWarning)


class WPS7Exception(Exception):
    pass


class WPS7:
    def __init__(self, host=None, user=None, pass_=None):
        # WPS7 defaults
        self.host = host or os.getenv('WPS7_HOST', '192.168.0.1')
        self.user = user or os.getenv('WPS7_USER', 'admin')
        self.pass_ = pass_ or os.getenv('WPS7_PASS', '1234')
        self.verbose = 0

    def on(self, n):
        self.sw(n, True)

    def off(self, n):
        self.sw(n, False)

    def cycle(self, n, t=1.0):
        try:
            l = list(n)
        except TypeError:
            l = [n]

        for n in l:
            self.sw(n, False)
        time.sleep(t)
        for n in l:
            self.sw(n, True)

    def sw(self, n, on):
        state = 'ON' if on else 'OFF'
        if n < 1 or n > 8:
            raise ValueError("require 1 <= sw %d <= 8" % n)

        c = pycurl.Curl()
        url = 'http://%s/outlet?%d=%s' % (self.host, n, state)
        if self.verbose:
            print('WPS: %s' % url)
            print('  u: %s' % self.user)
            print('  p: %s' % self.pass_)
        c.setopt(c.URL, url)
        fout = io.BytesIO()
        c.setopt(c.WRITEDATA, fout)
        c.setopt(pycurl.USERPWD, '%s:%s' % (self.user, self.pass_))
        c.perform()
        c.close()

        response = fout.getvalue()
        if b'Login Incorrect' not in response and b'<META HTTP-EQUIV="refresh" content="0; URL=/index.htm">' in response:
            return
        if self.verbose:
            print(response)
        raise WPS7Exception("bad response to %s" % (url, ))


def main():
    import argparse

    parser = argparse.ArgumentParser(description="")
    parser.add_argument("--host", help="")
    parser.add_argument("--user", help="")
    parser.add_argument("--password", help="")
    parser.add_argument("--switch", type=int, required=True, help="")
    parser.add_argument("--on", action="store_true", help="")
    parser.add_argument("--off", action="store_true", help="")
    args = parser.parse_args()

    w = WPS7(host=args.host, user=args.user, pass_=args.password)
    switch = args.switch
    if switch < 1 or switch > 8:
        raise ValueError("require 1 <= switch %d <= 8" % switch)
    if args.on:
        w.on(switch)
    if args.off:
        w.off(switch)


if __name__ == "__main__":
    main()
