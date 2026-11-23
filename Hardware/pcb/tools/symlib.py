"""Load KiCad library symbols (flattening `extends`) and build simple box symbols.

A symbol here is a dict:
  lib_id, node (S-expr list ready for the schematic's lib_symbols), pins:
  [{num, name, type, x, y, rot, unit}], units (count)
"""
import copy
import os
from kisexp import parse, find, first, Sym

KICAD_SYM = r"C:\Program Files\KiCad\10.0\share\kicad\symbols"
_libcache = {}


def _lib(name):
    if name not in _libcache:
        path = os.path.join(KICAD_SYM, name + ".kicad_sym")
        tree = parse(open(path, encoding="utf-8").read())
        _libcache[name] = {s[1]: s for s in find(tree, "symbol")}
    return _libcache[name]


def _rename_units(node, old, new):
    for sub in find(node, "symbol"):
        if sub[1].startswith(old + "_"):
            sub[1] = new + sub[1][len(old):]


def load(lib_id):
    lib, name = lib_id.split(":", 1)
    syms = _lib(lib)
    node = copy.deepcopy(syms[name])
    ext = first(node, "extends")
    if ext:
        parent = copy.deepcopy(syms[ext[1]])
        # child keeps its properties; parent's graphics/pins/flags fill in
        props = {p[1]: p for p in find(node, "property")}
        merged = [Sym("symbol"), name]
        for item in parent[2:]:
            if isinstance(item, list) and item[0] == "property" and item[1] in props:
                merged.append(props.pop(item[1]))
            else:
                merged.append(item)
        merged.extend(props.values())
        _rename_units(merged, ext[1], name)
        node = merged
    node[1] = lib_id
    return _finish(lib_id, node)


def _finish(lib_id, node):
    bare = lib_id.split(":", 1)[1]
    pins = []
    units = 1
    for sub in find(node, "symbol"):
        tail = sub[1][len(bare) + 1:] if sub[1].startswith(bare + "_") else sub[1].split("_", 1)[-1]
        u, _style = tail.split("_")
        u = int(u)
        units = max(units, u)
        for p in find(sub, "pin"):
            at = first(p, "at")
            nm = first(p, "name")
            nu = first(p, "number")
            hide = any(x == "hide" for x in p) or bool(first(p, "hide"))
            pins.append(dict(num=str(nu[1]), name=str(nm[1]), type=str(p[1]),
                             x=float(at[1]), y=float(at[2]), rot=float(at[3]) if len(at) > 3 else 0.0,
                             unit=u, hidden=hide))
    return dict(lib_id=lib_id, node=node, pins=pins, units=units)


def prop(node, key):
    for p in find(node, "property"):
        if p[1] == key:
            return p[2]
    return None


# ---------- generated box symbols ----------

def _pin_node(num, name, ptype, x, y, rot, length=2.54):
    return [Sym("pin"), Sym(ptype), Sym("line"), [Sym("at"), x, y, rot], [Sym("length"), length],
            [Sym("name"), name, [Sym("effects"), [Sym("font"), [Sym("size"), 1.0, 1.0]]]],
            [Sym("number"), str(num), [Sym("effects"), [Sym("font"), [Sym("size"), 1.0, 1.0]]]]]


def box(lib_id, left, right, top=(), bottom=(), ref="U", value=None, footprint="", datasheet="",
        description="", width=None):
    """left/right/top/bottom: lists of (num, name, type) or None for a gap."""
    bare = lib_id.split(":", 1)[1]
    p = 2.54
    rows = max(len(left), len(right), 1)
    cols = max(len(top), len(bottom), 0)
    maxname = max([len(n[1]) for n in list(left) + list(right) if n] + [4])
    w = width or max(round((maxname * 1.0 * 2 + 6) / p) * p, (cols + 1) * p, 10.16)
    w = round(w / (2 * p)) * 2 * p
    h = (rows + 1) * p
    x0, x1 = -w / 2, w / 2
    y0, y1 = h / 2, -h / 2  # lib coords: +y up
    y0 = round(y0 / p) * p
    y1 = y0 - h
    graph = [Sym("symbol"), bare + "_0_1",
             [Sym("rectangle"), [Sym("start"), x0, y0], [Sym("end"), x1, y1],
              [Sym("stroke"), [Sym("width"), 0.254], [Sym("type"), Sym("default")]],
              [Sym("fill"), [Sym("type"), Sym("background")]]]]
    pins = [Sym("symbol"), bare + "_1_1"]
    for i, pn in enumerate(left):
        if pn:
            pins.append(_pin_node(pn[0], pn[1], pn[2], x0 - p, y0 - p * (i + 1), 0))
    for i, pn in enumerate(right):
        if pn:
            pins.append(_pin_node(pn[0], pn[1], pn[2], x1 + p, y0 - p * (i + 1), 180))
    for i, pn in enumerate(top):
        if pn:
            pins.append(_pin_node(pn[0], pn[1], pn[2], x0 + p * (i + 1), y0 + p, 270))
    for i, pn in enumerate(bottom):
        if pn:
            pins.append(_pin_node(pn[0], pn[1], pn[2], x0 + p * (i + 1), y1 - p, 90))

    def pr(k, v, y, hide=False):
        e = [Sym("effects"), [Sym("font"), [Sym("size"), 1.27, 1.27]]]
        if hide:
            e.append([Sym("hide"), Sym("yes")])
        return [Sym("property"), k, v, [Sym("at"), 0, y, 0], e]

    node = [Sym("symbol"), lib_id, [Sym("exclude_from_sim"), Sym("no")], [Sym("in_bom"), Sym("yes")],
            [Sym("on_board"), Sym("yes")],
            pr("Reference", ref, y0 + 1.5), pr("Value", value or bare, y1 - 1.5),
            pr("Footprint", footprint, y1 - 3.5, True), pr("Datasheet", datasheet, y1 - 5.5, True),
            pr("Description", description, y1 - 7.5, True), graph, pins]
    return _finish(lib_id, node)
