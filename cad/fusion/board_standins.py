"""Stand-in boxes for board parts that have no KiCad 3D model (run with KiCad's python, pcbnew).
Writes cad/boards/standins.json (+ connectors.json: courtyards of the cable connectors): [{board, ref, side, x0, y0, x1, y1, h, note}] in DEVICE mm
(origin = KiCad (100, 100), +Y up). Outline = the footprint courtyard (else the pad box); height from the datasheet.
Usage: "C:/Program Files/KiCad/10.0/bin/python.exe" board_standins.py <dir with carrier/power/front_sensor .kicad_pcb>"""
import json, os, sys
import pcbnew

# ref -> (height mm, source). Parts listed here get a box even if the STEP carries a model of its own name.
H = {
    "carrier": {"U1": (1.0, "TI DRC0010J 3x3x1.0"), "U7": (2.4, "SIMCom SIM7080G 17.6x15.7x2.3 (+0.1 paste)"),
                "J14": (1.4, "GCT SIM8060 nano-SIM, 1.35 high"), "J1": (2.95, "JST SM22B-SRSS-TB, SH side entry 2.9 high"),
                "U10": (2.5, "Ebyte EWM104-BT5125: height not in the manual I have, 2.5 assumed (verify)")},
    "power": {"U2": (1.0, "TI VQFN-RHL-20 1.0"), "U7": (1.0, "TI VQFN-RHL-20 1.0"), "U3": (1.2, "TI HTSSOP-28 PWP 1.2"),
              "L1": (3.0, "Bourns SRP7028A 2.8 typ / 3.0 max"), "L2": (3.0, "Bourns SRP7028A 3.0 max"), "L3": (3.0, "Bourns SRP7028A 3.0 max"),
              "J7": (6.0, "JST S2B-PH-SM4-TB, 6.0 high (verify)"), "J1": (2.95, "JST SM22B/24B-SRSS-TB 2.9 high"),
              "J4": (6.5, "Amass MR30PW-M body, 6.5 high read off the drawing (verify)")},
    "front_sensor": {"U2": (1.35, "Broadcom APDS-9960 3.94x2.36x1.35")},
}

CONN = {"carrier": ("J1", "J4", "J6", "J7", "J8", "J9", "J11", "J12", "J13"), "power": ("J1", "J5", "J6", "J7")}


def bbox_dev(fp, side):
    cy = fp.GetCourtyard(pcbnew.B_CrtYd if side == "B" else pcbnew.F_CrtYd)
    if cy.OutlineCount():
        bb = cy.BBox()
    else:
        bb = pcbnew.BOX2I()
        for p in fp.Pads():
            bb.Merge(p.GetBoundingBox())
    to = pcbnew.ToMM
    return to(bb.GetLeft()) - 100, 100 - to(bb.GetBottom()), to(bb.GetRight()) - 100, 100 - to(bb.GetTop())


def main(d):
    out, conns = [], []
    for board, refs in H.items():
        b = pcbnew.LoadBoard(os.path.join(d, board + ".kicad_pcb"))
        for fp in b.GetFootprints():
            ref = fp.GetReference()
            if ref in CONN.get(board, ()):
                x0, y0, x1, y1 = bbox_dev(fp, "B" if fp.IsFlipped() else "F")
                conns.append(dict(board=board, ref=ref, x0=round(x0, 3), y0=round(y0, 3), x1=round(x1, 3), y1=round(y1, 3),
                                  fp=str(fp.GetFPID().GetLibItemName())))
            if ref not in refs:
                continue
            side = "B" if fp.IsFlipped() else "F"
            cy = fp.GetCourtyard(pcbnew.B_CrtYd if side == "B" else pcbnew.F_CrtYd)
            if cy.OutlineCount():
                bb = cy.BBox()
            else:
                bb = pcbnew.BOX2I()
                for p in fp.Pads():
                    bb.Merge(p.GetBoundingBox())
            to = pcbnew.ToMM
            x0, x1 = to(bb.GetLeft()) - 100, to(bb.GetRight()) - 100
            y0, y1 = 100 - to(bb.GetBottom()), 100 - to(bb.GetTop())
            h, note = refs[ref]
            out.append(dict(board=board, ref=ref, side=side, x0=round(x0, 3), y0=round(y0, 3), x1=round(x1, 3),
                            y1=round(y1, 3), h=h, note=note, fp=str(fp.GetFPID().GetLibItemName())))
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "..", "boards", "standins.json"), "w") as f:
        json.dump(out, f, indent=1)
    with open(os.path.join(here, "..", "boards", "connectors.json"), "w") as f:
        json.dump(conns, f, indent=1)
    for o in out:
        print("%(board)s %(ref)s %(side)s X %(x0).2f..%(x1).2f Y %(y0).2f..%(y1).2f h %(h).2f  %(fp)s" % o)

if __name__ == "__main__":
    main(sys.argv[1])
