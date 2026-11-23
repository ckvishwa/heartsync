"""Ansonia rev G board circuits. Values cite their source in the sheet notes.
Edit here, then run build_all.py (never hand-edit the generated .kicad_sch)."""
from schgen import Design, set_netclasses, _nc

GND = "GND"
V3 = "+3V3"
VSYS = "VSYS"

JST_SH = "Connector_JST:JST_SH_SM%02dB-SRSS-TB_1x%02d-1MP_P1.00mm_Horizontal"
UFL = "Connector_Coaxial:U.FL_Hirose_U.FL-R-SMT-1_Vertical"


def sh(n):
    return JST_SH % (n, n)


def conn(s, ref, n, nets, fp=None, value=None, **kw):
    sym = "Connector_Generic:Conn_01x%02d" % n
    return s.part(ref, sym, value or ("JST SH %d-pin" % n), fp or sh(n), {str(i + 1): nets[i] for i in range(n)}, **kw)


def pi_match(s, rf_from, rf_to, tag):
    """Pi-match pads: shunt (DNP) - series 0R - shunt (DNP)."""
    s.C("DNP", rf_from, GND, dnp=True, Note="pi-match shunt, " + tag)
    s.R("0R", rf_from, rf_to, Note="pi-match series, " + tag)
    s.C("DNP", rf_to, GND, dnp=True, Note="pi-match shunt, " + tag)


J1_NETS = [VSYS, VSYS, VSYS, GND, GND, GND, "I2C_SDA", "I2C_SCL", "PWR_INT", "I2S1_BCLK", "I2S1_WS",
           "I2S1_DOUT", "TAS_PDN", "AMP_BOOST_EN", "USB_DP", "USB_DN", "SPKL_P", "SPKL_P", "SPKL_N", "SPKL_N"]


