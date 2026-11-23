"""Project symbols (lib 'ansonia'): parts with no KiCad library symbol.
Pin tables come from the vendor documents named in each Description."""
import os
import symlib
from kisexp import Sym, dump, first

P, B, I, O, PI, PO, NC, OC = ("passive", "bidirectional", "input", "output", "power_in", "power_out",
                              "no_connect", "open_collector")


def sim7080g():
    t = {1: ("UART1_TXD", O), 2: ("UART1_RXD", I), 3: ("RTS", I), 4: ("CTS", O), 5: ("DCD", O), 6: ("DTR", I),
         7: ("RI", O), 9: ("PCM_DIN", I), 10: ("PCM_DOUT", O), 11: ("PCM_CLK", B), 12: ("PCM_SYNC", B),
         14: ("GPIO5", B), 15: ("SIM_DATA", B), 16: ("SIM_CLK", O), 17: ("SIM_RST", O), 18: ("SIM_VDD", PO),
         20: ("BOOT_CFG", I), 22: ("UART2_TXD", O), 23: ("UART2_RXD", I), 24: ("USB_VBUS", PI),
         25: ("USB_DP", B), 26: ("USB_DM", B), 28: ("NC", NC), 29: ("NC", NC), 32: ("RF_ANT", P),
         34: ("VBAT", PI), 35: ("VBAT", PI), 38: ("ADC", I), 39: ("PWRKEY", I), 40: ("VDD_EXT", PO),
         41: ("NETLIGHT", O), 42: ("STATUS", O), 43: ("ANT_CONTROL1", O), 44: ("ANT_CONTROL0", O),
         46: ("NC", NC), 47: ("NC", NC), 48: ("SPI_CS", O), 49: ("SPI_MOSI", O), 50: ("SPI_CLK", O),
         51: ("SPI_MISO", I), 52: ("NC", NC), 53: ("NC", NC), 54: ("NC", NC), 55: ("NC", NC), 56: ("NC", NC),
         57: ("GPIO1", B), 58: ("GPIO2", B), 59: ("GPIO3", B), 60: ("GPIO4", B), 61: ("UART3_TXD", O),
         62: ("UART3_RXD", I), 64: ("I2C_SDA", B), 65: ("I2C_SCL", O), 68: ("GNSS_ANT", P)}
    gnd = [8, 13, 19, 21, 27, 30, 31, 33, 36, 37, 45, 63, 66, 67] + list(range(69, 78))
    for g in gnd:
        t[g] = ("GND", PI)
    nums = sorted(t)
    left = [(n,) + t[n] for n in nums if n <= 38 and t[n][0] != "GND"]
    right = [(n,) + t[n] for n in nums if n > 38 and t[n][0] != "GND"]
    bottom = [(n,) + t[n] for n in nums if t[n][0] == "GND"]
    return symlib.box("ansonia:SIM7080G", left, right, bottom=bottom, ref="U", value="SIM7080G",
                      footprint="ansonia:SIM7080G",
                      datasheet="https://www.simcom.com/product/SIM7080G.html",
                      description="SIMCom SIM7080G Cat-M/NB-IoT + GNSS, LGA-77. Pins per SIM7080G pin table "
                                  "(cross-checked with SIM7080G/Y7080E Hardware Design fig. 2)")


def ewm104():
    t = {1: ("NC", NC), 2: ("SPDIF_IN/PIO19", B), 3: ("I2S_SDATA", O), 4: ("I2S_LRCK", O), 5: ("I2S_SCK", O),
         6: ("I2S_MCLK", O), 7: ("VBAT_SENSE", I), 8: ("USB_DN", B), 9: ("USB_DP", B), 10: ("VCHG", PI),
         11: ("VCHG_SENSE", I), 12: ("CHG_EXT", O), 13: ("SYS_CTRL", I), 14: ("VBAT", PI), 15: ("GND", PI),
         16: ("LED0", OC), 17: ("LED1", OC), 18: ("LED2", OC), 19: ("AIO4", B), 20: ("AIO5", B), 21: ("GND", PI),
         22: ("1V8", PO), 23: ("VDD_PADS1", PI), 24: ("VDD_PADS3_7", PI), 25: ("PIO4", B), 26: ("PIO3", B),
         27: ("PIO6", B), 28: ("PIO5", B), 29: ("PIO8", B), 30: ("PIO7", B), 31: ("PIO2", B), 32: ("PIO1", B),
         33: ("NC", NC), 34: ("SPK_RN", O), 35: ("SPK_RP", O), 36: ("SPK_LN", O), 37: ("SPK_LP", O),
         38: ("GND", PI), 39: ("MIC_BIAS", O), 40: ("MIC2_N", I), 41: ("MIC2_P", I), 42: ("MIC1_N", I),
         43: ("MIC1_P", I), 44: ("GND", PI), 45: ("GND", PI), 46: ("ANT", P), 47: ("GND", PI), 48: ("PIO54", B),
         49: ("PIO53", B), 50: ("PIO52", B), 51: ("PIO60", B), 52: ("PIO61", B), 53: ("PIO21", B),
         54: ("PIO20", B)}
    left = [(n,) + t[n] for n in range(1, 28)]
    right = [(n,) + t[n] for n in range(28, 55)]
    return symlib.box("ansonia:EWM104-BT5125", left, right, ref="U", value="EWM104-BT5125(I2S)",
                      footprint="ansonia:EWM104-BT5125",
                      datasheet="https://www.cdebyte.com/products/EWM104-BT5125(I2S)",
                      description="Ebyte EWM104-BT5125(I2S) QCC5125 BT audio module; pins per Ebyte user manual "
                                  "EWM104-BT5125_UserManual_EN_V1.0 sec. 2.2. Pin 46 ANT = 50 ohm, no on-board antenna")


