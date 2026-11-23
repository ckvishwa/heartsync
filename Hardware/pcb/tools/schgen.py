"""Generate a hierarchical KiCad 10 schematic + project from a Python netlist description.

Every symbol is placed on a grid; every pin gets a global label (its net) or a
no-connect flag. Rails without a power-output pin get a PWR_FLAG. The result is
a real, ERC-checkable, editable schematic; the same data also goes to a JSON
netlist that the PCB builder reads (and is cross-checked against kicad-cli's
netlist export).
"""
import json
import os
import re
import uuid

import symlib
from kisexp import Sym, dump, q, fmt

NS = uuid.UUID("6f1c2e1a-3b7d-4f7e-9a51-6a2f0b0c0a11")
LIB_NAME = "ansonia"
GRID = 2.54
PRELOAD = {}


def uid(*parts):
    return str(uuid.uuid5(NS, "/".join(str(p) for p in parts)))


def snap(v, g=GRID):
    return round(v / g) * g


# ---------------------------------------------------------------- data model

class Part:
    def __init__(self, ref, sym, value, fp, pins, fields=None, dnp=False, in_bom=True):
        self.ref, self.sym, self.value, self.fp = ref, sym, value, fp
        self.pinmap = pins  # pin number -> net (or None = NC)
        self.fields = fields or {}
        self.dnp = dnp
        self.in_bom = in_bom


class Sheet:
    def __init__(self, design, name, title):
        self.design, self.name, self.title = design, name, title
        self.parts = []
        self.notes = []

    # generic part
    def part(self, ref, sym, value, fp="", pins=None, dnp=False, nc_ok=False, **fields):
        if isinstance(sym, str):
            sym = self.design.symbol(sym)
        ref = self.design.ref(ref)
        resolved = {}
        bynum = {p["num"]: p for p in sym["pins"]}
        for key, net in (pins or {}).items():
            key = str(key)
            if key in bynum:
                targets = [key]
            else:
                targets = [p["num"] for p in sym["pins"] if p["name"] == key]
                if not targets:
                    raise KeyError("%s: no pin %r in %s" % (ref, key, sym["lib_id"]))
            for t in targets:
                resolved[t] = net
        missing = [p["num"] for p in sym["pins"] if p["num"] not in resolved]
        if missing and not nc_ok:
            raise ValueError("%s (%s): unassigned pins %s" % (ref, sym["lib_id"], missing))
        for m in missing:
            resolved[m] = None
        fp = fp or symlib.prop(sym["node"], "Footprint") or ""
        p = Part(ref, sym, value, fp, resolved, fields, dnp)
        self.parts.append(p)
        return p

    # two-pin helpers -------------------------------------------------------
    def _two(self, prefix, lib, value, a, b, fp, dnp=False, **f):
        return self.part(prefix, lib, value, fp, {"1": a, "2": b}, dnp=dnp, **f)

    def R(self, value, a, b, fp="0402", dnp=False, **f):
        return self._two("R", "Device:R", value, a, b, FP.get(("R", fp), fp), dnp, **f)

    def C(self, value, a, b, fp="0402", dnp=False, **f):
        return self._two("C", "Device:C", value, a, b, FP.get(("C", fp), fp), dnp, **f)

    def L(self, value, a, b, fp, dnp=False, **f):
        return self._two("L", "Device:L", value, a, b, FP.get(("L", fp), fp), dnp, **f)

    def FB(self, value, a, b, fp="0805", **f):
        return self._two("FB", "Device:FerriteBead_Small", value, a, b, FP.get(("L", fp), fp), **f)

    def D(self, value, k, a, fp, lib="Device:D", **f):
        return self.part("D", lib, value, fp, {"K": k, "A": a}, **f)

    def note(self, text):
        self.notes.append(text)