# =====================================================================================  CARRIER
def carrier():
    d = Design("carrier", "Ansonia carrier board rev A (rev G shell)", comments=[
        "4-layer 1.0 mm, component side faces the front wall. ESP32-S3-WROOM-1U-N16R8 + SIM7080G + EWM104-BT5125.",
        "J1 = board-to-board link to the power board (same pinout both ends, straight JST SH cable).",
        "Open items: see Hardware/pcb/README.md."])

    # ---------------------------------------------------------------- power
    s = d.sheet("power", "Power in, 3V3 buck-boost")
    s.note("J1 pin 1-3 VSYS (3.4-4.6 V from the power board), 4-6 GND; JST SH contacts are 1 A each.")
    s.note("U2 TPS63001 fixed 3.3 V buck-boost: L 2.2 uH, Cin 10 uF, VINA RC 100R/0.1 uF per TPS63001 datasheet fig. 1;")
    s.note("output 2 x 22 uF (Wi-Fi TX bursts).")
    conn(s, "J1", 20, J1_NETS, value="Link to power board (SM20B-SRSS-TB)")
    s.C("22uF", VSYS, GND, "0805")
    s.C("22uF", VSYS, GND, "0805")
    s.part("U", "Regulator_Switching:TPS63001", "TPS63001DRC", "Package_SON:Texas_DRC0010J", {
        "VIN": VSYS, "VINA": "3V3_VINA", "EN": VSYS, "PS/SYNC": VSYS, "L1": "3V3_L1", "L2": "3V3_L2",
        "VOUT": V3, "FB": V3, "GND": GND, "PGND": GND}, MPN="TPS63001DRCR", LCSC="C28855")
    s.R("100R", VSYS, "3V3_VINA")
    s.C("0.1uF", "3V3_VINA", GND)
    s.C("10uF", VSYS, GND, "0603")
    s.L("2.2uH", "3V3_L1", "3V3_L2", "1008", MPN="DFE252012F-2R2M=P2")
    s.C("22uF", V3, GND, "0805")
    s.C("22uF", V3, GND, "0805")
    s.C("0.1uF", V3, GND)

    # ---------------------------------------------------------------- MCU
    s = d.sheet("mcu", "ESP32-S3-WROOM-1U-N16R8")
    s.note("N16R8 = octal PSRAM: IO35-37 not usable (module datasheet table 3-1 note b). Straps IO0/3/45/46 unused.")
    s.note("IO19/20 native USB -> J1 -> power board USB-C port 1 data. EN RC 10k/1uF per module datasheet fig. 9-1.")
    s.note("N16R8 is rated -40..65 C ambient (module datasheet table 1-2): keep it away from the amp/boost heat.")
    s.part("U", "RF_Module:ESP32-S3-WROOM-1", "ESP32-S3-WROOM-1U-N16R8", "ansonia:ESP32-S3-WROOM-1U_NoVias", {
        "GND": GND, "3V3": V3, "EN": "ESP_EN",
        "IO4": "BT_I2S_BCLK", "IO5": "BT_I2S_WS", "IO6": "BT_I2S_SD", "IO7": "TOUCH",
        "IO15": "I2S1_BCLK", "IO16": "I2S1_WS", "IO17": "I2S1_DOUT", "IO18": "MIC_SD",
        "IO8": "I2C_SDA", "IO9": "I2C_SCL", "USB_D-": "USB_DN", "USB_D+": "USB_DP",
        "IO3": None, "IO46": None, "IO10": "OLED_CS", "IO11": "SPI_MOSI", "IO12": "SPI_SCLK",
        "IO13": "OLED_DC", "IO14": "OLED_RST", "IO21": "GEST_INT", "IO47": "SIM_RXD_3V3", "IO48": "SIM_TXD_3V3",
        "IO45": None, "IO0": "ESP_IO0", "IO35": None, "IO36": None, "IO37": None,
        "IO38": "EXP_INT", "IO39": "PWR_INT", "IO40": "EPD_CS", "IO41": "EPD_DC", "IO42": "EPD_BUSY",
        "RXD0": "ESP_RXD0", "TXD0": "ESP_TXD0", "IO2": "ESP_IO2", "IO1": "ESP_IO1"},
        MPN="ESP32-S3-WROOM-1U-N16R8", LCSC="C3013946")
    s.C("10uF", V3, GND, "0603")
    s.C("0.1uF", V3, GND)
    s.R("10k", V3, "ESP_EN")
    s.C("1uF", "ESP_EN", GND)
    s.R("10k", V3, "ESP_IO0")
    s.R("4.7k", V3, "I2C_SDA", Note="I2C pull-up (bus also on the power and front boards)")
    s.R("4.7k", V3, "I2C_SCL")
    s.R("10k", V3, "EXP_INT")
    s.R("10k", V3, "GEST_INT")
    s.R("10k", V3, "PWR_INT")
    for n in ["ESP_EN", "ESP_IO0", "ESP_RXD0", "ESP_TXD0", "USB_DP", "USB_DN", "ESP_IO1", "ESP_IO2", V3, GND]:
        tp = s.part("TP", "Connector:TestPoint", n, "TestPoint:TestPoint_Pad_D1.0mm", {"1": n})
        tp.in_bom = False

    # ---------------------------------------------------------------- IO
    s = d.sheet("io", "I/O expanders, buttons, haptics")
    s.note("Three TCA9554 (0x20 outputs, 0x21 inputs, 0x22 Bluetooth control): the pin plan needs 20 I/O, one TCA9554 has 8.")
    s.note("Outputs that must stay off at power-up get 10k pull-downs (TCA9554 inputs have 100k internal pull-ups).")
    s.note("DRV2605L: REG 1 uF, VDD 1 uF + 0.1 uF, IN/TRIG to GND when unused (DRV2605L datasheet pin table).")
    exp1 = {"A0": GND, "A1": GND, "A2": GND, "P0": "SIM_PWRKEY_CTL", "P1": "SIM_DTR_3V3", "P2": "TAS_PDN",
            "P3": "DRV_EN", "P4": "AMP_BOOST_EN", "P5": "OLED_VCC_EN", "P6": "EPD_RST", "P7": "MUTE_LED",
            "~{INT}": "EXP_INT", "SCL": "I2C_SCL", "SDA": "I2C_SDA", "VDD": V3, "GND": GND}
    s.part("U", "Interface_Expansion:TCA9554PW", "TCA9554PW (0x20)", "", exp1, MPN="TCA9554PWR", LCSC="C86803")
    exp2 = dict(exp1, A0=V3, P0="BTN_MUTE", P1="BTN_PWR", P2="BTN_VOLDN", P3="BTN_VOLUP", P4="BTN_PLAY",
                P5="SIM_STATUS_3V3", P6="BT_AMP_EN", P7=None)
    s.part("U", "Interface_Expansion:TCA9554PW", "TCA9554PW (0x21)", "", exp2, MPN="TCA9554PWR", LCSC="C86803")
    exp3 = dict(exp1, A0=GND, A1=V3, P0="BT_SYS_CTRL", P1="BT_RST", P2="BT_PIO2_CTL", P3="BT_PIO3_CTL",
                P4="BT_PIO4_CTL", P5="BT_PIO5_CTL", P6=None, P7=None)
    s.part("U", "Interface_Expansion:TCA9554PW", "TCA9554PW (0x22)", "", exp3, MPN="TCA9554PWR", LCSC="C86803")
    for _ in range(3):
        s.C("0.1uF", V3, GND)
    s.R("10k", "DRV_EN", GND)
    s.R("10k", "OLED_VCC_EN", GND)
    conn(s, "J12", 6, ["BTN_MUTE", "BTN_PWR", "BTN_VOLDN", "BTN_VOLUP", "BTN_PLAY", GND],
         value="Buttons (MUTE PWR VOL- VOL+ PLAY GND)")
    s.R("330R", "MUTE_LED", "MUTE_LED_A")
    conn(s, "J9", 2, ["MUTE_LED_A", GND], value="Mute LED")
    s.part("U", "Driver:DRV2605LDGS", "DRV2605LDGS", "Package_SO:TSSOP-10_3x3mm_P0.5mm", {
        "REG": "DRV_REG", "SCL": "I2C_SCL", "SDA": "I2C_SDA", "IN/TRIG": GND, "EN": "DRV_EN",
        "VDD/NC": VSYS, "OUT+": "HAPTIC_P", "GND": GND, "OUT-": "HAPTIC_N", "VDD": VSYS},
        MPN="DRV2605LDGSR", LCSC="C527464")
    s.C("1uF", "DRV_REG", GND)
    s.C("1uF", VSYS, GND)
    s.C("0.1uF", VSYS, GND)
    conn(s, "J6", 2, ["HAPTIC_P", "HAPTIC_N"], value="Haptic LRA")

    # ---------------------------------------------------------------- cellular
    s = d.sheet("cellular", "SIM7080G LTE-M/NB-IoT + GNSS, nano-SIM")
    s.note("VBAT straight from VSYS: 100 uF + 10 uF + 0.1 uF + 33 pF + 10 pF and a TVS at the pins (SIM7080G HD 3.1, fig. 5).")
    s.note("VBAT range 2.7-4.8 V (SIM7080G HD checklist). UART is 1.8 V (VDD_EXT): TXB0104 shifts to 3.3 V.")
    s.note("BOOT_CFG (20) and SPI_MOSI (49) must not be pulled up before power-up: BOOT_CFG goes to a test pad only.")
    s.note("RF: 50 ohm CPWG, pi-match pads (0R + 2 x DNP) at both U.FL. Test pads for USB (firmware update).")
    simpins = {"UART1_TXD": "SIM_TXD", "UART1_RXD": "SIM_RXD", "DTR": "SIM_DTR", "SIM_DATA": "SIM_DATA",
               "SIM_CLK": "SIM_CLK", "SIM_RST": "SIM_RST", "SIM_VDD": "SIM_VDD", "BOOT_CFG": "SIM_BOOT_CFG",
               "USB_VBUS": "SIM_USB_VBUS", "USB_DP": "SIM_USB_DP", "USB_DM": "SIM_USB_DM", "RF_ANT": "LTE_RF",
               "VBAT": VSYS, "PWRKEY": "SIM_PWRKEY", "VDD_EXT": "VDD_EXT", "STATUS": "SIM_STATUS",
               "GNSS_ANT": "GNSS_RF", "GND": GND}
    s.part("U", "ansonia:SIM7080G", "SIM7080G", "ansonia:SIM7080G", simpins, nc_ok=True, MPN="SIM7080G",
           LCSC="C2687012")
    s.C("100uF", VSYS, GND, "1210", Note="6.3 V X5R")
    s.C("10uF", VSYS, GND, "0603")
    s.C("0.1uF", VSYS, GND)
    s.C("33pF", VSYS, GND)
    s.C("10pF", VSYS, GND)
    s.part("D", "Device:D_Zener", "ESD5Z5.0 (5 V TVS)", "Diode_SMD:D_SOD-523", {"K": VSYS, "A": GND},
           Note="TVS at VBAT, SIM7080G HD 3.1")
    s.C("1uF", "VDD_EXT", GND)
    s.part("U", "Logic_LevelTranslator:TXB0104PW", "TXB0104PW", "", {
        "VCCA": "VDD_EXT", "A1": "SIM_RXD", "A2": "SIM_TXD", "A3": "SIM_STATUS", "A4": "SIM_DTR", "OE": "VDD_EXT",
        "GND": GND, "B1": "SIM_RXD_3V3", "B2": "SIM_TXD_3V3", "B3": "SIM_STATUS_3V3", "B4": "SIM_DTR_3V3",
        "VCCB": V3, "NC": None}, MPN="TXB0104PWR", LCSC="C53406")
    s.C("0.1uF", "VDD_EXT", GND)
    s.C("0.1uF", V3, GND)
    s.part("Q", "Transistor_BJT:MMBT3904", "MMBT3904", "", {"B": "SIM_PWRKEY_B", "E": GND, "C": "SIM_PWRKEY"})
    s.R("4.7k", "SIM_PWRKEY_CTL", "SIM_PWRKEY_B")
    s.R("10k", "SIM_PWRKEY_B", GND, Note="holds PWRKEY released while the expander pin is an input (100k pull-up)")
    # SIM card
    s.part("J14", "Connector:SIM_Card", "nano-SIM push-pull", "Connector_Card:nanoSIM_GCT_SIM8060-6-0-14-00", {
        "VCC": "SIM_VDD", "RST": "SIMC_RST", "CLK": "SIMC_CLK", "GND": GND, "VPP": None, "I/O": "SIMC_DATA"},
           MPN="SIM8060-6-0-14-00-A")
    s.R("22R", "SIM_RST", "SIMC_RST")
    s.R("22R", "SIM_CLK", "SIMC_CLK")
    s.R("22R", "SIM_DATA", "SIMC_DATA")
    s.R("10k", "SIM_VDD", "SIMC_DATA", dnp=True, Note="SIM_DATA pull-up option")
    s.C("0.1uF", "SIM_VDD", GND)
    s.C("33pF", "SIMC_CLK", GND, dnp=True)
    s.part("U", "Power_Protection:TPD4E05U06DQA", "TPD4E05U06DQA", "", {
        "D1+": "SIMC_DATA", "D1-": "SIMC_CLK", "D2+": "SIMC_RST", "D2-": "SIM_VDD", "GND": GND, "NC": None},
           MPN="TPD4E05U06DQAR")
    for n in ["SIM_BOOT_CFG", "VDD_EXT", "SIM_USB_VBUS", "SIM_USB_DP", "SIM_USB_DM", "SIM_PWRKEY"]:
        s.part("TP", "Connector:TestPoint", n, "TestPoint:TestPoint_Pad_D1.0mm", {"1": n}).in_bom = False
    # RF
    pi_match(s, "LTE_RF", "LTE_UFL", "LTE")
    s.part("J15", "Connector:Conn_Coaxial", "U.FL LTE", UFL, {"In": "LTE_UFL", "Ext": GND}, MPN="U.FL-R-SMT-1(10)")
    pi_match(s, "GNSS_RF", "GNSS_UFL", "GNSS")
    s.part("J16", "Connector:Conn_Coaxial", "U.FL GNSS", UFL, {"In": "GNSS_UFL", "Ext": GND}, MPN="U.FL-R-SMT-1(10)")

    # ---------------------------------------------------------------- bluetooth
    s = d.sheet("bluetooth", "Ebyte EWM104-BT5125(I2S) Bluetooth audio")
    s.note("Pin 46 ANT is a 50 ohm stamp hole with NO on-board antenna (Ebyte manual sec. 2.1): U.FL for a 2.4 GHz FPC antenna.")
    s.note("VBAT 2.8-4.6 V from VSYS. VDD_PADS = 3.3 V so I2S/PIO match the ESP32. BT is I2S master into ESP32 I2S0.")
    s.note("SYS_CTRL must not be RC-delayed or tied to VBAT (manual 4.1): driven by expander 0x22 through 1k, 10k pull-down.")
    s.note("PIO1 reset and PIO2-5 button polarity: confirm with Ebyte firmware before bring-up. VCHG unused (NC).")
    s.part("U", "ansonia:EWM104-BT5125", "EWM104-BT5125(I2S)", "ansonia:EWM104-BT5125", {
        "I2S_SDATA": "BT_I2S_SD", "I2S_LRCK": "BT_I2S_WS", "I2S_SCK": "BT_I2S_BCLK", "VBAT_SENSE": VSYS,
        "USB_DN": "BT_USB_DN", "USB_DP": "BT_USB_DP", "SYS_CTRL": "BT_SYS_CTRL_M", "VBAT": VSYS, "GND": GND,
        "1V8": "BT_1V8", "VDD_PADS1": V3, "VDD_PADS3_7": V3, "PIO4": "BT_PIO4", "PIO3": "BT_PIO3",
        "PIO5": "BT_PIO5", "PIO2": "BT_PIO2", "PIO1": "BT_PIO1", "ANT": "BT_RF", "PIO20": "BT_PIO20"},
           nc_ok=True, MPN="EWM104-BT5125(I2S)")
    s.C("10uF", VSYS, GND, "0603")
    s.C("0.1uF", VSYS, GND)
    s.C("1uF", "BT_1V8", GND)
    s.C("0.1uF", V3, GND)
    s.C("0.1uF", V3, GND)
    s.R("1k", "BT_SYS_CTRL", "BT_SYS_CTRL_M")
    s.R("10k", "BT_SYS_CTRL_M", GND)
    s.R("1k", "BT_RST", "BT_PIO1")
    for k in (2, 3, 4, 5):
        s.R("1k", "BT_PIO%d_CTL" % k, "BT_PIO%d" % k)
    s.R("1k", "BT_PIO20", "BT_AMP_EN")
    for n in ["BT_USB_DP", "BT_USB_DN"]:
        s.part("TP", "Connector:TestPoint", n, "TestPoint:TestPoint_Pad_D1.0mm", {"1": n}).in_bom = False
    pi_match(s, "BT_RF", "BT_UFL", "BT")
    s.part("J17", "Connector:Conn_Coaxial", "U.FL BT", UFL, {"In": "BT_UFL", "Ext": GND}, MPN="U.FL-R-SMT-1(10)")

    # ---------------------------------------------------------------- display
    s = d.sheet("display", "3.12in SSD1322 panel (J11) + 12 V boost, back e-paper FPC (J13, DNP)")
    s.note("SSD1322 values from the SSD1322 datasheet rev 1.2 fig. 14-1: C1-C3 1 uF (VCI, VDDIO, VDD), VCOMH 4.7 uF + 0.1 uF,")
    s.note("VCC 4.7 uF, VSL 50 ohm (51R used) + 2 x 1N4148 to VSS, IREF R = (VCC - 6 V)/10 uA = 600k at 12 V -> 620k (sec. 8.6).")
    s.note("4-wire SPI: BS0 = BS1 = 0, E/RD# and R/W# to VSS, D2 open, D3-D7 to VSS (pin table 7-1). VCC floats when off (8.9).")
    s.note("TPS61040: Vout = 1.233 V x (1 + 487k/56k) = 11.96 V; 10 uH, Schottky, 4.7 uF in, 1 uF out (TPS61040 datasheet).")
    s.note("Q1/Q2 high-side switch removes the boost input so VCC floats when the panel is off (SSD1322 8.9 note 2).")
    s.note("J13 e-paper: generic 24-pin 0.5 mm FPC (SSD168x-style pinout), DNP; panel booster parts to add once chosen.")
    s.part("Q", "Transistor_FET:AO3401A", "AO3401A", "", {"G": "OLED_SW_G", "S": VSYS, "D": "OLED_VIN"})
    s.R("100k", VSYS, "OLED_SW_G")
    s.part("Q", "Transistor_FET:2N7002", "2N7002", "", {"G": "OLED_VCC_EN", "S": GND, "D": "OLED_SW_G"})
    s.C("4.7uF", "OLED_VIN", GND, "0603")
    s.part("U", "Regulator_Switching:TPS61040DBV", "TPS61040DBV", "", {
        "SW": "OLED_SW", "GND": GND, "FB": "OLED_FB", "EN": "OLED_VIN", "VIN": "OLED_VIN"},
           MPN="TPS61040DBVR", LCSC="C7722")
    s.L("10uH", "OLED_VIN", "OLED_SW", "1008", MPN="DFE252012F-100M")
    s.D("MBR0530", "OLED_12V", "OLED_SW", "Diode_SMD:D_SOD-123", lib="Device:D_Schottky")
    s.R("487k", "OLED_12V", "OLED_FB")
    s.R("56k", "OLED_FB", GND)
    s.C("22pF", "OLED_12V", "OLED_FB", Note="feed-forward")
    s.C("1uF", "OLED_12V", GND, "0603", Note="25 V")
    p30 = {1: GND, 2: GND, 3: "OLED_12V", 4: "OLED_VCOMH", 5: GND, 6: GND, 7: GND, 8: GND, 9: GND, 10: GND,
           11: None, 12: "SPI_MOSI", 13: "SPI_SCLK", 14: GND, 15: GND, 16: GND, 17: GND, 18: "OLED_DC",
           19: "OLED_CS", 20: "OLED_RST", 21: None, 22: "OLED_IREF", 23: None, 24: V3, 25: "OLED_VDD",
           26: V3, 27: "OLED_VSL", 28: GND, 29: "OLED_12V", 30: GND}
    s.part("J11", "Connector_Generic:Conn_01x30", "FH12-30S-0.5SH (SSD1322 panel)",
           "Connector_FFC-FPC:Hirose_FH12-30S-0.5SH_1x30-1MP_P0.50mm_Horizontal",
           {str(k): v for k, v in p30.items()}, MPN="FH12-30S-0.5SH(55)")
    s.C("4.7uF", "OLED_12V", GND, "0805", Note="C5 VCC, 25 V")
    s.C("4.7uF", "OLED_VCOMH", GND, "0805", Note="C4a, 25 V")
    s.C("0.1uF", "OLED_VCOMH", GND, Note="C4b")
    s.C("1uF", V3, GND, Note="C1 VCI")
    s.C("1uF", V3, GND, Note="C2 VDDIO")
    s.C("1uF", "OLED_VDD", GND, Note="C3 VDD (internal regulator)")
    s.R("620k", "OLED_IREF", GND, Note="R1 IREF")
    s.R("51R", "OLED_VSL", "OLED_VSL_D", "0603", Note="R2 VSL 50 ohm")
    s.D("1N4148WS", "OLED_VSL_D2", "OLED_VSL_D", "Diode_SMD:D_SOD-323")
    s.D("1N4148WS", GND, "OLED_VSL_D2", "Diode_SMD:D_SOD-323")
    p24 = {i: None for i in range(1, 25)}
    p24.update({8: GND, 9: "EPD_BUSY", 10: "EPD_RST", 11: "EPD_DC", 12: "EPD_CS", 13: "SPI_SCLK", 14: "SPI_MOSI",
                15: V3, 16: V3, 17: GND})
    s.part("J13", "Connector_Generic:Conn_01x24", "FH12-24S-0.5SH (e-paper, DNP)",
           "Connector_FFC-FPC:Hirose_FH12-24S-0.5SH_1x24-1MP_P0.50mm_Horizontal",
           {str(k): v for k, v in p24.items()}, dnp=True, MPN="FH12-24S-0.5SH(55)")
    s.C("1uF", V3, GND, dnp=True, Note="e-paper VCI")

    # ---------------------------------------------------------------- front-wall links
    s = d.sheet("links", "Front-wall boards and speaker L")
    s.note("J8 -> front sensor board (ICS-43434 + APDS-9960). J7 -> touch strip. J4 -> left speaker (amp channel A on the power board, via J1).")
    conn(s, "J8", 8, [V3, GND, "I2C_SDA", "I2C_SCL", "GEST_INT", "I2S1_BCLK", "I2S1_WS", "MIC_SD"],
         value="Front sensor board")
    conn(s, "J7", 2, ["TOUCH", GND], value="Touch strip")
    conn(s, "J4", 2, ["SPKL_P", "SPKL_N"], value="Speaker L")
    s.C("10uF", V3, GND, "0603", Note="front board supply bulk")
    s.note("H1-H4: M2 holes on the printed bracket frame (H3/H4 moved from the fit-map spots, see README).")
    for h in ("H1", "H2", "H3", "H4"):
        s.part(h, "Mechanical:MountingHole", "M2", "MountingHole:MountingHole_2.2mm_M2", {})

    set_netclasses("carrier", [
        _nc("Default"),
        _nc("Power", track=0.5, via_d=0.8, via_drill=0.4),
        _nc("RF50", clearance=0.2, track=0.3),
        _nc("Speaker", track=0.5),
        _nc("USB", diff_w=0.2, diff_gap=0.15)],
        [("VSYS", "Power"), ("+3V3", "Power"), ("OLED_12V", "Power"), ("OLED_VIN", "Power"), ("GND", "Power"),
         ("*_RF", "RF50"), ("*_UFL", "RF50"), ("SPKL_*", "Speaker"), ("USB_D*", "USB")])
    return d


