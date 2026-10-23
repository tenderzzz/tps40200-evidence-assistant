"""Explicit chip registry. Never mutate a process-wide active chip."""
from pathlib import Path
from .corpus import ROOT

CHIPS = {
    "tps40200": dict(name="TPS40200", manufacturer="TI", category="电源控制器", revision="SLUS659G (Rev. G)", revision_date="2014-11", pdf="tps40200-rev-g.pdf", initial="反馈参考电压 VFB 是多少？", pins_page=3, package="SOIC（D）顶视图", core_pages=40),
    "lm2596-adj": dict(name="LM2596-ADJ", title="LM2596 SIMPLE SWITCHER Power Converter 150-kHz 3-A Step-Down Voltage Regulator", manufacturer="TI", category="降压稳压器", revision="SNVS124G (Rev. G)", revision_date="2023-03", pdf="lm2596.pdf", initial="反馈基准 VFB 是多少？", pins_page=4, package="TO-220（NDH）顶视图", packages=[dict(id="ndh",name="TO-220（NDH）"),dict(id="ktt",name="TO-263（KTT）")], core_pages=35),
    "lm358": dict(name="LM358", title="Industry-Standard Dual Operational Amplifiers", manufacturer="TI", category="双运算放大器", revision="SLOS068AB (Rev. AB)", revision_date="2024-10", pdf="lm358.pdf", initial="输入失调电压 VOS 是多少？", pins_page=3, package="SOIC（D）顶视图", core_pages=31),
    "ne555": dict(name="NE555", title="xx555 Precision Timers", manufacturer="TI", category="定时器", revision="SLFS022K (Rev. K)", revision_date="2026-03", pdf="ne555.pdf", initial="TRIG 触发阈值是多少？", pins_page=3, package="SOIC（D）顶视图", core_pages=20),
}

def profile(chip_id="tps40200"):
    if not isinstance(chip_id,str) or chip_id not in CHIPS:
        raise ValueError("未知芯片。请选择 TPS40200、LM2596-ADJ、LM358 或 NE555。")
    return dict(id=chip_id, **CHIPS[chip_id])

def data_root(chip_id="tps40200") -> Path:
    profile(chip_id)
    return ROOT/"data" if chip_id=="tps40200" else ROOT/"data/chips"/chip_id

def pdf_path(chip_id="tps40200") -> Path:
    if chip_id=="tps40200":
        from . import corpus
        return corpus.PDF
    return data_root(chip_id)/"source"/profile(chip_id)["pdf"]

def catalogue():
    from .chip_specs import SPECS
    functions={
        'tps40200':['参数查询','测试条件筛选','供电/结温/频率检查','RC定时与容差'],
        'lm2596-adj':['参数查询','测试条件筛选','输入范围检查','反馈分压标称估算'],
        'lm358':['参数查询','测试条件筛选','供电压差/TA检查','推荐与电气共模范围检查'],
        'ne555':['参数查询','测试条件筛选','供电/TA检查','单稳态/无稳态定时与元件容差']}
    result=[]
    for chip in CHIPS:
        labels={f['name']:f['label'] for f in SPECS[chip]['check_fields']+SPECS[chip]['condition_fields']} if chip in SPECS else {
            'vdd':'输入电压 VDD','tj':'结温 TJ','frequency':'振荡频率 fOSC','resistance':'定时电阻 RRC','capacitance':'定时电容 CRC',
            'temperature':'筛选温度','temperature_kind':'温度类型','ambient_temperature':'环境温度 TA','resistance_tolerance':'电阻容差','capacitance_tolerance':'电容容差'}
        result.append(dict(profile(chip),features=functions[chip],input_labels=labels))
    return result
