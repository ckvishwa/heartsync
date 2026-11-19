"""
heartsync carrier board v0.1 - full circuit as code (SKiDL)

Run:   python heartsync_carrier.py
Makes: heartsync_carrier.net  (import into the KiCad PCB editor: File > Import > Netlist)
       heartsync_carrier_bom.csv

Board: 70 x 45 mm, 2 layers. ESP32-S3-WROOM-1-N16R8 + 2x MAX98357A + DRV2605L + BMI270 +
MAX17048 + TLV62569 3.3 V buck + USB ESD + 1.8 V level shifter for the SIM7080G.
Bought modules (power bank / USB-PD, Qi2 TX, SIM7080G) and the front parts (OLED, mic,
light sensor, touch strip, buttons, mute switch) connect through JST-SH cables.

Pin numbers come from the official KiCad 10 symbols (RF_Module:ESP32-S3-WROOM-1,
Audio:MAX98357A, Driver:DRV2605LDGS, Logic_LevelTranslator:TXS0102DCU,
Power_Protection:USBLC6-2SC6, Regulator_Switching:TLV62569DBV, Transistor_FET:BSS138),
the MAX17048 datasheet (TDFN-8) and a BMI270 LGA-14 symbol. Check each against its
datasheet before ordering boards.
"""
import csv
from skidl import *  # noqa: F401,F403  (provides Part, Pin, Net, NC, SKIDL, ERC, generate_netlist)

PASSIVE, PWR_IN, BIDIR = Pin.types.PASSIVE, Pin.types.PWRIN, Pin.types.BIDIR

FP_R = "Resistor_SMD:R_0603_1608Metric"
FP_C = "Capacitor_SMD:C_0603_1608Metric"
FP_C_BIG = "Capacitor_SMD:C_0805_2012Metric"
FP_JST = "Connector_JST:JST_SH_SM{n:02d}B-SRSS-TB_1x{n:02d}-1MP_P1.00mm_Horizontal"

BOM = []


def part(ref, name, value, fp, pins, mpn="", note=""):
    p = Part(tool=SKIDL, name=name, ref=ref, tag=ref, value=value, footprint=fp,
             pins=[Pin(num=n, name=nm, func=PASSIVE) for n, nm in pins])
    BOM.append({"ref": ref, "value": value, "footprint": fp, "mpn": mpn, "note": note})
    return p


def two(ref, value, fp, a, b, mpn="", note=""):
    p = part(ref, ref[0], value, fp, [(1, "1"), (2, "2")], mpn, note)
    a += p[1]
    b += p[2]
    return p


def R(ref, value, a, b, note=""):
    return two(ref, value, FP_R, a, b, note=note)


def C(ref, value, a, b, big=False, note=""):
    return two(ref, value, FP_C_BIG if big else FP_C, a, b, note=note)


def jst(ref, nets, label):
    n = len(nets)
    p = part(ref, "CONN_%d" % n, label, FP_JST.format(n=n), [(i + 1, str(i + 1)) for i in range(n)],
             "JST SM%02dB-SRSS-TB" % n, label)
    for i, net in enumerate(nets):
        if net is None:
            p[i + 1] += NC
        else:
            net += p[i + 1]
    return p


# ---------------------------------------------------------------- nets
GND, P5V, P3V3, VBAT, VDD_EXT = Net("GND"), Net("+5V"), Net("+3V3"), Net("VBAT"), Net("VDD_EXT_1V8")
MIC_3V3 = Net("MIC_3V3")
SDA, SCL, ALERT = Net("I2C_SDA"), Net("I2C_SCL"), Net("ALERT_N")
USB_DP, USB_DM = Net("USB_D+"), Net("USB_D-")
I2S_BCLK, I2S_LRCLK, I2S_DIN, AMP_SD = Net("I2S_BCLK"), Net("I2S_LRCLK"), Net("I2S_DIN"), Net("AMP_SD")
SD_L, SD_R = Net("AMP_L_SDMODE"), Net("AMP_R_SDMODE")
MIC_SCK, MIC_WS, MIC_SD = Net("MIC_SCK"), Net("MIC_WS"), Net("MIC_SD")
OLED_SCK, OLED_MOSI, OLED_CS, OLED_DC, OLED_RST = (Net("OLED_SCK"), Net("OLED_MOSI"), Net("OLED_CS"),
                                                   Net("OLED_DC"), Net("OLED_RST"))