# =====================================================================================  POWER
def power():
    d = Design("power", "Ansonia power board rev A (rev G shell)", comments=[
        "2 oz copper, 1.6 mm, 4-layer. Two Amphenol 124019572112A USB-C: port 1 in/out (DRP), port 2 output only.",
        "Power-bank / PD IC NOT CHOSEN: U1 is a DNP placeholder with labelled nets (see README for options).",
        "TAS5805M BTL stereo amp + TPS61088 12 V PVDD boost. J1 mirrors the carrier's J1."])

    s = d.sheet("usb", "USB-C ports and protection")
    s.note("Port 1 (J2, X +52.75): DRP, data D+/D- go to the ESP32 via J1 (flashing). Port 2 (J3, X +66.05): source only.")
    s.note("ESD: TPD4E05U06 on CC/D lines of each port; VBUS TVS SMF22A (22 V standoff, PD up to 20 V).")
    usb_common = {"A1": GND, "A12": GND, "B1": GND, "B12": GND, "SH": GND, "A2": None, "A3": None, "B2": None,
                  "B3": None, "A10": None, "A11": None, "B10": None, "B11": None, "A8": None, "B8": None}
    s.part("J2", "ansonia:USB_C_124019572112A", "124019572112A (port 1, in/out)", "", dict(
        usb_common, A4="VBUS1", A9="VBUS1", B4="VBUS1", B9="VBUS1", A5="CC1_1", B5="CC2_1", A6="USB_DP",
        B6="USB_DP", A7="USB_DN", B7="USB_DN"), MPN="124019572112A")
    s.part("J3", "ansonia:USB_C_124019572112A", "124019572112A (port 2, out)", "", dict(
        usb_common, A4="VBUS2", A9="VBUS2", B4="VBUS2", B9="VBUS2", A5="CC1_2", B5="CC2_2", A6="DP2",
        B6="DP2", A7="DM2", B7="DM2"), MPN="124019572112A")
    s.part("U5", "Power_Protection:TPD4E05U06DQA", "TPD4E05U06DQA", "", {
        "D1+": "CC1_1", "D1-": "CC2_1", "D2+": "USB_DP", "D2-": "USB_DN", "GND": GND, "NC": None},
           MPN="TPD4E05U06DQAR")
    s.part("U6", "Power_Protection:TPD4E05U06DQA", "TPD4E05U06DQA", "", {
        "D1+": "CC1_2", "D1-": "CC2_2", "D2+": "DP2", "D2-": "DM2", "GND": GND, "NC": None}, MPN="TPD4E05U06DQAR")
    for v in ("VBUS1", "VBUS2"):
        s.part("D", "Device:D_Zener", "SMF22A", "Diode_SMD:D_SOD-123F", {"K": v, "A": GND}, Note="VBUS TVS")
        s.C("10uF", v, GND, "0805", Note="25 V")

    s = d.sheet("charger", "Power-bank / PD IC (placeholder), cell, NTC, protection")
    s.note("U1 DNP placeholder: VBUS1/2, CC x2, DP2/DM2, BAT, SYS, NTC, SDA/SCL, INT, KEY, QI_5V, QI_EN.")
    s.note("Cell 1160100 10,000 mAh on J4 (PH2.0, 2 A rating!). Full-power audio can pull ~7 A from the cell:")
    s.note("either cap amp power in firmware or use the BAT solder pads (TP) with 18 AWG leads. Q = reverse-battery PFET (DMP3013SFV),")
    s.note("F1 = 8 A fuse, D = SMF5.0A TVS. The 0R (DNP) bridges BAT_SW -> VSYS for bring-up without the PD IC.")
    s.part("U1", "ansonia:PD_IC_PLACEHOLDER", "PD/charger IC TBD", "", {
        "VBUS1": "VBUS1", "CC1_1": "CC1_1", "CC2_1": "CC2_1", "VBUS2": "VBUS2", "CC1_2": "CC1_2", "CC2_2": "CC2_2",
        "DP2": "DP2", "DM2": "DM2", "BAT": "BAT_SW", "SYS": VSYS, "NTC": "NTC", "SDA": "I2C_SDA",
        "SCL": "I2C_SCL", "INT": "PWR_INT", "KEY": "PWR_KEY", "QI_5V": "QI_5V", "QI_EN": "QI_EN", "GND": GND},
           nc_ok=True, dnp=True)
    conn(s, "J4", 2, ["BAT_RAW", GND], fp="Connector_JST:JST_PH_S2B-PH-SM4-TB_1x02-1MP_P2.00mm_Horizontal",
         value="Cell (JST PH 2.0)")
    s.part("TP1", "Connector:TestPoint", "BAT+ pad", "TestPoint:TestPoint_Pad_3.0x3.0mm", {"1": "BAT_RAW"})
    s.part("TP2", "Connector:TestPoint", "BAT- pad", "TestPoint:TestPoint_Pad_3.0x3.0mm", {"1": GND})
    conn(s, "J5", 2, ["NTC", GND], value="NTC 10k B3435")
    s.part("F1", "Device:Fuse", "8A fast", "Fuse:Fuse_1206_3216Metric", {"1": "BAT_RAW", "2": "BAT_F"},
           MPN="0466008.NR")
    s.part("Q", "Transistor_FET:DMP3013SFV", "DMP3013SFV", "", {"S": "BAT_SW", "G": "BAT_Q_G", "D": "BAT_F"},
           Note="reverse-battery PFET (drain to cell)")
    s.R("10k", "BAT_Q_G", GND)
    s.part("D", "Device:D_Zener", "SMF5.0A", "Diode_SMD:D_SOD-123F", {"K": "BAT_SW", "A": GND})
    s.C("22uF", "BAT_SW", GND, "0805")
    s.R("0R", "BAT_SW", VSYS, "1206", dnp=True, Note="bring-up bypass, PD IC absent")
    s.C("22uF", VSYS, GND, "0805")
    s.R("10k", "PWR_KEY", V3, dnp=True)
    conn(s, "J6", 3, ["QI_5V", "QI_EN", GND], value="Qi TX driver")

    s = d.sheet("boost", "TPS61088 PVDD boost, 12 V")
    s.note("Values from TPS61088(-Q1) datasheet sec. 9.2: Vout = 1.204 x (1 + 499k/56k) = 11.93 V; RFREQ = 4(1/fsw - tdelay*Vout/Vin)/CFREQ")
    s.note("-> 232k for ~600 kHz at Vin 3.2 V; L 2.2 uH (Isat > 11 A); ILIM 49.9k (9.4 A typ in PWM, MODE = GND);")
    s.note("comp R5 = 2pi Vout Rsense fc Co / ((1-D) Vref Gea) = 23.7k at fc 5 kHz, Co 45 uF eff, D 0.75; C5 = Ro Co/(2 R5) = 8.2 nF; C8 open.")
    s.note("SS 47 nF, BOOT 0.1 uF, VCC 4.7 uF. EN from the carrier expander (10k pull-down: off at power-up).")
    s.part("U", "ansonia:TPS61088RHL", "TPS61088RHLR", "", {
        "VIN": "BAT_SW", "EN": "AMP_BOOST_EN", "FSW": "BST_FSW", "MODE": GND, "ILIM": "BST_ILIM", "SS": "BST_SS",
        "COMP": "BST_COMP", "NC": GND, "SW": "BST_SW", "BOOT": "BST_BOOT", "VOUT": "PVDD", "FB": "BST_FB",
        "VCC": "BST_VCC", "AGND": GND, "PGND": GND}, MPN="TPS61088RHLR", LCSC="C88281")
    s.R("10k", "AMP_BOOST_EN", GND)
    s.C("22uF", "BAT_SW", GND, "0805")
    s.C("22uF", "BAT_SW", GND, "0805")
    s.C("10uF", "BAT_SW", GND, "0603")
    s.C("0.1uF", "BAT_SW", GND)
    s.L("2.2uH", "BAT_SW", "BST_SW", "Inductor_SMD:L_Bourns_SRP7028A_7.3x6.6mm", MPN="SRP7028A-2R2M")
    s.R("232k", "BST_FSW", "BST_SW")
    s.C("0.1uF", "BST_BOOT", "BST_SW")
    s.C("4.7uF", "BST_VCC", GND, "0603")
    s.C("47nF", "BST_SS", GND)
    s.R("49.9k", "BST_ILIM", GND)
    s.R("23.7k", "BST_COMP", "BST_COMP_RC")
    s.C("8.2nF", "BST_COMP_RC", GND)
    s.C("10pF", "BST_COMP", GND, dnp=True, Note="C8, open per eq. 20")
    s.R("499k", "PVDD", "BST_FB")
    s.R("56k", "BST_FB", GND)
    for _ in range(3):
        s.C("22uF", "PVDD", GND, "1206", Note="25 V X5R")
    s.C("1uF", "PVDD", GND, "0603", Note="25 V")

    s = d.sheet("amp", "TAS5805M stereo BTL amplifier")
    s.note("TAS5805M datasheet fig. 8-1 / table 8-3 (ferrite-bead output filter): PVDD 2 x (22 uF + 22 uF + 0.1 uF), L5 100R@100MHz bead,")
    s.note("DVDD 4.7 uF + 0.1 uF, AVDD 1 uF, VR_DIG 1 uF, BST 0.22 uF x4, outputs 300R@100MHz beads + 2200 pF + (2200 pF + 68R) per leg.")
    s.note("ADR 4.7k to DVDD -> I2C 0x2C. PDN from the expander with a 10k pull-down; start-up: PDN high, wait >= 5 ms, then clocks.")
    s.note("Channel A -> speaker L (via J1 -> carrier J4), channel B -> speaker R (J7 here). Use Fsw 384 kHz + spread spectrum (8.2.1).")
    s.FB("100R@100MHz 4A", "PVDD", "PVDD_AMP", Note="L5")
    s.C("2200pF", "PVDD", GND, Note="C23")
    s.part("U", "Amplifier_Audio:TAS5805MPWP", "TAS5805MPWP", "ansonia:TI_PWP0028M_HTSSOP-28_ThermalVias_0.3", {
        "DGND": GND, "DVDD": V3, "ADR/~{FAULT}": "TAS_ADR", "VR_DIG": "TAS_VRDIG", "LRCLK": "I2S1_WS",
        "SCLK": "I2S1_BCLK", "SDIN": "I2S1_DOUT", "SDOUT": None, "SDA": "I2C_SDA", "SCL": "I2C_SCL",
        "~{PDN}": "TAS_PDN", "AVDD": "TAS_AVDD", "AGND": GND, "PVDD": "PVDD_AMP", "OUT_B+": "OUTB_P",
        "BST_B+": "BSTB_P", "PGND": GND, "OUT_B-": "OUTB_N", "BST_B-": "BSTB_N", "BST_A-": "BSTA_N",
        "OUT_A-": "OUTA_N", "BST_A+": "BSTA_P", "OUT_A+": "OUTA_P", "EP": GND}, MPN="TAS5805MPWPR", LCSC="C2059816")
    for _ in range(2):
        s.C("22uF", "PVDD_AMP", GND, "0805", Note="35 V")
        s.C("22uF", "PVDD_AMP", GND, "0805", Note="35 V")
        s.C("0.1uF", "PVDD_AMP", GND, Note="50 V")
    s.C("4.7uF", V3, GND, "0603", Note="C7 DVDD")
    s.C("0.1uF", V3, GND, Note="C8")
    s.C("1uF", "TAS_AVDD", GND, "0603", Note="C9")
    s.C("1uF", "TAS_VRDIG", GND, "0603", Note="C10")
    s.R("4.7k", V3, "TAS_ADR", Note="R1 -> addr 0x2C")
    s.R("10k", "TAS_PDN", GND, Note="hold PDN low until firmware enables")
    for bst, out in (("BSTA_P", "OUTA_P"), ("BSTA_N", "OUTA_N"), ("BSTB_P", "OUTB_P"), ("BSTB_N", "OUTB_N")):
        s.C("0.22uF", bst, out, "0603", Note="BST, 50 V")
    legs = (("OUTA_P", "SPKL_P"), ("OUTA_N", "SPKL_N"), ("OUTB_P", "SPKR_P"), ("OUTB_N", "SPKR_N"))
    for out, spk in legs:
        s.FB("300R@100MHz 3.1A", out, spk, Note="NFZ2MSM301 / UPZ2012E class")
        s.C("2200pF", spk, GND, "0603", Note="100 V")
        s.C("2200pF", spk, spk + "_SN", "0603")
        s.R("68R", spk + "_SN", GND, "0603")
    conn(s, "J7", 2, ["SPKR_P", "SPKR_N"], fp="Connector_JST:JST_PH_S2B-PH-SM4-TB_1x02-1MP_P2.00mm_Horizontal",
         value="Speaker R (JST PH)")

    s = d.sheet("link", "Link to carrier, 3V3 LDO")
    s.note("J1 mirrors carrier J1 (straight cable). U: AP2112K-3.3 for TAS5805M DVDD (I2C pull-ups live on the carrier).")
    conn(s, "J1", 20, J1_NETS, value="Link to carrier (SM20B-SRSS-TB)")
    s.part("U", "Regulator_Linear:AP2112K-3.3", "AP2112K-3.3", "", {"VIN": VSYS, "GND": GND, "EN": VSYS,
                                                                    "NC": None, "VOUT": V3},
           MPN="AP2112K-3.3TRG1", LCSC="C51118")
    s.C("1uF", VSYS, GND)
    s.C("1uF", V3, GND)

    set_netclasses("power", [
        _nc("Default"),
        _nc("Power", track=0.6, via_d=0.8, via_drill=0.4),
        _nc("HighCurrent", clearance=0.2, track=1.5, via_d=0.8, via_drill=0.4),
        _nc("Speaker", track=0.6),
        _nc("USB", diff_w=0.2, diff_gap=0.15)],
        [("BAT_*", "HighCurrent"), ("BST_SW", "HighCurrent"), ("PVDD*", "HighCurrent"), ("VBUS*", "Power"),
         ("VSYS", "Power"), ("GND", "Power"), ("OUT*", "Speaker"), ("SPK*", "Speaker"), ("USB_D*", "USB")])
    return d


