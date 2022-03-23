import datetime
import os
import glob
import sys


def add_bool_arg(parser, yes_arg, default=False, **kwargs):
    dashed = yes_arg.replace('--', '')
    dest = dashed.replace('-', '_')
    parser.add_argument(yes_arg,
                        dest=dest,
                        action='store_true',
                        default=default,
                        **kwargs)
    parser.add_argument('--no-' + dashed,
                        dest=dest,
                        action='store_false',
                        **kwargs)


def parse_size(size_str):
    size = 1
    if 'k' in size_str:
        size *= 1000
    if 'K' in size_str:
        size *= 1024
    size *= int(size_str, 0)
    return size


def default_date_dir(root, prefix, postfix):
    datestr = datetime.datetime.now().isoformat()[0:10]

    if prefix:
        prefix = prefix + '_'
    else:
        prefix = ''

    n = 1
    while True:
        fn = os.path.join(root, '%s%s_%02u' % (prefix, datestr, n))
        if len(glob.glob(fn + '*')) == 0:
            if postfix:
                return fn + '_' + postfix
            else:
                return fn
        n += 1


def tobytes(buff):
    if type(buff) is str:
        #return bytearray(buff, 'ascii')
        return bytearray([ord(c) for c in buff])
    elif type(buff) is bytearray or type(buff) is bytes:
        return buff
    else:
        assert 0, type(buff)


def tostr(buff):
    if type(buff) is str:
        return buff
    elif type(buff) is bytearray or type(buff) is bytes:
        return ''.join([chr(b) for b in buff])
    else:
        assert 0, type(buff)


def hexdump(data,
            label=None,
            indent='',
            address_width=8,
            f=sys.stdout,
            terse=False):
    def isprint(c):
        return c >= ' ' and c <= '~'

    if label:
        print(label)

    bytes_per_half_row = 8
    bytes_per_row = 16
    data = bytearray(data)
    data_len = len(data)

    def hexdump_half_row(start):
        left = max(data_len - start, 0)

        real_data = min(bytes_per_half_row, left)

        f.write(''.join('%02X ' % c for c in data[start:start + real_data]))
        f.write(''.join('   ' * (bytes_per_half_row - real_data)))
        f.write(' ')

        return start + bytes_per_half_row

    pos = 0
    prev_row = None
    dotted = False
    while pos < data_len:
        if terse:
            row = data[pos:pos + bytes_per_row]
            last_row = pos + bytes_per_row >= len(data)
            # Always print the last row
            if not last_row:
                if row == prev_row:
                    if not dotted:
                        f.write("...\n")
                        dotted = True
                    pos += bytes_per_row
                    continue
                prev_row = row

                # Broke a repeat streak
                # Display the previous row to make continuity clear
                if dotted:
                    pos -= bytes_per_row
                    prev_row = None
                dotted = False

        row_start = pos
        f.write(indent)
        if address_width:
            f.write(('%%0%dX  ' % address_width) % pos)
        pos = hexdump_half_row(pos)
        pos = hexdump_half_row(pos)
        f.write("|")
        # Char view
        left = data_len - row_start
        real_data = min(bytes_per_row, left)

        f.write(''.join([
            c if isprint(c) else '.'
            for c in tostr(data[row_start:row_start + real_data])
        ]))
        f.write((" " * (bytes_per_row - real_data)) + "|\n")


def time_str_sec(delta):
    """Print a hh:mm::ss time"""
    fraction = delta % 1
    delta -= fraction
    delta = int(delta)
    seconds = delta % 60
    delta /= 60
    minutes = delta % 60
    delta /= 60
    hours = delta
    return '%02u:%02u:%02u' % (hours, minutes, seconds)


def time_str_ms(delta):
    """Print a hh:mm::ss.fff time"""
    fraction = delta % 1
    delta -= fraction
    delta = int(delta)
    seconds = delta % 60
    delta /= 60
    minutes = delta % 60
    delta /= 60
    hours = delta
    return '%02u:%02u:%02u.%03u' % (hours, minutes, seconds, fraction * 1000)
