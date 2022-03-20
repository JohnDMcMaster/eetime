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
        elif j["type"] == "footer":
            footer = j
        elif j["type"] == "read":
            reads.append(j)
        else:
            assert 0, j["type"]
    return header, footer, reads


def load_jls_arg(args, ignore_bad=True):
    if os.path.isdir(args[0]):
        fns = glob.glob(args[0] + "/*.jl")
    else:
        fns = args

    for fn in sorted(fns):
        header, footer, reads = load_jl(fn)
        if not footer:
            continue
        yield fn, header, footer, reads