FP = {
    ("R", "0402"): "Resistor_SMD:R_0402_1005Metric",
    ("R", "0603"): "Resistor_SMD:R_0603_1608Metric",
    ("R", "0805"): "Resistor_SMD:R_0805_2012Metric",
    ("R", "1206"): "Resistor_SMD:R_1206_3216Metric",
    ("C", "0402"): "Capacitor_SMD:C_0402_1005Metric",
    ("C", "0603"): "Capacitor_SMD:C_0603_1608Metric",
    ("C", "0805"): "Capacitor_SMD:C_0805_2012Metric",
    ("C", "1206"): "Capacitor_SMD:C_1206_3216Metric",
    ("C", "1210"): "Capacitor_SMD:C_1210_3225Metric",
    ("L", "0805"): "Inductor_SMD:L_0805_2012Metric",
    ("L", "1008"): "Inductor_SMD:L_1008_2520Metric",
    ("L", "0603"): "Inductor_SMD:L_0603_1608Metric",
}


class Design:
    def __init__(self, name, title, rev="A", company="Ansonia", comments=()):
        self.name, self.title, self.rev, self.company = name, title, rev, company
        self.comments = list(comments)
        self.sheets = []
        self._counters = {}
        self._syms = {}

    def sheet(self, name, title):
        s = Sheet(self, name, title)
        self.sheets.append(s)
        return s

    def symbol(self, lib_id):
        if lib_id not in self._syms:
            self._syms[lib_id] = PRELOAD.get(lib_id) or symlib.load(lib_id)
        return self._syms[lib_id]

    def add_symbol(self, sym):
        self._syms[sym["lib_id"]] = sym
        return sym

    def ref(self, ref):
        if re.match(r"^[A-Z#]+$", ref):  # prefix only -> auto number
            n = self._counters.get(ref, 0) + 1
            while "%s%d" % (ref, n) in self._used():
                n += 1
            self._counters[ref] = n
            return "%s%d" % (ref, n)
        if ref in self._used():
            raise ValueError("duplicate ref " + ref)
        return ref

    def _used(self):
        return {p.ref for s in self.sheets for p in s.parts}

    def parts(self):
        return [p for s in self.sheets for p in s.parts]

    def nets(self):
        nets = {}
        for s in self.sheets:
            for p in s.parts:
                for num, net in p.pinmap.items():
                    if net:
                        nets.setdefault(net, []).append((p.ref, num))
        return nets


# ---------------------------------------------------------------- writer

PWR_OUT = {"power_out"}


def _label_geom(pin, sx, sy):
    """Return (x, y, angle, justify) for a global label at the pin end."""
    x = sx + pin["x"]
    y = sy - pin["y"]
    r = int(round(pin["rot"])) % 360
    # pin rot = direction from end point towards the body
    ang = {0: 180, 180: 0, 90: 270, 270: 90}[r]
    just = "right" if ang in (180, 270) else "left"
    return x, y, ang, just


def _sym_extent(sym):
    xs = [p["x"] for p in sym["pins"]] or [0]
    ys = [p["y"] for p in sym["pins"]] or [0]
    return min(xs), max(xs), min(ys), max(ys)