# =====================================================================================  FRONT
def front_sensor():
    d = Design("front_sensor", "Ansonia front sensor board rev A (mic + gesture)", comments=[
        "0.8 mm 2-layer. ICS-43434 bottom-port under the 1.0 mm wall hole at X -69.5, Y 31.25 (mic on the BACK side,",
        "port hole through the PCB); APDS-9960 on the FRONT side behind the IR-clear window at X -64, Y 31.25."])
    s = d.sheet("sensors", "ICS-43434 + APDS-9960")
    s.note("ICS-43434: L/R to GND = left slot; 0.1 uF at VDD; 100k pull-down on SD (ICS-43434 datasheet).")
    s.note("APDS-9960 single supply (datasheet fig. 14b): VDD via 22R + 1 uF; LEDA 1 uF + 10 uF; LDR tied to LEDK.")
    conn(s, "J1", 8, [V3, GND, "I2C_SDA", "I2C_SCL", "GEST_INT", "I2S1_BCLK", "I2S1_WS", "MIC_SD"],
         value="To carrier J8", fp="Connector_JST:JST_SH_BM08B-SRSS-TB_1x08-1MP_P1.00mm_Vertical")
    s.part("U1", "Sensor_Audio:ICS-43434", "ICS-43434", "", {"WS": "I2S1_WS", "LR": GND, "GND": GND,
                                                              "SCK": "I2S1_BCLK", "VDD": V3, "SD": "MIC_SD"},
           MPN="ICS-43434")
    s.C("0.1uF", V3, GND)
    s.R("100k", "MIC_SD", GND)
    s.part("U2", "Sensor:APDS-9960", "APDS-9960", "", {"SDA": "I2C_SDA", "INT": "GEST_INT", "LDR": "APDS_LEDK",
                                                      "LED_K": "APDS_LEDK", "LED_A": V3, "GND": GND,
                                                      "SCL": "I2C_SCL", "VDD": "APDS_VDD"}, MPN="APDS-9960")
    s.R("22R", V3, "APDS_VDD")
    s.C("1uF", "APDS_VDD", GND)
    s.C("1uF", V3, GND)
    s.C("10uF", V3, GND, "0603")
    return d


def front_touch():
    d = Design("front_touch", "Ansonia touch strip rev A", comments=[
        "0.8 mm 2-layer, 40 x 5 mm. One copper sense pad (front side) with a ground hatch around it, to carrier J7."])
    s = d.sheet("touch", "Touch pad")
    s.note("Sense pad on F.Cu facing the 1.2 mm front wall; hatched GND ring on F.Cu only, B.Cu kept clear under the pad.")
    s.part("E1", "Connector:TestPoint", "Touch pad 34x3", "ansonia:TouchPad_34x3", {"1": "TOUCH"}).in_bom = False
    conn(s, "J1", 2, ["TOUCH", GND], value="To carrier J7",
         fp="Connector_JST:JST_SH_BM02B-SRSS-TB_1x02-1MP_P1.00mm_Vertical")
    s.part("TP1", "Connector:TestPoint", "GND", "TestPoint:TestPoint_Pad_D1.0mm", {"1": GND}).in_bom = False
    return d


ALL = {"carrier": carrier, "power": power, "front_sensor": front_sensor, "front_touch": front_touch}