TOUCH1, TOUCH2, TOUCH3 = Net("TOUCH1"), Net("TOUCH2"), Net("TOUCH3")
BTN_ADC, BTN_PWR, IMU_INT, MUTE_SENSE = Net("BTN_ADC"), Net("BTN_PWR_N"), Net("IMU_INT"), Net("MUTE_SENSE")
ESP_TX, ESP_RX, SIM_TXD, SIM_RXD = Net("ESP_TX"), Net("ESP_RX"), Net("SIM_TXD_1V8"), Net("SIM_RXD_1V8")
PWRKEY_CTL, SIM_PWRKEY = Net("SIM_PWRKEY_CTL"), Net("SIM_PWRKEY")
EN, BOOT, TXD0, RXD0, FB, SW = Net("ESP_EN"), Net("ESP_BOOT"), Net("UART0_TX"), Net("UART0_RX"), Net("REG_FB"), Net("REG_SW")
SPKL_P, SPKL_N, SPKR_P, SPKR_N = Net("SPK_L+"), Net("SPK_L-"), Net("SPK_R+"), Net("SPK_R-")
LRA_P, LRA_N, DRV_REG = Net("LRA+"), Net("LRA-"), Net("DRV_REG")

# ---------------------------------------------------------------- ESP32-S3-WROOM-1-N16R8
esp_pins = [(1, "GND"), (2, "3V3"), (3, "EN"), (4, "IO4"), (5, "IO5"), (6, "IO6"), (7, "IO7"),
            (8, "IO15"), (9, "IO16"), (10, "IO17"), (11, "IO18"), (12, "IO8"), (13, "USB_D-"),
            (14, "USB_D+"), (15, "IO3"), (16, "IO46"), (17, "IO9"), (18, "IO10"), (19, "IO11"),
            (20, "IO12"), (21, "IO13"), (22, "IO14"), (23, "IO21"), (24, "IO47"), (25, "IO48"),
            (26, "IO45"), (27, "IO0"), (28, "IO35"), (29, "IO36"), (30, "IO37"), (31, "IO38"),
            (32, "IO39"), (33, "IO40"), (34, "IO41"), (35, "IO42"), (36, "RXD0"), (37, "TXD0"),
            (38, "IO2"), (39, "IO1"), (40, "GND"), (41, "GND_EP")]
U1 = part("U1", "ESP32-S3-WROOM-1", "ESP32-S3-WROOM-1-N16R8", "RF_Module:ESP32-S3-WROOM-1",
          esp_pins, "ESP32-S3-WROOM-1-N16R8", "Antenna end flush with the board top edge")
GND += U1[1], U1[40], U1[41]
P3V3 += U1[2]
EN += U1[3]
TOUCH3 += U1[4]          # IO4
BTN_ADC += U1[5]         # IO5
BTN_PWR += U1[6]         # IO6
IMU_INT += U1[7]         # IO7
I2S_BCLK += U1[8]        # IO15
I2S_LRCLK += U1[9]       # IO16
I2S_DIN += U1[10]        # IO17
AMP_SD += U1[11]         # IO18
SDA += U1[12]            # IO8
USB_DM += U1[13]
USB_DP += U1[14]
SCL += U1[17]            # IO9
OLED_CS += U1[18]        # IO10
OLED_MOSI += U1[19]      # IO11
OLED_SCK += U1[20]       # IO12
OLED_DC += U1[21]        # IO13
OLED_RST += U1[22]       # IO14
ALERT += U1[23]          # IO21
PWRKEY_CTL += U1[24]     # IO47
MUTE_SENSE += U1[25]     # IO48
BOOT += U1[27]           # IO0
MIC_SCK += U1[31]        # IO38
MIC_WS += U1[32]         # IO39
MIC_SD += U1[33]         # IO40
ESP_TX += U1[34]         # IO41
ESP_RX += U1[35]         # IO42
RXD0 += U1[36]
TXD0 += U1[37]
TOUCH2 += U1[38]         # IO2
TOUCH1 += U1[39]         # IO1
for n in (15, 16, 26, 28, 29, 30):   # IO3, IO46, IO45 strapping; IO35-37 octal PSRAM
    U1[n] += NC

