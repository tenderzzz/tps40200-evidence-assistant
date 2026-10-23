import json
from .corpus import load_corpus
from .models import Result, RATING_LABELS, RULE_LABELS

def bundle(result: Result):
    manifest,ev,_=load_corpus(result.chip_id)
    return dict(format_version="1.0",result=result.model_dump(),source=manifest,
                evidence=[ev[eid].model_dump() for eid in result.evidence_ids])

def json_export(result):
    return json.dumps(bundle(result),ensure_ascii=False,indent=2)

def number(value):
    if value is None:return "—"
    if isinstance(value,float):return f"{value:g}"
    return str(value)

def markdown_export(result):
    b=bundle(result);r=result
    def cell(value):return str(value).replace("|","\\|").replace("\n"," ")
    from .chips import profile
    lines=[f"# TI {profile(r.chip_id)['name']} / {r.question}","",r.answer,"",f"状态：{r.status}",""]
    if r.inputs:
        labels={"vdd":"输入电压 VDD","tj":"结温 TJ","frequency":"振荡频率 fOSC","resistance":"定时电阻 RRC","capacitance":"定时电容 CRC","ambient_temperature":"环境温度 TA","resistance_tolerance":"电阻容差","capacitance_tolerance":"电容容差"}
        if r.chip_id!='tps40200':
            from .chip_inputs import labels as chip_labels
            labels.update(chip_labels(r.chip_id))
        lines += ["## 原始输入",""]+[f"- {labels.get(k,k)}：{v}" for k,v in r.inputs.items()]+[""]
    if r.parameters:
        lines += ["| 参数 | 类别 | MIN | TYP | MAX | 单位 | 条件 | 证据 |","|---|---|---:|---:|---:|---|---|---|"]
        for p in r.parameters:
            lines.append("| "+" | ".join(map(cell,[f"{p.symbol} {p.name}",RATING_LABELS[p.rating],number(p.minimum),number(p.typical),number(p.maximum),p.unit,p.conditions,", ".join(p.evidence_ids)]))+" |")
        lines += ["","参数注释：",""]
        for p in r.parameters:lines.append(f"- {p.id}："+"；".join(p.notes))
    if r.checks:
        lines += ["","## 逐项检查",""]
        lines += [f"- {c.title} / {RULE_LABELS[c.status]}：{c.message} [{', '.join(c.evidence_ids)}]" for c in r.checks]
    if r.condition_inputs:
        lines += ["", "## 参数行条件匹配", "", "输入（原样保留）：", ""]
        lines += [f"- {k}：{v}" for k,v in r.condition_inputs.items()]
        labels={"applicable":"已提供条件符合","not_applicable":"条件不符","needs_information":"信息不足","not_evaluated":"额定限制／未筛选","invalid":"输入无效"}
        lines += ["", "| 参数行 | 匹配结果 | 原因 |", "|---|---|---|"]
        for match in r.applicability:
            lines.append("| "+" | ".join(map(cell,[match.parameter_id,labels[match.status],"；".join(match.reasons)]))+" |")
    lines += ["","## 说明",""]+[f"- {n}" for n in r.notices]
    lines += ["","## 原文证据",""]
    for e in b["evidence"]:
        lines += [f"### [{e['id']}] {e['title']}","",f"PDF 物理页 {e['page']} / 印刷页 {e['printed_page']}；区域 {e['bbox']}（PDF pt，左上原点）","",e["text"],""]
        if e["context"]:lines += ["表头／脚注上下文：",e["context"],""]
    lines += [f"来源：{b['source']['url']}",f"版本：{b['source']['revision']}",f"SHA-256：{b['source']['sha256']}",""]
    return "\n".join(lines)