def write(design, outdir, lib_dir_rel="../lib"):
    os.makedirs(outdir, exist_ok=True)
    nets = design.nets()
    # power flags: nets that contain power_in pins but no power_out pin
    pin_types = {}
    for p in design.parts():
        bynum = {pp["num"]: pp for pp in p.sym["pins"]}
        for num, net in p.pinmap.items():
            if net:
                pin_types.setdefault(net, set()).add(bynum[num]["type"])
    flag_nets = sorted(n for n, t in pin_types.items() if "power_in" in t and not (t & PWR_OUT))
    root_uuid = uid(design.name, "root")
    pwrflag = design.symbol("power:PWR_FLAG")

    sheet_files = []
    netlist = {"design": design.name, "parts": [], "nets": {}}
    for si, sh in enumerate(design.sheets):
        sh_uuid = uid(design.name, "sheet", sh.name)
        fname = "%s.kicad_sch" % sh.name
        sheet_files.append((sh, sh_uuid, fname))
        items = []
        lib_ids = {}
        # layout: shelf packing
        maxw = 520.0
        x, y, rowh = 25.4, 30.48, 0.0
        placed = []
        for p in sh.parts:
            x0, x1, y0, y1 = _sym_extent(p.sym)
            names = [n for n in p.pinmap.values() if n]
            lab = max([len(n) for n in names] + [3]) * 1.1 + 4
            w = (x1 - x0) + 2 * lab + 12
            h = (y1 - y0) + 14
            if x + w > maxw:
                x, y, rowh = 25.4, y + rowh + 6, 0.0
            sx = snap(x + lab - x0 + 4)
            sy = snap(y + y1 + 6)
            placed.append((p, sx, sy))
            x += w
            rowh = max(rowh, h)
        # flags for this sheet: nets first appearing here
        page_w = maxw + 20
        page_h = max(y + rowh + 40, 200)
        # notes
        for p, sx, sy in placed:
            lib_ids[p.sym["lib_id"]] = p.sym
            su = uid(design.name, "sym", p.ref)
            props = [
                ("Reference", p.ref, False), ("Value", p.value, False), ("Footprint", p.fp, True),
                ("Datasheet", p.fields.get("datasheet", symlib.prop(p.sym["node"], "Datasheet") or ""), True),
                ("Description", p.fields.get("description", symlib.prop(p.sym["node"], "Description") or ""), True),
            ]
            for k in ("MPN", "Manufacturer", "LCSC", "Note"):
                if p.fields.get(k):
                    props.append((k, p.fields[k], True))
            x0, x1, y0, y1 = _sym_extent(p.sym)
            node = [Sym("symbol"), [Sym("lib_id"), p.sym["lib_id"]], [Sym("at"), sx, sy, 0],
                    [Sym("unit"), 1], [Sym("exclude_from_sim"), Sym("no")],
                    [Sym("in_bom"), Sym("yes" if p.in_bom else "no")], [Sym("on_board"), Sym("yes")],
                    [Sym("dnp"), Sym("yes" if p.dnp else "no")], [Sym("uuid"), su]]
            for i, (k, v, hide) in enumerate(props):
                if k == "Reference":
                    at = [Sym("at"), sx, sy - y1 - 2.54, 0]
                elif k == "Value":
                    at = [Sym("at"), sx, sy - y0 + 2.54, 0]
                else:
                    at = [Sym("at"), sx, sy, 0]
                e = [Sym("effects"), [Sym("font"), [Sym("size"), 1.27, 1.27]]]
                if hide:
                    e.append([Sym("hide"), Sym("yes")])
                node.append([Sym("property"), k, v, at, e])
            for pin in p.sym["pins"]:
                node.append([Sym("pin"), pin["num"], [Sym("uuid"), uid(design.name, "pin", p.ref, pin["num"])]])
            node.append([Sym("instances"), [Sym("project"), design.name,
                         [Sym("path"), "/%s/%s" % (root_uuid, sh_uuid), [Sym("reference"), p.ref],
                          [Sym("unit"), 1]]]])
            items.append(node)
            # labels / no-connects
            seen_pos = set()
            for pin in p.sym["pins"]:
                net = p.pinmap.get(pin["num"])
                lx, ly, ang, just = _label_geom(pin, sx, sy)
                key = (round(lx, 3), round(ly, 3))
                if key in seen_pos:  # stacked pins share one label
                    continue
                seen_pos.add(key)
                if net is None:
                    items.append([Sym("no_connect"), [Sym("at"), lx, ly],
                                  [Sym("uuid"), uid(design.name, "nc", p.ref, pin["num"])]])
                else:
                    shape = "passive"
                    items.append([Sym("global_label"), net, [Sym("shape"), Sym(shape)],
                                  [Sym("at"), lx, ly, ang],
                                  [Sym("fields_autoplaced"), Sym("yes")],
                                  [Sym("effects"), [Sym("font"), [Sym("size"), 1.0, 1.0]],
                                   [Sym("justify"), Sym(just)]],
                                  [Sym("uuid"), uid(design.name, "gl", p.ref, pin["num"])]])
            netlist["parts"].append({
                "ref": p.ref, "value": p.value, "footprint": p.fp, "lib_id": p.sym["lib_id"],
                "sheet": sh.name, "sheet_uuid": sh_uuid, "sym_uuid": su, "dnp": p.dnp,
                "fields": {k: v for k, v in p.fields.items() if k in ("MPN", "Manufacturer", "LCSC", "Note")},
                "datasheet": p.fields.get("datasheet", symlib.prop(p.sym["node"], "Datasheet") or ""),
                "description": p.fields.get("description", symlib.prop(p.sym["node"], "Description") or ""),
                "in_bom": p.in_bom,
                "pins": {num: net for num, net in p.pinmap.items()},
                "pin_names": {pp["num"]: pp["name"] for pp in p.sym["pins"]},
            })
        # PWR_FLAGs: put each flagged net on the first sheet that uses it
        fx = snap(30.0)
        fy = snap(page_h - 25)
        for net in flag_nets:
            first_sheet = next(s for s in design.sheets if any(net in pp.pinmap.values() for pp in s.parts))
            if first_sheet is not sh:
                continue
            lib_ids[pwrflag["lib_id"]] = pwrflag
            ref = "#FLG%02d" % (flag_nets.index(net) + 1)
            fu = uid(design.name, "flag", net)
            node = [Sym("symbol"), [Sym("lib_id"), "power:PWR_FLAG"], [Sym("at"), fx, fy, 0], [Sym("unit"), 1],
                    [Sym("exclude_from_sim"), Sym("no")], [Sym("in_bom"), Sym("yes")], [Sym("on_board"), Sym("yes")],
                    [Sym("dnp"), Sym("no")], [Sym("uuid"), fu],
                    [Sym("property"), "Reference", ref, [Sym("at"), fx, fy - 5, 0],
                     [Sym("effects"), [Sym("font"), [Sym("size"), 1.27, 1.27]], [Sym("hide"), Sym("yes")]]],
                    [Sym("property"), "Value", "PWR_FLAG", [Sym("at"), fx, fy - 3.8, 0],
                     [Sym("effects"), [Sym("font"), [Sym("size"), 1.0, 1.0]]]],
                    [Sym("property"), "Footprint", "", [Sym("at"), fx, fy, 0],
                     [Sym("effects"), [Sym("font"), [Sym("size"), 1.27, 1.27]], [Sym("hide"), Sym("yes")]]],
                    [Sym("property"), "Datasheet", "", [Sym("at"), fx, fy, 0],
                     [Sym("effects"), [Sym("font"), [Sym("size"), 1.27, 1.27]], [Sym("hide"), Sym("yes")]]],
                    [Sym("pin"), "1", [Sym("uuid"), uid(design.name, "flagpin", net)]],
                    [Sym("instances"), [Sym("project"), design.name,
                                        [Sym("path"), "/%s/%s" % (root_uuid, sh_uuid),
                                         [Sym("reference"), ref], [Sym("unit"), 1]]]]]
            items.append(node)
            items.append([Sym("global_label"), net, [Sym("shape"), Sym("passive")], [Sym("at"), fx, fy, 270],
                          [Sym("fields_autoplaced"), Sym("yes")],
                          [Sym("effects"), [Sym("font"), [Sym("size"), 1.0, 1.0]], [Sym("justify"), Sym("right")]],
                          [Sym("uuid"), uid(design.name, "flaglabel", net)]])
            fx += 22.86
            if fx > page_w - 30:
                fx, fy = snap(30.0), fy + 12.7
        # notes text
        ty = 18.0
        notes = ["%s - %s" % (sh.title, design.title)] + sh.notes
        for i, t in enumerate(notes):
            items.append([Sym("text"), t, [Sym("exclude_from_sim"), Sym("no")], [Sym("at"), 25.4, ty, 0],
                          [Sym("effects"), [Sym("font"), [Sym("size"), 2.0 if i == 0 else 1.4,
                                                                2.0 if i == 0 else 1.4]],
                           [Sym("justify"), Sym("left"), Sym("bottom")]],
                          [Sym("uuid"), uid(design.name, "text", sh.name, i)]])
            ty += 3.2 if i == 0 else 2.4
        _write_sch(os.path.join(outdir, fname), design, sh.title, lib_ids, items, sh_uuid,
                   page=(page_w, max(page_h, ty + 20 if ty > page_h else page_h)), page_no=si + 2)

    # root sheet with sheet symbols
    items = []
    bx, by = 25.4, 40.64
    for i, (sh, sh_uuid, fname) in enumerate(sheet_files):
        node = [Sym("sheet"), [Sym("at"), bx, by], [Sym("size"), 50.8, 20.32],
                [Sym("exclude_from_sim"), Sym("no")], [Sym("in_bom"), Sym("yes")], [Sym("on_board"), Sym("yes")],
                [Sym("dnp"), Sym("no")], [Sym("fields_autoplaced"), Sym("yes")],
                [Sym("stroke"), [Sym("width"), 0.1524], [Sym("type"), Sym("solid")]],
                [Sym("fill"), [Sym("color"), 0, 0, 0, 0.0]], [Sym("uuid"), sh_uuid],
                [Sym("property"), "Sheetname", sh.name, [Sym("at"), bx, by - 0.7, 0],
                 [Sym("effects"), [Sym("font"), [Sym("size"), 1.27, 1.27]], [Sym("justify"), Sym("left"), Sym("bottom")]]],
                [Sym("property"), "Sheetfile", fname, [Sym("at"), bx, by + 20.9, 0],
                 [Sym("effects"), [Sym("font"), [Sym("size"), 1.27, 1.27]], [Sym("justify"), Sym("left"), Sym("top")]]],
                [Sym("instances"), [Sym("project"), design.name,
                                    [Sym("path"), "/" + root_uuid, [Sym("page"), str(i + 2)]]]]]
        items.append(node)
        items.append([Sym("text"), sh.title, [Sym("exclude_from_sim"), Sym("no")], [Sym("at"), bx + 2, by + 10, 0],
                      [Sym("effects"), [Sym("font"), [Sym("size"), 1.5, 1.5]], [Sym("justify"), Sym("left")]],
                      [Sym("uuid"), uid(design.name, "roottext", sh.name)]])
        bx += 63.5
        if bx > 330:
            bx, by = 25.4, by + 38.1
    ty = 20.0
    for i, t in enumerate([design.title] + design.comments):
        items.append([Sym("text"), t, [Sym("exclude_from_sim"), Sym("no")], [Sym("at"), 25.4, ty, 0],
                      [Sym("effects"), [Sym("font"), [Sym("size"), 2.5 if i == 0 else 1.4, 2.5 if i == 0 else 1.4]],
                       [Sym("justify"), Sym("left"), Sym("bottom")]],
                      [Sym("uuid"), uid(design.name, "rootnote", i)]])
        ty += 4 if i == 0 else 2.4
    root_page_h = max(by + 60, ty + 20, 297)
    _write_sch(os.path.join(outdir, design.name + ".kicad_sch"), design, design.title, {}, items, root_uuid,
               page=(420, root_page_h), page_no=1, root=True)

    # project file
    _write_pro(design, outdir)
    with open(os.path.join(outdir, "sym-lib-table"), "w", newline="\n") as f:
        f.write('(sym_lib_table\n  (version 7)\n  (lib (name "%s")(type "KiCad")(uri "${KIPRJMOD}/%s/%s.kicad_sym")(options "")(descr "Ansonia project symbols"))\n)\n'
                % (LIB_NAME, lib_dir_rel, LIB_NAME))
    with open(os.path.join(outdir, "fp-lib-table"), "w", newline="\n") as f:
        f.write('(fp_lib_table\n  (version 7)\n  (lib (name "%s")(type "KiCad")(uri "${KIPRJMOD}/%s/%s.pretty")(options "")(descr "Ansonia project footprints"))\n)\n'
                % (LIB_NAME, lib_dir_rel, LIB_NAME))
    netlist["nets"] = {n: v for n, v in sorted(design.nets().items())}
    netlist["root_uuid"] = root_uuid
    with open(os.path.join(outdir, design.name + ".netlist.json"), "w") as f:
        json.dump(netlist, f, indent=1)
    return netlist