C("C1", "10uF", P3V3, GND, big=True, note="ESP32 bulk, next to pin 2")
C("C2", "100nF", P3V3, GND, note="ESP32 decoupling")
R("R1", "10k", P3V3, EN, note="EN pull-up")
C("C3", "1uF", EN, GND, note="EN delay")
R("R2", "10k", P3V3, BOOT, note="IO0 pull-up")
sw_pins = [(1, "1"), (2, "2")]
SW1 = part("SW1", "SW_PUSH", "RESET", "Button_Switch_SMD:SW_SPST_TL3342", sw_pins, "TL3342")
EN += SW1[1]; GND += SW1[2]
SW2 = part("SW2", "SW_PUSH", "BOOT", "Button_Switch_SMD:SW_SPST_TL3342", sw_pins, "TL3342")
BOOT += SW2[1]; GND += SW2[2]

# ---------------------------------------------------------------- 3.3 V buck (TLV62569DBV)
U2 = part("U2", "TLV62569DBV", "TLV62569DBV", "Package_TO_SOT_SMD:SOT-23-5",
          [(1, "EN"), (2, "GND"), (3, "SW"), (4, "VIN"), (5, "FB")], "TLV62569DBVR", "2 A buck, 5 V -> 3.3 V")
P5V += U2[1], U2[4]
GND += U2[2]
SW += U2[3]
FB += U2[5]
two("L1", "2.2uH", "Inductor_SMD:L_Bourns-SRN4018", SW, P3V3, "SRN4018-2R2M", "2.2 uH, >= 2 A")
R("R3", "453k 1%", P3V3, FB, note="FB top: Vout = 0.6 V x (1 + 453k/100k) = 3.32 V")
R("R4", "100k 1%", FB, GND, note="FB bottom")
C("C4", "10uF", P5V, GND, big=True, note="Buck input")
C("C5", "22uF", P3V3, GND, big=True, note="Buck output")
C("C6", "22uF", P5V, GND, big=True, note="5 V bulk at the power connector")

# ---------------------------------------------------------------- USB ESD (USBLC6-2SC6)
U3 = part("U3", "USBLC6-2SC6", "USBLC6-2SC6", "Package_TO_SOT_SMD:SOT-23-6",
          [(1, "I/O1"), (2, "GND"), (3, "I/O2"), (4, "I/O2"), (5, "VBUS"), (6, "I/O1")], "USBLC6-2SC6")
USB_DM += U3[1], U3[6]
USB_DP += U3[3], U3[4]
GND += U3[2]
P5V += U3[5]

# ---------------------------------------------------------------- 2x MAX98357A (stereo)
amp_pins = [(1, "DIN"), (2, "GAIN_SLOT"), (3, "GND"), (4, "SD_MODE"), (5, "NC"), (6, "NC"),
            (7, "VDD"), (8, "VDD"), (9, "OUTP"), (10, "OUTN"), (11, "GND"), (12, "NC"),
            (13, "NC"), (14, "LRCLK"), (15, "GND"), (16, "BCLK"), (17, "PAD")]
for ref, sd, op, on, cref in (("U4", SD_L, SPKL_P, SPKL_N, 7), ("U5", SD_R, SPKR_P, SPKR_N, 9)):
    a = part(ref, "MAX98357A", "MAX98357A", "Package_DFN_QFN:TQFN-16-1EP_3x3mm_P0.5mm_EP1.23x1.23mm",
             amp_pins, "MAX98357AETE+", "Left amp" if ref == "U4" else "Right amp")
    I2S_DIN += a[1]
    a[2] += NC                      # GAIN_SLOT open = 9 dB
    GND += a[3], a[11], a[15], a[17]
    sd += a[4]
    for n in (5, 6, 12, 13):
        a[n] += NC
    P5V += a[7], a[8]
    op += a[9]
    on += a[10]
    I2S_LRCLK += a[14]
    I2S_BCLK += a[16]
    C("C%d" % cref, "10uF", P5V, GND, big=True, note=ref + " bulk")
    C("C%d" % (cref + 1), "100nF", P5V, GND, note=ref + " decoupling")