def tps61088():
    left = [(9, "VIN", PI), (2, "EN", I), (3, "FSW", I), (13, "MODE", I), (19, "ILIM", P), (10, "SS", P),
            (18, "COMP", P), (11, "NC", P), (12, "NC", P)]
    right = [(4, "SW", P), (5, "SW", P), (6, "SW", P), (7, "SW", P), (8, "BOOT", P), (14, "VOUT", PO),
             (15, "VOUT", P), (16, "VOUT", P), (17, "FB", I), (1, "VCC", PO)]
    bottom = [(20, "AGND", PI), (21, "PGND", PI)]
    return symlib.box("ansonia:TPS61088RHL", left, right, bottom=bottom, ref="U", value="TPS61088RHLR",
                      footprint="Package_DFN_QFN:Texas_VQFN-RHL-20",
                      datasheet="https://www.ti.com/lit/ds/symlink/tps61088.pdf",
                      description="TI TPS61088 10 A sync boost, VQFN-20 RHL. Pins per TPS61088(-Q1) pin functions "
                                  "(SLVSE52A); NC pins 11/12 go to ground per datasheet")


def usbc():
    names = {"A1": "GND", "A2": "TX1+", "A3": "TX1-", "A4": "VBUS", "A5": "CC1", "A6": "D+", "A7": "D-",
             "A8": "SBU1", "A9": "VBUS", "A10": "RX2-", "A11": "RX2+", "A12": "GND", "SH": "SHIELD",
             "B1": "GND", "B2": "TX2+", "B3": "TX2-", "B4": "VBUS", "B5": "CC2", "B6": "D+", "B7": "D-",
             "B8": "SBU2", "B9": "VBUS", "B10": "RX1-", "B11": "RX1+", "B12": "GND"}
    left = [(n, names[n], P) for n in ["A4", "A9", "B4", "B9", "A5", "B5", "A6", "B6", "A7", "B7", "A8", "B8"]]
    right = [(n, names[n], P) for n in ["A2", "A3", "B2", "B3", "A10", "A11", "B10", "B11", "A1", "A12", "B1",
                                        "B12", "SH"]]
    right[-1] = ("SH", "SHIELD", P)
    return symlib.box("ansonia:USB_C_124019572112A", left, right, ref="J", value="124019572112A",
                      footprint="ansonia:USB_C_Amphenol_124019572112A",
                      datasheet="https://www.amphenol-cs.com/product/124019572112a.html",
                      description="Amphenol USB 3.2 Type-C receptacle, mid-mount, waterproof")


def pdic():
    t = {1: "VBUS1", 2: "VBUS1", 3: "CC1_1", 4: "CC2_1", 5: "VBUS2", 6: "VBUS2", 7: "CC1_2", 8: "CC2_2",
         9: "DP2", 10: "DM2", 11: "BAT", 12: "BAT", 13: "BAT", 14: "SYS", 15: "SYS", 16: "NTC", 17: "SDA",
         18: "SCL", 19: "INT", 20: "KEY", 21: "QI_5V", 22: "QI_EN", 41: "GND"}
    for n in range(23, 41):
        t[n] = "RSVD%d" % n
    left = [(n, t[n], P) for n in range(1, 11)] + [(n, t[n], P) for n in (20, 21, 22)]
    right = [(n, t[n], P) for n in range(11, 20)] + [(41, "GND", P)]
    bottom = [(n, t[n], P) for n in range(23, 41)]
    return symlib.box("ansonia:PD_IC_PLACEHOLDER", left, right, bottom=bottom, ref="U",
                      value="PD/charger IC TBD (DNP)", footprint="ansonia:PLACEHOLDER_PDIC_QFN40_6x6",
                      description="Placeholder for the power-bank / USB PD IC (2x Type-C: port 1 DRP, port 2 source)."
                                  " Net labels only; pin numbers are NOT a real part's pinout")


def lsm6dsox():
    """LSM6DSOX = pin-identical to KiCad's LSM6DSL (LGA-14); SDO/SA0, SDX, SCX made passive (strapped to GND)."""
    import copy
    base = symlib.load("Sensor_Motion:LSM6DSL")
    node = copy.deepcopy(base["node"])
    symlib._rename_units(node, "LSM6DSL", "LSM6DSOX")
    node[1] = "ansonia:LSM6DSOX"
    for sub in [x for x in node if isinstance(x, list) and x and x[0] == "symbol"]:
        for p in [x for x in sub if isinstance(x, list) and x and x[0] == "pin"]:
            if str(first(p, "number")[1]) in ("1", "2", "3"):
                p[1] = Sym("passive")
    for p in [x for x in node if isinstance(x, list) and x and x[0] == "property"]:
        if p[1] == "Value":
            p[2] = "LSM6DSOX"
    return symlib._finish("ansonia:LSM6DSOX", node)


ALL = [sim7080g, ewm104, tps61088, usbc, pdic, lsm6dsox]


def build(lib_path):
    syms = [f() for f in ALL]
    node = [Sym("kicad_symbol_lib"), [Sym("version"), 20241209], [Sym("generator"), "ansonia_tools"],
            [Sym("generator_version"), "1.0"]]
    for s in syms:
        n = [x for x in s["node"]]
        n[1] = s["lib_id"].split(":", 1)[1]
        node.append(n)
    os.makedirs(os.path.dirname(lib_path), exist_ok=True)
    with open(lib_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(dump(node) + "\n")
    return {s["lib_id"]: s for s in syms}