def _write_sch(path, design, title, lib_ids, items, file_uuid, page, page_no, root=False):
    w, h = page
    head = [Sym("kicad_sch"), [Sym("version"), 20250114], [Sym("generator"), "eeschema"],
            [Sym("generator_version"), "9.0"], [Sym("uuid"), file_uuid],
            [Sym("paper"), "User", snap(w, 1), snap(h, 1)],
            [Sym("title_block"), [Sym("title"), title], [Sym("date"), "2026-11-23"], [Sym("rev"), design.rev],
             [Sym("company"), design.company],
             [Sym("comment"), 1, "Generated by Hardware/pcb/tools (edit the Python source, then regenerate)"]],
            [Sym("lib_symbols")] + [s["node"] for _, s in sorted(lib_ids.items())]]
    body = head + items
    if root:
        body.append([Sym("sheet_instances"), [Sym("path"), "/", [Sym("page"), "1"]]])
        body.append([Sym("embedded_fonts"), Sym("no")])
    else:
        body.append([Sym("embedded_fonts"), Sym("no")])
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(dump(body) + "\n")


def _write_pro(design, outdir):
    path = os.path.join(outdir, design.name + ".kicad_pro")
    pro = {
        "board": {"design_settings": {"rules": {
            "min_clearance": 0.127, "min_track_width": 0.127, "min_through_hole_diameter": 0.3,
            "min_via_diameter": 0.45, "min_via_annular_width": 0.075, "min_hole_to_hole": 0.25,
            "min_copper_edge_clearance": 0.3, "min_hole_clearance": 0.2, "min_silk_clearance": 0.0,
            "min_text_height": 0.6, "min_text_thickness": 0.1, "solder_mask_to_copper_clearance": 0.0}}},
        "meta": {"filename": design.name + ".kicad_pro", "version": 3},
        "net_settings": {"classes": NETCLASSES.get(design.name, NETCLASSES["default"]),
                         "meta": {"version": 4},
                         "netclass_patterns": PATTERNS.get(design.name, [])},
        "schematic": {"legacy_lib_dir": "", "legacy_lib_list": []},
        "sheets": [[uid(design.name, "root"), "Root"]] + [[uid(design.name, "sheet", s.name), s.name]
                                                         for s in design.sheets],
        "erc": {"rule_severities": {"single_global_label": "ignore", "lib_symbol_mismatch": "warning"}},
        "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": []},
    }
    with open(path, "w") as f:
        json.dump(pro, f, indent=2)


def _nc(name, clearance=0.15, track=0.2, via_d=0.6, via_drill=0.3, diff_w=None, diff_gap=None):
    d = {"name": name, "clearance": clearance, "track_width": track, "via_diameter": via_d,
         "via_drill": via_drill, "microvia_diameter": 0.3, "microvia_drill": 0.1, "bus_width": 12,
         "wire_width": 6, "line_style": 0, "pcb_color": "rgba(0, 0, 0, 0.000)",
         "schematic_color": "rgba(0, 0, 0, 0.000)", "priority": 2147483647}
    if diff_w:
        d.update({"diff_pair_width": diff_w, "diff_pair_gap": diff_gap, "diff_pair_via_gap": 0.25})
    return d


NETCLASSES = {"default": [_nc("Default")]}
PATTERNS = {}


def set_netclasses(design_name, classes, patterns):
    NETCLASSES[design_name] = classes
    PATTERNS[design_name] = [{"netclass": c, "pattern": p} for p, c in patterns]