# SD_MODE from one GPIO: high -> U4 left (>1.4 V), U5 right (0.77-1.4 V); low -> both shut down
R("R5", "10k", AMP_SD, SD_L, note="U4 SD_MODE: about 3.0 V = left")
R("R6", "68k", AMP_SD, SD_R, note="U5 SD_MODE divider top")
R("R7", "47k", SD_R, GND, note="U5 SD_MODE divider bottom: about 1.0-1.1 V = right")

# ---------------------------------------------------------------- DRV2605L haptic
U6 = part("U6", "DRV2605LDGS", "DRV2605LDGS", "Package_SO:TSSOP-10_3x3mm_P0.5mm",
          [(1, "REG"), (2, "SCL"), (3, "SDA"), (4, "IN/TRIG"), (5, "EN"), (6, "VDD/NC"),
           (7, "OUT+"), (8, "GND"), (9, "OUT-"), (10, "VDD")], "DRV2605LDGSR", "LRA mode, EN tied high")
DRV_REG += U6[1]
SCL += U6[2]
SDA += U6[3]
GND += U6[4], U6[8]
P3V3 += U6[5], U6[6], U6[10]
LRA_P += U6[7]
LRA_N += U6[9]
C("C11", "1uF", DRV_REG, GND, note="DRV2605L REG")
C("C12", "1uF", P3V3, GND, note="DRV2605L VDD")

# ---------------------------------------------------------------- BMI270 IMU (I2C, addr 0x68)
U7 = part("U7", "BMI270", "BMI270", "Package_LGA:Bosch_LGA-14_3x2.5mm_P0.5mm",
          [(1, "SDO"), (2, "ASDX"), (3, "ASCX"), (4, "INT1"), (5, "VDDIO"), (6, "GNDIO"), (7, "GND"),
           (8, "VDD"), (9, "INT2"), (10, "OCSB"), (11, "OSDO"), (12, "CSB"), (13, "SCX"), (14, "SDX")],
          "BMI270", "CSB high = I2C, SDO low = 0x68")
GND += U7[1], U7[6], U7[7]
for n in (2, 3, 9, 10, 11):
    U7[n] += NC
IMU_INT += U7[4]
P3V3 += U7[5], U7[8], U7[12]
SCL += U7[13]
SDA += U7[14]
C("C13", "100nF", P3V3, GND, note="BMI270 VDD")
C("C14", "100nF", P3V3, GND, note="BMI270 VDDIO")

# ---------------------------------------------------------------- MAX17048 fuel gauge
U8 = part("U8", "MAX17048", "MAX17048G+T10", "Package_DFN_QFN:TDFN-8-1EP_2x2mm_P0.5mm_EP0.8x1.2mm",
          [(1, "CTG"), (2, "CELL"), (3, "VDD"), (4, "GND"), (5, "ALRT"), (6, "QSTRT"), (7, "SCL"),
           (8, "SDA"), (9, "EP")], "MAX17048G+T10", "Powered from and sensing the cell")
GND += U8[1], U8[4], U8[6], U8[9]
VBAT += U8[2], U8[3]
ALERT += U8[5]
SCL += U8[7]
SDA += U8[8]
C("C15", "100nF", VBAT, GND, note="MAX17048 VDD")

# ---------------------------------------------------------------- I2C + alert pull-ups
R("R8", "4.7k", P3V3, SDA, note="I2C pull-up")
R("R9", "4.7k", P3V3, SCL, note="I2C pull-up")
R("R10", "10k", P3V3, ALERT, note="Shared open-drain alert")

# ---------------------------------------------------------------- SIM7080G: 1.8 V level shift + PWRKEY
U9 = part("U9", "TXS0102DCU", "TXS0102DCU", "Package_SO:VSSOP-8_2.3x2mm_P0.5mm",
          [(1, "B2"), (2, "GND"), (3, "VCCA"), (4, "A2"), (5, "A1"), (6, "OE"), (7, "VCCB"), (8, "B1")],
          "TXS0102DCUR", "A side 1.8 V (SIM), B side 3.3 V (ESP32)")
