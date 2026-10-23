"""Source-grounded expectations fixed before implementing the query engine.

Self-authored development/holdout set, not an independent external benchmark.
Expected numbers are literal transcriptions, never copied from program output.
"""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
cases=[]
def q(cat,split,family,question,evidence, facts=None,status="answered",contains=None):
    cases.append(dict(id=f"{cat}-{split}-{len(cases)+1:02}",category=cat,split=split,
        family=family,kind="query",question=question,expected=dict(status=status,
        evidence=evidence,facts=facts or {},contains=contains or [])))
def ck(split,family,point,rule,status,evidence,value=None):
    cases.append(dict(id=f"rules-{split}-{len(cases)+1:02}",category="rules",split=split,
        family=family,kind="check",point=point,expected=dict(rule=rule,rule_status=status,
        evidence=evidence,value=value)))

# Parameter facts, five development and five held-out families.
q("parameters","dev","feedback-overview","反馈参考电压 VFB 是多少？",["reference"],{"vfb-25":{"minimum":686,"typical":696,"maximum":703,"unit":"mV"}})
q("parameters","dev","uvlo-on-values","欠压启动阈值的范围是什么？",["uvlo"],{"uvlo-on":{"minimum":3.8,"typical":4.25,"maximum":4.5,"unit":"V"}})
q("parameters","dev","oscillator-range","开关频率允许的范围？",["oscillator"],{"fosc-range":{"minimum":35,"typical":None,"maximum":500,"unit":"kHz"}})
q("parameters","dev","min-pulse-12","tMIN 在 12 V 时的值",["pwm"],{"tmin-12":{"minimum":None,"typical":200,"maximum":400,"unit":"ns"}})
q("parameters","dev","recommended-voltage","推荐输入电压上下限",["recommended"],{"rec-vdd":{"minimum":4.5,"maximum":52,"unit":"V"}})
q("parameters","holdout","gate-source-values","Isrc 栅极拉高电流的数据",["gate"],{"gate-source":{"minimum":125,"typical":300,"maximum":None,"unit":"mA"}})
q("parameters","holdout","quiescent-values","Iqq 静态电流的典型值与最大值",["quiescent"],{"iqq":{"minimum":None,"typical":1.5,"maximum":3,"unit":"mA"}})
q("parameters","holdout","amplifier-bandwidth","GBWP 单位增益带宽",["amplifier"],{"gbwp":{"minimum":1.5,"typical":3,"maximum":None,"unit":"MHz"}})
q("parameters","holdout","overcurrent-duty-column","OCDF 过流占空比 2% 位于哪一列",["current-limit"],{"ocdf":{"minimum":None,"typical":None,"maximum":2,"unit":"%"}})
q("parameters","holdout","gate-sink-values","Isnk 栅极拉低电流参数",["gate"],{"gate-sink":{"minimum":200,"typical":300,"maximum":None,"unit":"mA"}})

q("conditions","dev","reference-full-temp","VFB 在 -40 到 125 度的上下限",["reference"],{"vfb-125":{"minimum":679,"maximum":710,"conditions":"4.5 V < VDD < 52 V；−40 °C < TA < 125 °C"}})
q("conditions","dev","ilim-cold-range","低温时 VILIM 最小值是多少？",["current-limit"],{"ilim-40":{"minimum":55,"maximum":140}})
q("conditions","dev","duty-100-condition","100 kHz 下最大占空比 DMAX",["pwm"],{"dmax-100":{"minimum":93,"typical":95,"maximum":None}})
q("conditions","dev","pulse-30-condition","30 V 供电下的最小脉宽 tMIN",["pwm"],{"tmin-30":{"typical":100,"maximum":200}})
q("conditions","dev","frequency-line-high","12 V 以上的频率线性调整率",["line-regulation"],{"line-high":{"minimum":-9,"typical":None,"maximum":0}})
q("conditions","holdout","gate-voltage-condition","VGATE 的测试条件是什么",["gate"],{"gate-voltage":{"conditions":"VGATE=VDD−VGDRV；12 V < VDD < 52 V","minimum":6,"maximum":10}})
q("conditions","holdout","reference-comp-condition","COMP=FB 的 VFB 那一行",["reference"],{"vfb-comp":{"minimum":689,"maximum":702,"conditions":"COMP=FB；TA=25 °C；其余默认条件见表头"}})
q("conditions","holdout","comp-source-condition","ICOMP(src) 输出源电流适用条件",["amplifier"],{"comp-source":{"minimum":100,"typical":250,"conditions":"VFB=0.6 V；COMP=1 V"}})
q("conditions","holdout","comp-sink-condition","ICOMP(snk) 输出灌电流的条件",["amplifier"],{"comp-sink":{"minimum":1,"typical":2.5,"conditions":"VFB=1.2 V；COMP=1 V"}})
q("conditions","holdout","frequency-line-low","低于 12 V 的 Frequency line regulation",["line-regulation"],{"line-low":{"minimum":-20,"typical":None,"maximum":0}})

