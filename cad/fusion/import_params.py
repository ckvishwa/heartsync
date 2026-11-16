# Fusion 360 script: load cad/params.csv into the active design's user parameters.
# See cad/fusion/README.md. NOT YET RUN IN FUSION: test on an empty design first.
#
# Runs inside Fusion 360 only (the `adsk` modules do not exist elsewhere).
import csv
import os
import traceback

import adsk.core
import adsk.fusion

PARAMS_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "params.csv")


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)
        if not design:
            ui.messageBox("Open a design first.")
            return

        user_params = design.userParameters
        updated, created, skipped = [], [], []

        with open(PARAMS_CSV, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                name = row["name"].strip()
                unit = row["unit"].strip()
                try:
                    value = float(row["value"])
                except ValueError:
                    skipped.append(f"{name} (not a number)")
                    continue
                if value == 0:
                    skipped.append(f"{name} ({row['status']})")
                    continue

                # Counts are unitless; everything else is a length in mm.
                fusion_unit = "" if unit == "count" else unit
                expression = f"{value:g}" if fusion_unit == "" else f"{value:g} {fusion_unit}"
                comment = row.get("comment", "")

                existing = user_params.itemByName(name)
                if existing:
                    existing.expression = expression
                    existing.comment = comment
                    updated.append(name)
                else:
                    user_params.add(
                        name,
                        adsk.core.ValueInput.createByString(expression),
                        fusion_unit,
                        comment,
                    )
                    created.append(name)

        ui.messageBox(
            f"Created {len(created)}, updated {len(updated)}, skipped {len(skipped)}.\n\n"
            + ("Skipped (unknown values):\n" + "\n".join(skipped) if skipped else "")
        )
    except Exception:  # Fusion scripts report errors through a message box
        if ui:
            ui.messageBox("import_params failed:\n" + traceback.format_exc())
