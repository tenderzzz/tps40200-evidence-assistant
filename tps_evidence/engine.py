import re
from .corpus import load_corpus
from .models import Result, Hit
from .rules import check
from .search import retrieve

PARAM_NOTICE="典型值不等于保证上下限；空白表示手册未给出该列数值。各条件行分别有效，不自动合并或插值。"

def query(question: str, conditions=None, *, chip_id="tps40200") -> Result:
    from .chips import profile
    p=profile(chip_id)
    source,_,_=load_corpus(chip_id)
    chips=re.findall(r"\b(?:TPS\d+[A-Z0-9/-]*|LM\d+[A-Z0-9/-]*|(?:NE|NA|SA|SE|TLC|LMC)\d+[A-Z0-9/-]*|STM\d+[A-Z0-9/-]*|AD\d+[A-Z0-9/-]*|MP\d+[A-Z0-9/-]*|LT\d+[A-Z0-9/-]*)\b",question,re.I)
    allowed={"tps40200":{"TPS40200"},"lm2596-adj":{"LM2596","LM2596-ADJ","LM2596S-ADJ","LM2596T-ADJ"},"lm358":{"LM358"},"ne555":{"NE555"}}[chip_id]
    if any(c.upper() not in allowed for c in chips):
        return Result(chip_id=chip_id,status="unsupported",question=question,
            answer=f"当前所选资料只覆盖 {p['name']}（TI）。问题包含其他型号或后缀，请切换对应芯片；没有收录的型号不能沿用当前规格。",
            source_sha256=source['sha256'],source_revision=source['revision'])
    result = _query(question) if chip_id=="tps40200" else _chip_query(question,chip_id)
    if conditions is not None:
        from .conditions import annotate
        result = annotate(result, conditions)
    return result

def _chip_query(question,chip_id):
    manifest,evidence,parameters=load_corpus(chip_id)
    def result(status,answer,**kw):
        return Result(chip_id=chip_id,status=status,question=question,answer=answer,source_sha256=manifest['sha256'],source_revision=manifest['revision'],**kw)
    if not question.strip():return result('invalid','请输入参数符号、中文参数名或选择下方案例。')
    if len(question)>2000:return result('invalid','问题过长，请缩短到2000字以内。')
    if re.search(r"曲线.*(?:读|数值|精确|插值)|(?:读|插值).*曲线|完整.*(?:电路|BOM|原理图)|整个.*(?:PCB|电路)|保证.*(?:稳定|效率)|生成.*(?:BOM|原理图)",question,re.I):
        return result('unsupported','当前支持手册证据与有限检查；曲线自动读数和完整电路设计判断暂不支持。')
    checking=bool(re.search(r'能.*(?:工作|运行|用)|(?:是否|可以).*(?:符合|满足|工作|用)|检查|核对',question))
    voltages=re.findall(r'([+-]?(?:\d+(?:\.\d*)?|\.\d+)\s*(?:mV|V))(?![a-zA-Z])',question)
    if checking and not re.search(r'VFB|VREF|VOS|TRIG|THRES|RESET|参考|阈值|失调|输出|共模|栅',question,re.I):
        if len(voltages)==1 and chip_id in ('lm2596-adj','ne555'):
            r=check({'vin' if chip_id=='lm2596-adj' else 'vcc':voltages[0]},chip_id=chip_id);r.question=question;return r
        if voltages or re.search(r'\d',question):
            return result('needs_information',('请在条件检查页分别填写 V+、V−，不能把单个电压默认当成总压差或共模输入。' if chip_id=='lm358' else '请在条件检查页确认输入量与单位，不自动从多个电压中选择供电。'),evidence_ids=['recommended'])
    hits=retrieve(question,chip_id=chip_id)
    if not hits:return result('not_found','在当前型号的已整理证据中未找到匹配内容。请试用明确参数符号或中文参数名。')
    first=evidence[hits[0].evidence_id]
    if hits[0].score<100:
        return result('evidence_only','找到当前型号可能相关的原文，请核对原文条件；未生成结构化参数结论。',hits=hits,evidence_ids=[h.evidence_id for h in hits])
    records=[p for p in parameters if first.id in p.evidence_ids and not first.context_only]
    ids=list(dict.fromkeys([first.id]+[eid for p in records for eid in p.evidence_ids]))
    return result('answered' if records else 'evidence_only',first.summary,parameters=records,hits=hits,evidence_ids=ids,
        notices=[PARAM_NOTICE,'本页只使用当前TI型号适用行；原文片段可能同时列出其他型号，其数值不会自动转用于当前型号。'])