q("traps","dev","low-input-uvlo","4.3 V 能正常工作吗？",["recommended"],status="answered",contains=["不满足"])
q("traps","dev","typical-is-not-limit","VFB 的 696 mV 是否是保证值？",["reference"],{"vfb-85":{"typical":696,"minimum":679,"maximum":708}},contains=["典型值"])
q("traps","dev","negative-abs-input","VDD 绝对最大额定值是否允许 -0.3 V",["abs"],{"abs-vdd":{"minimum":-0.3,"maximum":52}},contains=["应力"])
q("traps","dev","output-current-controller","最大输出电流是否保证 2.5 A",["application-boundary"],status="evidence_only",contains=["控制器"])
q("traps","dev","uvlo-off-missing-limits","VUVLO(off) 的最小最大值有给出吗",["uvlo"],{"uvlo-off":{"minimum":None,"typical":4.05,"maximum":None}})
q("traps","holdout","min-pulse-typ-column","最小脉宽的 200 ns 是最小值吗",["pwm"],{"tmin-12":{"minimum":None,"typical":200,"maximum":400}})
q("traps","holdout","duty-typ-column","最大占空比 95% 能当保证下限吗",["pwm"],{"dmax-100":{"minimum":93,"typical":95,"maximum":None}})
q("traps","holdout","junction-not-ambient","环境温度 25 °C 能直接作为结温检查吗",["recommended"],status="needs_information",contains=["环境温度","结温"])
q("traps","holdout","gbwp-max-absent","GBWP 的 3 MHz 是最大值吗",["amplifier"],{"gbwp":{"minimum":1.5,"typical":3,"maximum":None}})
q("traps","holdout","design-not-production","仅由设计保证是生产测试过了吗",["design-note"],status="evidence_only",contains=["未进行生产测试"])

q("citations","dev","overcurrent-restart-mechanism","过流后如何恢复",["overcurrent-recovery"],status="evidence_only",contains=["软启动"])
q("citations","dev","timing-equations-location","RC 频率公式在哪里",["timing"],status="evidence_only",contains=["0.105"])
q("citations","dev","sync-requirements","外部时钟同步有什么要求",["sync"],status="evidence_only",contains=["20 ns"])
q("citations","dev","softstart-process","软启动原理是什么",["softstart-mechanism"],status="evidence_only",contains=["电容"])
q("citations","dev","pin-rc-wiring","RC 引脚应该怎么接线",["pins"],status="evidence_only",contains=["定时"])
q("citations","holdout","uvlo-mechanism-hysteresis","欠压工作原理中为什么有迟滞",["uvlo-mechanism"],status="evidence_only",contains=["4.3"])
q("citations","holdout","ramp-source-location","VRMP 斜坡幅度的原文",["ramp"],{"ramp":{"typical":"VDD / 10","minimum":None,"maximum":None}})
q("citations","holdout","softstart-internal-resistors","RSS(chg) 内部充电电阻在哪页",["softstart-values"],{"rss-charge":{"minimum":65,"typical":105,"maximum":170}})
q("citations","holdout","error-input-bias-location","IIB 输入偏置电流的表格",["amplifier"],{"iib":{"minimum":None,"typical":100,"maximum":250}})
q("citations","holdout","sense-pin-role","ISNS 管脚作用和采样电阻接线",["pins"],status="evidence_only",contains=["采样电阻"])

ck("dev","vdd-too-low",{"vdd":"4.3 V"},"vdd","violated",["recommended"])
ck("dev","timing-current-valid",{"vdd":"12 V","resistance":"200 kΩ","capacitance":"470 pF"},"rc_current","satisfied",["timing"],60)
ck("dev","frequency-too-high",{"frequency":"600 kHz"},"frequency","violated",["oscillator"])
ck("dev","millivolt-conversion",{"vdd":"3000 mV"},"vdd","violated",["recommended"],3)
ck("dev","ambient-only-input",{"ambient_temperature":"25 °C"},"tj","needs_information",["recommended"])
ck("holdout","junction-too-high",{"tj":"126 °C"},"tj","violated",["recommended"],126)
ck("holdout","timing-current-exact-boundary",{"vdd":"48 V","resistance":"64 kΩ"},"rc_current","satisfied",["timing"],750)
ck("holdout","nominal-frequency-estimate",{"resistance":"68.1 kΩ","capacitance":"470 pF"},"rc_frequency","estimated",["timing"],297.55395769080275)
ck("holdout","resistance-missing-unit",{"vdd":"12 V","resistance":"200"},"rc_current","invalid",["timing"])
ck("holdout","negative-capacitance",{"resistance":"200 kΩ","capacitance":"-1 nF"},"rc_frequency","invalid",["timing"])

for split,items in {
 "dev":[("other-buck","LM2596 的输入范围？","unsupported"),("curve-read","请读取图 21 的曲线数值","unsupported"),("complete-design","帮我设计完整电路","unsupported"),("pcb-guarantee","确认整个 PCB 一定稳定","unsupported"),("unrelated-weather","今天北京天气怎么样","not_found")],
 "holdout":[("other-mcu","STM32F103 的参考电压","unsupported"),("curve-interpolation","根据曲线插值 150 kHz 的最小导通时间","unsupported"),("generate-bom","生成完整 BOM 和原理图","unsupported"),("thermal-curve-digitize","从温度曲线读取精确值","unsupported"),("unrelated-recipe","教我做红烧茄子","not_found")]
}.items():
 for family,question,status in items:q("unsupported",split,family,question,[],status=status)

assert len(cases)==60
assert sum(c["split"]=="dev" for c in cases)==30
assert len({c["family"] for c in cases})==60
payload=dict(description="自建小型验证集，预先定义期望；不是独立第三方基准。",source_revision="SLUS659G",
 source_sha256="a3e23ec7367038ecd8f6ddbfc38392fcb87d997352eabb715b573de538a76240",
 methodology="数值独立抄自 PDF；每类 5 个开发案例、5 个留出案例；不同改写不跨组。",
 corrections=[dict(case="rules-holdout-48",old_value=297.5580817,new_value=297.55395769080275,
 reason="首轮留出发现预期值算术错误。独立用 1/(68100×470e-12×0.105)/1000 验算并用 Fraction 精确有理数复核；未修改计算引擎。首轮结果保存在 reports/holdout-first.json。")],cases=cases)
(ROOT/"data/benchmark.json").write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n")
print("Prepared 60 source-grounded cases (30 dev / 30 holdout).")
