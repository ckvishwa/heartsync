"""Generate the four schematics, run ERC, export netlists and cross-check them.
   python build_sch.py [board ...]"""
import json
import os
import re
import subprocess
import sys

import custom_syms
import designs
import schgen
from kisexp import parse, find, first

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
CLI = r"C:\Program Files\KiCad\10.0\bin\kicad-cli.exe"


def run(args, cwd):
    r = subprocess.run([CLI] + args, cwd=cwd, capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def check_netlist(board_dir, name, js):
    rc, out = run(["sch", "export", "netlist", "--format", "kicadsexpr", "-o", name + ".net", name + ".kicad_sch"],
                  board_dir)
    tree = parse(open(os.path.join(board_dir, name + ".net"), encoding="utf-8").read())
    nets = {}
    for n in find(first(tree, "nets"), "net"):
        nname = first(n, "name")[1].lstrip("/")
        nodes = sorted((first(x, "ref")[1], first(x, "pin")[1]) for x in find(n, "node"))
        if not nname.startswith("unconnected-"):
            nets[nname] = nodes
    want = {k: sorted(tuple(x) for x in v) for k, v in js["nets"].items()}
    # PWR_FLAG pins appear in the KiCad netlist only as #FLG refs: drop them
    got = {k: [x for x in v if not x[0].startswith("#")] for k, v in nets.items()}
    bad = []
    for k, v in want.items():
        if got.get(k) != v:
            bad.append((k, v, got.get(k)))
    extra = [k for k in got if k not in want and got[k]]
    return bad, extra


def main(boards):
    lib = custom_syms.build(os.path.join(ROOT, "lib", "ansonia.kicad_sym"))
    schgen.PRELOAD.update(lib)
    for b in boards:
        d = designs.ALL[b]()
        out = os.path.join(ROOT, b)
        js = schgen.write(d, out)
        rc, txt = run(["sch", "erc", "--severity-all", "--format", "report", "-o", b + "_ERC.rpt",
                       b + ".kicad_sch"], out)
        rpt = open(os.path.join(out, b + "_ERC.rpt"), encoding="utf-8").read()
        m = re.search(r"\*\* ERC messages: (\d+)\s+Errors (\d+)\s+Warnings (\d+)", rpt)
        print("== %s: %d parts, %d nets | ERC %s" % (b, len(js["parts"]), len(js["nets"]),
                                                    m.groups() if m else txt[-300:]))
        bad, extra = check_netlist(out, b, js)
        print("   netlist cross-check: %d mismatched nets, %d extra nets" % (len(bad), len(extra)))
        for k, v, g in bad[:8]:
            print("     ", k, "\n        want", v, "\n        got ", g)
        for k in extra[:8]:
            print("      extra", k)


if __name__ == "__main__":
    main(sys.argv[1:] or list(designs.ALL))
