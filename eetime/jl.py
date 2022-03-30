import json
import glob
import os


def load_jl(fn):
    header = None
    footer = None
    reads = []
    for l in open(fn, "r"):
        j = json.loads(l)
        if j["type"] == "header":
            header = j
            if "sn" in header:
                header["sn"] = header["sn"].upper()
        elif j["type"] == "footer":
            footer = j
        elif j["type"] == "read":
            reads.append(j)
        else:
            assert 0, j["type"]
    return header, footer, reads


def load_jls_arg(args, ignore_bad=True):
    # accept multiple dirs or individual files
    fns = []
    for fn in args:
        if os.path.isdir(fn):
            fns += sorted(list(glob.glob(fn + "/*.jl")))
        else:
            fns += [fn]

    for fn in sorted(fns):
        header, footer, reads = load_jl(fn)
        if not footer:
            continue
        yield fn, header, footer, reads
