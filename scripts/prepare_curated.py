"""Explicit transcription of Rev G pp.4-6, visually checked against the PDF.

This file is reviewed source data, not an automatic PDF parser. Empty cells are
None. Re-run to reproduce curated JSON; ingestion separately preserves raw output.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/curated"
OUT.mkdir(parents=True, exist_ok=True)

evidence = []
def ev(id, page, box, title, aliases, summary, context_boxes=()):
    evidence.append(dict(id=id, page=page, printed_page=str(page), bbox=box,
                         title=title, aliases=aliases, summary=summary,
                         context_bboxes=list(context_boxes), curated=True))

DEFAULT5 = [[54, 74, 558, 114]]
DEFAULT6 = [[54, 74, 558, 119]]
FN1 = [54, 546, 558, 558]
ev("abs",4,[54,98,558,264],"6.1 绝对最大额定值",["绝对最大","absolute maximum","stress ratings","引脚极限"],"绝对最大额定值描述应力限制，不代表在这些条件下保证功能正常。")
ev("recommended",4,[54,395,558,462],"6.3 推荐工作条件",["输入电压","供电范围","VDD","VIN","工作温度","结温","TJ","recommended operating"],"推荐 VDD 为 4.5–52 V，推荐结温 TJ 为 −40–125 °C。范围内只表示满足该项限制。")
ev("reference",5,[54,114,558,181],"6.5 反馈参考电压 VFB",["VFB","反馈电压","反馈参考","基准电压","reference","Feedback voltage","温漂"],"VFB 的典型值是 696 mV；上下限取决于测试条件，必须逐行读取。",DEFAULT5)
ev("gate",5,[54,181,558,233],"6.5 栅极驱动",["GDRV","VGATE","Isrc","Isnk","栅极","驱动电流","gate driver","拉电流","灌电流"],"驱动输出面向外部 P 沟道 MOSFET；拉高和拉低电流的最小值不同，表格未给最大值。",DEFAULT5)
ev("quiescent",5,[54,233,558,260],"6.5 静态电流 Iqq",["Iqq","静态电流","静态功耗","quiescent","待机电流"],"Iqq 的 1.5 mA 典型值、3.0 mA 最大值适用于驱动不切换等指定测试条件。",DEFAULT5)
ev("uvlo",5,[54,260,558,313],"6.5 欠压锁定 UVLO",["UVLO","欠压","启动阈值","关断阈值","迟滞","turn-on","turn-off","hysteresis"],"启动阈值典型为 4.25 V；推荐输入下限仍为 4.5 V。关断阈值只列典型值 4.05 V。",DEFAULT5)
ev("softstart-values",5,[54,313,558,384],"6.5 软启动参数",["RSS","RSS(chg)","RSS(dchg)","VSSRST","软启动电阻","复位阈值","soft start resistance"],"充电电阻典型为 105 kΩ，放电电阻典型为 305 kΩ；这些是内部参数，具有表内上下限。",DEFAULT5)
ev("current-limit",5,[54,384,558,450],"6.5 过流保护阈值",["VILIM","ILIM","过流阈值","过流门限","电流限制","current limit","OCDF","过流占空比"],"VILIM 是采样压降阈值而不是输出电流额定值；低温行下限为 55 mV。OCDF 的 2% 在 MAX 列，且仅由设计保证。",DEFAULT5+[FN1])
ev("oscillator",5,[54,450,558,502],"6.5 振荡器频率",["fosc","fsw","振荡频率","开关频率","频率范围","oscillator frequency","35kHz","500kHz"],"振荡频率范围为 35–500 kHz，仅由设计保证、未进行生产测试；特定 RC 的频率上下限须另看对应行。",DEFAULT5+[FN1])
ev("line-regulation",5,[54,502,558,529],"6.5 频率线性调整率",["频率线性调整","频率线调整","频率电源调整","line regulation","频率随电压"],"两行频率线性调整率分别对应 12–52 V 和 4.5–12 V 供电条件，典型值栏为空。",DEFAULT5)
ev("ramp",5,[54,529,558,542],"6.5 斜坡幅度 VRMP",["VRMP","斜坡","ramp amplitude","ramp"],"斜坡幅度的典型表达式为 VDD/10，不能当成有上下限的数值保证。",DEFAULT5)
ev("pwm",6,[54,119,558,207],"6.5 PWM 脉宽、占空比与增益",["tMIN","最小脉宽","最小导通","DMAX","最大占空比","KPWM","调制器增益","minimum pulse","duty cycle","PWM"],"最小脉宽列出典型值和最大值；最大占空比列出最小值和典型值，并依赖频率与负载条件。",DEFAULT6+[[54,290,558,304]])
ev("amplifier",6,[54,207,558,287],"6.5 误差放大器",["AOL","GBWP","IIB","ICOMP","误差放大器","开环增益","带宽","偏置电流","error amplifier","gain bandwidth"],"误差放大器的开环增益和单位增益带宽仅由设计保证；输出源、灌电流依赖 FB 和 COMP 测试电压。",DEFAULT6+[[54,290,558,304]])
ev("pins",3,[54,275,558,484],"5 引脚功能",["引脚","pin","COMP","FB","GND","RC","SS","ISNS","接线","管脚"],"RC 接定时网络，SS 接软启动电容，ISNS 与 VDD 间接电流采样电阻；GDRV 驱动外部 P 沟道 MOSFET。")
ev("uvlo-mechanism",12,[54,305,558,370],"7.3.2 欠压锁定机制",["欠压工作原理","启动迟滞","UVLO mechanism","4.3","4.1"],"本节用约 4.3 V 启动、约 4.1 V 关断描述典型机制；精确的电气特性应看第 5 页，推荐工作条件看第 4 页。")
ev("timing",12,[54,382,558,578],"7.3.3 RC 定时公式与电流约束",["RRC","CRC","定时电阻","定时电容","RC公式","频率计算","频率公式","750","timing","operating frequency","0.105"],"标称频率估算 fSW=1/(RRC×CRC×0.105)，R 用 Ω、C 用 F；同时满足 VIN/RRC≤750 μA。公式未给出完整容差模型，不能保证实际频率精度。")
ev("sync",12,[54,587,558,674],"7.3.4 外部时钟同步",["同步","外部时钟","synchronizing","synchronization","150mV","20ns"],"同步需要将 RC 拉至 150 mV 以下至少 20 ns，外部时钟高于自由振荡频率；拉低时间还受到上限约束，须完整阅读本节。")
ev("overcurrent-recovery",14,[54,93,558,264],"7.3.5 过流后的关断与重启",["过流恢复","过流后","打嗝","重启","过流原理","故障恢复","current limit recovery","hiccup","overcurrent"],"过流触发后关断 MOSFET 并放电软启动电容；软启动电压降至复位阈值以下后重试。持续故障会重复此过程；正文约 100 mV、150 mV 为机制描述，保证界限需查第 5 页。")
ev("softstart-mechanism",17,[54,93,558,282],"7.3.6 软启动机制",["软启动原理","软启动过程","延迟启动","soft-start","CSS","软启动时间"],"SS 电容控制软启动过程，内部充电电阻形成上升参考。首版只提供机制证据，暂不自动计算软启动时间。")
ev("application-boundary",19,[54,82,558,125],"8 应用信息的适用范围",["输出电流额定","额定电流","最大输出电流","2.5A","应用示例","design example","output current"],"TPS40200 是控制器，应用示例中的负载电流不等于芯片保证的输出电流能力；实际能力取决于外部功率器件等设计。")
evidence[-1]["bbox"]=[54,75,558,145]
ev("design-note",5,[54,546,558,558],"6.5 脚注 (1)：设计保证",["设计保证","生产测试","production tested","ensured by design"],"脚注 (1) 表示仅由设计保证，未进行生产测试。")

rows=[]
def row(id,symbol,name,rating,minimum,typical,maximum,unit,conditions,eid,notes=()):
    rows.append(dict(id=id,symbol=symbol,name=name,rating=rating,minimum=minimum,
                     typical=typical,maximum=maximum,unit=unit,conditions=conditions,
                     evidence_ids=[eid],notes=list(notes),review="按 PDF 原图逐行复核；非自动提取保证"))
A="absolute_maximum"; R="recommended"; E="electrical"
abs_note=["应力额定值，不代表保证功能正常。"]
for id,sym,name,lo,hi,unit,cond in [
 ("abs-vdd","VDD / ISNS","输入电压",-.3,52,"V","VDD、ISNS 引脚"),
 ("abs-rc-fb","RC / FB","输入电压",-.3,5.5,"V","RC、FB 引脚"),
 ("abs-ss","SS","输入电压",-.3,9,"V","SS 引脚"),
 ("abs-comp","COMP","输出电压",-.3,9,"V","COMP 引脚"),
 ("abs-gdrv","GDRV","输出电压","VIN − 10", "VIN","V","GDRV 引脚；边界依赖 VIN"),
 ("abs-tj","TJ","工作结温",-40,125,"°C","工作结温"),
 ("abs-lead","Lead temperature","引线温度",None,260,"°C","距封装 1.6 mm，持续 10 秒")]:
 row(id,sym,name,A,lo,None,hi,unit,cond,"abs",abs_note)
row("rec-vdd","VDD","推荐输入电压",R,4.5,None,52,"V","推荐工作条件；不是对整个电路的保证","recommended")
row("rec-tj","TJ","推荐工作结温",R,-40,None,125,"°C","结温 TJ；不能用环境温度 TA 代替","recommended")
common="默认 −40 °C < TA = TJ < 85 °C；VDD=12 V；fOSC=100 kHz，除非另有注明。"
def ec(id,symbol,name,lo,ty,hi,unit,condition,eid,notes=()):
 row(id,symbol,name,E,lo,ty,hi,unit,condition,eid,[common]+list(notes))
 if any("仅由设计保证" in note for note in notes):
  rows[-1]["evidence_ids"].append("design-note")
ec("vfb-comp","VFB","反馈参考电压",689,696,702,"mV","COMP=FB；TA=25 °C；其余默认条件见表头","reference")
ec("vfb-25","VFB","反馈参考电压",686,696,703,"mV","4.5 V < VDD < 52 V；TA=25 °C","reference")
ec("vfb-85","VFB","反馈参考电压",679,696,708,"mV","4.5 V < VDD < 52 V；−40 °C < TA < 85 °C","reference")
ec("vfb-125","VFB","反馈参考电压",679,696,710,"mV","4.5 V < VDD < 52 V；−40 °C < TA < 125 °C","reference")
ec("gate-source","Isrc","栅极驱动拉高电流",125,300,None,"mA","默认测试条件","gate")
ec("gate-sink","Isnk","栅极驱动拉低电流",200,300,None,"mA","默认测试条件","gate")
ec("gate-voltage","VGATE","栅极驱动电压",6,8,10,"V","VGATE=VDD−VGDRV；12 V < VDD < 52 V","gate")
ec("iqq","Iqq","静态电流",None,1.5,3,"mA","fOSC=300 kHz；驱动不切换；4.5 V < VDD < 52 V","quiescent")
ec("uvlo-on","VUVLO(on)","欠压启动阈值",3.8,4.25,4.5,"V","−40 °C < TA < 125 °C","uvlo")
ec("uvlo-off","VUVLO(off)","欠压关断阈值",None,4.05,None,"V","默认测试条件；未给出最小值与最大值","uvlo")
ec("uvlo-hyst","VUVLO(HYST)","欠压迟滞",110,200,275,"mV","默认测试条件","uvlo")
ec("rss-charge","RSS(chg)","内部软启动充电电阻",65,105,170,"kΩ","默认测试条件","softstart-values")
ec("rss-discharge","RSS(dchg)","内部软启动放电电阻",190,305,485,"kΩ","默认测试条件","softstart-values")
ec("ss-reset","VSSRST","软启动复位阈值",100,150,200,"mV","默认测试条件","softstart-values")
ec("ilim-0","VILIM","过流阈值",65,100,140,"mV","4.5 V < VDD < 52 V；0 °C < TA < 125 °C","current-limit")
ec("ilim-40","VILIM","过流阈值",55,100,140,"mV","4.5 V < VDD < 52 V；−40 °C < TA < 125 °C","current-limit")
design="脚注 (1)：仅由设计保证，未进行生产测试。"
ec("ocdf","OCDF","过流占空比",None,None,2,"%","默认测试条件；2% 在 MAX 列","current-limit",[design])
ec("ilim-reset","VILIM(rst)","过流复位阈值",100,150,200,"mV","默认测试条件","current-limit")
ec("fosc-range","fOSC","振荡频率范围",35,None,500,"kHz","范围限制","oscillator",[design])
ec("fosc-100","fOSC","振荡频率",85,100,115,"kHz","RRC=200 kΩ；CRC=470 pF","oscillator")
ec("fosc-300","fOSC","振荡频率",255,300,345,"kHz","RRC=68.1 kΩ；CRC=470 pF","oscillator")
ec("line-high","Frequency line regulation","频率线性调整率",-9,None,0,"%","12 V < VDD < 52 V","line-regulation")
ec("line-low","Frequency line regulation","频率线性调整率",-20,None,0,"%","4.5 V < VDD < 12 V","line-regulation")
ec("ramp","VRMP","斜坡幅度",None,"VDD / 10",None,"V","4.5 V < VDD < 52 V","ramp")
ec("tmin-12","tMIN","最小可控脉宽",None,200,400,"ns","VDD=12 V","pwm",["脚注 (2)：参见图 21 的 tMIN 与 fOSC 关系；首版不自动读曲线。"])
ec("tmin-30","tMIN","最小可控脉宽",None,100,200,"ns","VDD=30 V","pwm",["脚注 (2)：参见图 21；不在离散条件之间插值。"])
ec("dmax-100","DMAX","最大占空比",93,95,None,"%","fOSC=100 kHz；CL=470 pF","pwm")
ec("dmax-300","DMAX","最大占空比",90,93,None,"%","fOSC=300 kHz；CL=470 pF","pwm")
ec("kpwm","KPWM","调制器与功率级直流增益",8,10,12,"V/V","默认测试条件","pwm")
ec("iib","IIB","输入偏置电流",None,100,250,"nA","默认测试条件","amplifier")
ec("aol","AOL","开环增益",60,80,None,"dB","默认测试条件","amplifier",[design])
ec("gbwp","GBWP","单位增益带宽",1.5,3,None,"MHz","默认测试条件","amplifier",[design])
ec("comp-source","ICOMP(src)","误差放大器输出源电流",100,250,None,"μA","VFB=0.6 V；COMP=1 V","amplifier")
ec("comp-sink","ICOMP(snk)","误差放大器输出灌电流",1,2.5,None,"mA","VFB=1.2 V；COMP=1 V","amplifier")

def dump(name, data):
 (OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n")
dump("evidence_specs.json",evidence)
dump("parameters.json",rows)
dump("review_log.json",dict(
 source_sha256="a3e23ec7367038ecd8f6ddbfc38392fcb87d997352eabb715b573de538a76240",
 method="先保存未经修正的 pdfplumber 文本与表格，再按原图独立抄录关键三类表格。",
 reviewed_pages=[4,5,6,12], reviewer="Codex 对照原图复核（无独立第三方复核）",
 manual_transcription=True, notes=[
 "VFB 的 VDD 条件为合并单元格，只适用于后三行；第一行为 COMP=FB。",
 "Isrc/Isnk/AOL/GBWP 的第二个数在 TYP 栏；tMIN 的两个数在 TYP/MAX 栏。",
 "DMAX 的两个数在 MIN/TYP 栏，MAX 留空；OCDF 的 2% 在 MAX 栏。",
 "p.12 的 μ 被文本提取误写成 m，定时电阻电流上限按原图保存为 750 μA。",
 "p.6 AOL/GBWP 的脚注 (1) 指向 p.5 的设计保证说明，p.6 本地只印出脚注 (2)。",
 "p.12 正文的约 4.3/4.1 V 不覆盖 p.5 电气特性表和 p.4 推荐条件。"
 ]))
print(f"Prepared {len(evidence)} reviewed evidence groups and {len(rows)} parameter rows.")