def _query(question: str) -> Result:
    manifest,evidence,parameters=load_corpus()
    def result(status,answer,**kw):
        return Result(status=status,question=question,answer=answer,source_sha256=manifest["sha256"],**kw)
    if not question.strip():return result("invalid","请输入参数符号或工程问题，例如 VFB、过流后如何恢复。")
    if len(question)>2000:return result("invalid","问题过长，请缩短到 2000 字以内。")
    chips=re.findall(r"\b(?:TPS\d+[A-Z0-9-]*|LM\d+[A-Z0-9-]*|STM\d+[A-Z0-9-]*|AD\d+[A-Z0-9-]*|MP\d+[A-Z0-9-]*|LT\d+[A-Z0-9-]*)\b",question,re.I)
    if any(c.upper()!="TPS40200" for c in chips):
        return result("unsupported","当前资料只覆盖 TPS40200 Rev. G；不能用它回答其他芯片的参数。")
    if re.search(r"(?:曲线.*(?:读|精确|插值|数值)|(?:读|插值).*曲线|读取图\s*\d|完整.*(?:电路|BOM|原理图)|整个.*(?:PCB|电路)|保证.*(?:稳定|效率)|生成.*(?:BOM|原理图))",question,re.I):
        return result("unsupported","当前支持参数证据查询和有限条件检查；曲线读数、完整电路设计及整机性能保证需要进一步分析。")
    if "环境温度" in question and re.search(r"结温|TJ|工作|检查",question,re.I):
        return result("needs_information","环境温度 TA 不能直接作为结温 TJ。请补充结温或经验证的热模型。",evidence_ids=["recommended"],hits=[Hit(evidence_id="recommended",score=1)])
    # Free text only extracts explicit voltage/frequency units for narrow check intents.
    checking=bool(re.search(r"能.*(?:工作|运行|用)|(?:是否|可以).*(?:符合|满足|工作|用)|检查|核对",question))
    if checking and not re.search(r"VFB|VGATE|VUVLO|VILIM|参考|阈值|占空比|脉宽",question,re.I):
        voltages=list(re.finditer(r"([+-]?(?:\d+(?:\.\d*)?|\.\d+)\s*(?:mV|V))(?![a-zA-Z])",question))
        frequencies=list(re.finditer(r"([+-]?(?:\d+(?:\.\d*)?|\.\d+)\s*(?:MHz|kHz|Hz))(?![a-zA-Z])",question))
        if len(voltages)>1 or len(frequencies)>1 or (voltages and re.search(r"输出|栅极|栅压|COMP|SS",question,re.I)):
            return result("needs_information","请在条件检查页明确填写输入电压 VDD 和频率。不能把输出或栅极电压当成 VDD，也不自动选择多个数值中的一个。",evidence_ids=["recommended"])
        voltage=voltages[0] if voltages else None
        freq=frequencies[0] if frequencies else None
        if voltage or freq:
            r=check(dict(vdd=voltage.group(1) if voltage else None,frequency=freq.group(1) if freq else None))
            r.question=question;return r
        if re.search(r"\d",question):
            return result("needs_information","请确认数值对应的参数并补充单位，例如输入电压 4.3 V 或频率 100 kHz。",evidence_ids=["recommended"])
    hits=retrieve(question)
    if not hits:return result("not_found","在当前手册证据中未找到匹配内容。可试用参数符号、中文参数名，或选择示例问题。")
    first=evidence[hits[0].evidence_id]
    # Only reviewed alias matches can produce structured fact answers.
    if hits[0].score<100:
        return result("evidence_only","找到可能相关的原文，请核对右侧证据；当前未识别出可直接回答的参数。",hits=hits,evidence_ids=[h.evidence_id for h in hits],notices=["检索得分只用于排序，不表示答案置信度。"])
    records=[p for p in parameters if first.id in p.evidence_ids and first.id!="design-note"]
    ids=[first.id]
    if first.id in ("gate","application-boundary"):
        ids.append("pins") # External P-channel FET/controller context is on p.3.
    for p in records:
        for eid in p.evidence_ids:
            if eid not in ids:ids.append(eid)
    notices=[PARAM_NOTICE] if records else ["中文整理说明与英文原文分开展示；以引用的条件和脚注为准。"]
    return result("answered" if records else "evidence_only",first.summary,
                  parameters=records,hits=hits,evidence_ids=ids,notices=notices)
