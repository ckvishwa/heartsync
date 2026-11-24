"""Runner for ansonia_revG.py, pasted into the Fusion MCP script tool (or run from Scripts and Add-Ins).

    import importlib.util
    spec = importlib.util.spec_from_file_location("run_revG", r"D:/SyncD/cad/fusion/run_revG.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); m.go("build")   # or "exports", "shots"

"build" opens a NEW design document (the open ones are left alone), builds, checks and writes
cad/fusion/_out/build_report.txt (+ _clashes.json). A build takes longer than the MCP call timeout:
wait for the report file. "exports" / "shots" work on the active design.
"""
import adsk.core
import adsk.fusion
import importlib.util
import os
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "_out")


def _mod():
    spec = importlib.util.spec_from_file_location("ansonia_revG", os.path.join(HERE, "ansonia_revG.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def go(what="build"):
    os.makedirs(OUT, exist_ok=True)
    app = adsk.core.Application.get()
    done = os.path.join(OUT, what + ".done")
    if os.path.exists(done):
        os.remove(done)
    try:
        m = _mod()
        if what == "build":
            for d in [app.documents.item(i) for i in range(app.documents.count)]:
                try:
                    des = adsk.fusion.Design.cast(d.products.itemByProductType("DesignProductType"))
                    if des and des.attributes.itemByName("ansonia", "build") and not d.isSaved:
                        d.close(False)          # an earlier unsaved build of this script
                except Exception:
                    pass
            doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            design = adsk.fusion.Design.cast(app.activeProduct)
            design.designType = adsk.fusion.DesignTypes.DirectDesignType
            text = m.build(os.path.join(OUT, "build_report.txt"))
        elif what == "exports":
            text = m.exports(os.path.join(os.path.dirname(HERE), "exports", "revG"))
        elif what == "shots":
            text = m.screenshots(os.path.join(os.path.dirname(HERE), "renders", "revG"))
        else:
            text = "unknown step " + what
    except Exception:
        text = "RUNNER FAILED:\n" + traceback.format_exc()
        with open(os.path.join(OUT, what + "_error.txt"), "w") as f:
            f.write(text)
    with open(done, "w") as f:
        f.write(text[:2000])
    return text