ESP_TX += U9[1]          # B2 <- ESP TX
GND += U9[2]
VDD_EXT += U9[3], U9[6]  # VCCA and OE from the SIM's 1.8 V
SIM_RXD += U9[4]         # A2 -> SIM RXD
SIM_TXD += U9[5]         # A1 <- SIM TXD
P3V3 += U9[7]
ESP_RX += U9[8]          # B1 -> ESP RX
C("C16", "100nF", VDD_EXT, GND, note="TXS0102 VCCA")
C("C17", "100nF", P3V3, GND, note="TXS0102 VCCB")
Q1 = part("Q1", "BSS138", "BSS138", "Package_TO_SOT_SMD:SOT-23", [(1, "G"), (2, "S"), (3, "D")],
          "BSS138", "Pulls SIM PWRKEY low")
GATE = Net("Q1_GATE")
GATE += Q1[1]; GND += Q1[2]; SIM_PWRKEY += Q1[3]
R("R11", "1k", PWRKEY_CTL, GATE, note="Gate series")
R("R12", "100k", GATE, GND, note="Gate pull-down, PWRKEY idle at boot")

# ---------------------------------------------------------------- mic mute + button lines
R("R13", "100k", MIC_3V3, GND, note="Mic rail reads low when the mute switch is open")
R("R14", "1k", MIC_3V3, MUTE_SENSE, note="Mute sense to IO48")
C("C18", "100nF", MIC_3V3, GND, note="Mic rail")
R("R15", "10k", P3V3, BTN_ADC, note="Button ladder top (ladder resistors on the button strip)")
R("R16", "10k", P3V3, BTN_PWR, note="Power button pull-up")
C("C19", "100nF", BTN_PWR, GND, note="Power button debounce")

# ---------------------------------------------------------------- connectors (JST-SH 1.0 mm)
jst("J1", [P5V, P5V, GND, GND, USB_DP, USB_DM, ALERT], "POWER: 5V,5V,GND,GND,D+,D-,ALERT (power bank / USB-C module)")
jst("J2", [VBAT, GND], "BATTERY SENSE: VBAT, GND (cell, for fuel gauge and SIM)")
jst("J3", [VBAT, GND, SIM_TXD, SIM_RXD, SIM_PWRKEY, VDD_EXT], "SIM7080G: VBAT,GND,TXD,RXD,PWRKEY,VDD_EXT")
jst("J4", [SPKL_P, SPKL_N], "SPEAKER LEFT")
jst("J5", [SPKR_P, SPKR_N], "SPEAKER RIGHT")
jst("J6", [LRA_P, LRA_N], "HAPTIC LRA")
jst("J7", [TOUCH1, TOUCH2, TOUCH3, GND], "TOUCH STRIP")
jst("J8", [MIC_3V3, GND, MIC_SCK, MIC_WS, MIC_SD], "MIC INMP441: 3V3(muted),GND,SCK,WS,SD")
jst("J9", [P3V3, MIC_3V3], "MUTE SWITCH: 3V3 out, mic rail back")
jst("J10", [P3V3, GND, SDA, SCL], "LIGHT SENSOR VEML7700")
jst("J11", [P3V3, GND, OLED_SCK, OLED_MOSI, OLED_CS, OLED_DC, OLED_RST], "OLED SPI")
jst("J12", [P3V3, GND, BTN_ADC, BTN_PWR], "BUTTON STRIP: 3V3,GND,LADDER,POWER")

# ---------------------------------------------------------------- test points
for ref, net, label in (("TP1", P5V, "+5V"), ("TP2", P3V3, "+3V3"), ("TP3", GND, "GND"),
                        ("TP4", VBAT, "VBAT"), ("TP5", TXD0, "UART0 TX"), ("TP6", RXD0, "UART0 RX"),
                        ("TP7", VDD_EXT, "1V8")):
    tp = part(ref, "TestPoint", label, "TestPoint:TestPoint_Pad_D1.0mm", [(1, "1")])
    net += tp[1]

if __name__ == "__main__":
    ERC()
    generate_netlist(file_="heartsync_carrier.net")
    with open("heartsync_carrier_bom.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["ref", "value", "footprint", "mpn", "note"])
        w.writeheader()
        w.writerows(BOM)
    print("Parts: %d. Wrote heartsync_carrier.net and heartsync_carrier_bom.csv" % len(BOM))
