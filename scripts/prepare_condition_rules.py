"""Explicit transcription of Rev.G pp.4–6 row conditions and inherited headers.

Not a generic expression parser. Strict inequalities follow the printed table.
TA=TJ is a test setup, never an ambient-to-junction temperature conversion.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def eq(field, value, label):return dict(field=field, op="eq", value=value, label=label)
def between(field, low, high, label):return dict(field=field, op="open", low=low, high=high, label=label)
temperature = between("test_temperature", -40, 85, "−40 °C < TA = TJ < 85 °C（表头）")
vdd = eq("vdd", 12, "VDD = 12 V（表头）")
frequency = eq("frequency", 100000, "fOSC = 100 kHz（表头）")
wide_vdd = between("vdd", 4.5, 52, "4.5 V < VDD < 52 V")
rules = {}
def row(ids, *overrides, omit=(), notes=()):
    terms = {t["field"]: t for t in (temperature, vdd, frequency) if t["field"] not in omit}
    terms.update({t["field"]: t for t in overrides})
    for id in ids.split():rules[id] = dict(constraints=list(terms.values()), notes=list(notes))

row("vfb-comp", eq("test_temperature",25,"TA = TJ = 25 °C"), eq("comp_equals_fb",True,"COMP = FB"))
row("vfb-25", wide_vdd, eq("test_temperature",25,"TA = TJ = 25 °C"))
row("vfb-85", wide_vdd)
row("vfb-125", wide_vdd, between("test_temperature",-40,125,"−40 °C < TA = TJ < 125 °C"))
row("gate-source gate-sink rss-charge rss-discharge ss-reset ocdf ilim-reset kpwm iib aol gbwp")
row("gate-voltage line-high", between("vdd",12,52,"12 V < VDD < 52 V"))
row("iqq",wide_vdd,eq("frequency",300000,"fOSC = 300 kHz"),eq("driver_switching",False,"驱动不切换"))
row("uvlo-on",between("test_temperature",-40,125,"−40 °C < TA = TJ < 125 °C"), omit=("vdd",), notes=("VUVLO(on) 是被测的电压扫描阈值，不能用表头 12 V 把阈值本身筛掉。",))
row("uvlo-off uvlo-hyst",omit=("vdd",),notes=("此项由 VDD 扫描测得；仅匹配温度与频率条件，不用表头 12 V 替代扫描阈值或验证扫描过程。",))
row("ilim-0",wide_vdd,between("test_temperature",0,125,"0 °C < TA = TJ < 125 °C"))
row("ilim-40",wide_vdd,between("test_temperature",-40,125,"−40 °C < TA = TJ < 125 °C"))
for id,resistance in [("fosc-100",200000),("fosc-300",68100)]:
    row(id,eq("resistance",resistance,f"RRC = {resistance/1000:g} kΩ"),eq("capacitance",470e-12,"CRC = 470 pF"),omit=("frequency",),notes=("fOSC 是该行的测量结果，按指定 RRC/CRC 匹配，不把它当独立的频率输入条件。",))
row("line-low",between("vdd",4.5,12,"4.5 V < VDD < 12 V"))
row("ramp",wide_vdd)
row("tmin-12")
row("tmin-30",eq("vdd",30,"VDD = 30 V"))
row("dmax-100",eq("load_capacitance",470e-12,"负载电容 CL = 470 pF；不是定时电容 CRC"))
row("dmax-300",eq("frequency",300000,"fOSC = 300 kHz"),eq("load_capacitance",470e-12,"负载电容 CL = 470 pF；不是定时电容 CRC"))
row("comp-source",eq("vfb",.6,"VFB = 0.6 V"),eq("comp",1,"COMP = 1 V"))
row("comp-sink",eq("vfb",1.2,"VFB = 1.2 V"),eq("comp",1,"COMP = 1 V"))
for id in "abs-vdd abs-rc-fb abs-ss abs-comp abs-gdrv abs-tj abs-lead rec-vdd rec-tj fosc-range".split():
    rules[id] = dict(constraints=[], limit=True, notes=["此行是额定值或范围限制，不是测试条件行；不能用测试条件筛选替代工作条件检查。"])
out = dict(source_sha256="a3e23ec7367038ecd8f6ddbfc38392fcb87d997352eabb715b573de538a76240",
           review="Codex transcription of pp.4–6 and inherited table headers; not independently reviewed.",
           method="Row overrides replace matching header dimensions. TA=TJ requires an explicitly selected test-temperature input. Other missing conditions stay unknown.",rules=rules)
(ROOT/"data/curated/condition_rules.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
print(f"Prepared {len(rules)} explicit condition records.")
