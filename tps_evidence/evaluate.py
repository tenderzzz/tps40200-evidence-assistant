from collections import Counter
from datetime import datetime, timezone
from math import isclose
from .corpus import ROOT, load_json, dump_json, load_corpus
from .engine import query
from .rules import check
from .search import plain_retrieve

def evaluate(split="all",save=True,*,chip_id="tps40200"):
    from .chips import data_root
    benchmark=load_json(data_root(chip_id)/"benchmark.json")
    manifest,ev,_=load_corpus(chip_id)
    if benchmark["source_sha256"]!=manifest["sha256"]:raise ValueError("验证集的手册版本不一致。")
    cases=[c for c in benchmark["cases"] if split=="all" or c["split"]==split]
    rows=[]
    for c in cases:
        exp=c["expected"];r=query(c["question"],c.get('conditions'),chip_id=chip_id) if c["kind"]=="query" else check(c["point"],chip_id=chip_id)
        errors=[]
        if c["kind"]=="query":
            if r.status!=exp["status"]:errors.append(f"status: expected {exp['status']}, got {r.status}")
            actual={p.id:p.model_dump() for p in r.parameters}
            for pid,values in exp["facts"].items():
                for k,value in values.items():
                    if actual.get(pid,{}).get(k,"__absent__")!=value:errors.append(f"{pid}.{k}: expected {value!r}")
            for phrase in exp["contains"]:
                if phrase not in r.answer:errors.append(f"answer missing: {phrase}")
            applicability={m.parameter_id:m.status for m in r.applicability}
            for pid,status in exp.get('applicability',{}).items():
                if applicability.get(pid)!=status:errors.append(f'applicability {pid}: expected {status}, got {applicability.get(pid)}')
        else:
            item=next((x for x in r.checks if x.rule==exp["rule"]),None)
            if item is None or item.status!=exp["rule_status"]:errors.append("rule status mismatch")
            if exp["value"] is not None and (item is None or item.value is None or not isclose(item.value,exp["value"],rel_tol=1e-7,abs_tol=1e-7)):
                errors.append("rule numeric value mismatch")
        top3=[h.evidence_id for h in r.hits[:3]]
        expected=exp["evidence"]
        hit=any(eid in top3 for eid in expected) if expected else None
        baseline_hit=None
        if c["kind"]=="query" and expected:
            baseline=plain_retrieve(c["question"],chip_id=chip_id)
            def overlaps(chunk,eid):
                e=ev[eid]; b=chunk["bbox"]
                vertical=max(0,min(b[3],e.bbox[3])-max(b[1],e.bbox[1]))
                return chunk["page"]==e.page and vertical/(e.bbox[3]-e.bbox[1])>=0.25
            baseline_hit=any(overlaps(ch,eid) for ch in baseline for eid in expected)
        missing=[eid for eid in r.evidence_ids if eid not in ev]
        if missing:errors.append(f"unknown evidence IDs: {missing}")
        rows.append(dict(id=c["id"],category=c["category"],split=c["split"],family=c["family"],
            kind=c["kind"],question=c.get("question",str(c.get("point"))),passed=not errors,errors=errors,
            actual_status=r.status,top3=top3,expected_evidence=expected,retrieval_hit=hit,
            baseline_hit=baseline_hit,has_expected_facts=bool(exp.get("facts")),
            fact_answered=bool(r.parameters),fact_correct=not errors and bool(exp.get("facts")),
            output=r.model_dump()))
    def metrics(items):
        relevant=[r for r in items if r["kind"]=="query" and r["retrieval_hit"] is not None]
        facts=[r for r in items if r["has_expected_facts"]]
        answered=[r for r in facts if r["fact_answered"]]
        unsupported=[r for r in items if r["category"]=="unsupported"]
        def fraction(n,d):return n/d if d else None
        return dict(cases=len(items),passed=sum(r["passed"] for r in items),
            query_retrieval_cases=len(relevant),top3_recall=fraction(sum(r["retrieval_hit"] for r in relevant),len(relevant)),
            plain_top3_recall=fraction(sum(bool(r["baseline_hit"]) for r in relevant),len(relevant)),
            fact_cases=len(facts),fact_answered=len(answered),
            fact_accuracy=fraction(sum(r["fact_correct"] for r in answered),len(answered)),
            fact_coverage=fraction(len(answered),len(facts)),
            unsupported_correct=sum(r["passed"] for r in unsupported),unsupported_cases=len(unsupported),
            by_category={cat:dict(total=sum(r["category"]==cat for r in items),passed=sum(r["category"]==cat and r["passed"] for r in items)) for cat in sorted({r["category"] for r in items})})
    report=dict(evaluated_at=datetime.now(timezone.utc).isoformat(),source=manifest,chip_id=chip_id,
        benchmark_corrections=benchmark.get("corrections",[]),
        methodology="自建验证集；先定义期望再实现。开发/留出各30题。基线与增强检索用同一BM25分词器；增强额外包含人工别名、结构化表格与整理说明，因此不能把差异单独归因于分块。",
        limitations=["题目、参数整理和实现由同一开发过程完成，不是独立盲测。","证据命中按预标注区域评价；不等于任意问题的引用语义正确率。","留出集规模小，比例仅适用于本组案例，不代表通用芯片手册准确率。"],
        metrics=metrics(rows),splits={s:metrics([r for r in rows if r["split"]==s]) for s in ["dev","holdout"] if any(r["split"]==s for r in rows)},cases=rows)
    if chip_id!='tps40200':
        report['methodology']='自建固定验证集，开发/留出各30题，同一问题的改写同组；期望数值来自固定PDF转录或独立有理数计算，未从被测引擎生成。增强检索包含人工别名、结构化表格与中文说明，不单独归因于分块。'
    if save:
        folder=ROOT/('reports' if chip_id=='tps40200' else f'reports/chips/{chip_id}')
        dump_json(folder/f"evaluation-{split}.json",report)
        if split in ("holdout","all") and not (folder/"holdout-first.json").exists():
            dump_json(folder/"holdout-first.json",dict(report,initial_holdout_metrics=report["splits"].get("holdout")))
    return report

def markdown_report(report):
    from .chips import profile
    name=profile(report.get('chip_id','tps40200'))['name']
    lines=[f"# {name} 本地原型验证报告","",report["methodology"],"",
        "| 分组 | 案例通过 | 证据 Top-3 | 原文基线 Top-3 | 参数事实正确 | 参数覆盖 |",
        "|---|---:|---:|---:|---:|---:|"]
    def pct(v):return "不适用" if v is None else f"{v:.1%}"
    for s,m in report["splits"].items():
        lines.append(f"| {s} | {m['passed']}/{m['cases']} | {pct(m['top3_recall'])} ({m['query_retrieval_cases']}题) | {pct(m['plain_top3_recall'])} | {pct(m['fact_accuracy'])} | {pct(m['fact_coverage'])} ({m['fact_cases']}题) |")
    lines += ["","## 失败案例",""]
    failures=[c for c in report["cases"] if not c["passed"]]
    lines += [f"- {c['id']}：{c['question']}；{'；'.join(c['errors'])}" for c in failures] or ["本组预定义案例未观察到失败；这不说明任意表述都可正确处理。"]
    lines += ["","## 实际能力边界",""]+[f"- {l}" for l in report["limitations"]]
    if report.get("benchmark_corrections"):
        lines += ["","## 验证数据修正记录",""]
        lines += [f"- {c['case']}：期望值由 {c['old_value']} 改为 {c['new_value']} kHz。{c['reason']}" for c in report["benchmark_corrections"]]
    lines += ["- 无别名的中文表达可能只返回相关原文或无结果，无法进行开放式语言理解。","- 不自动选择所有温度/电压条件对应的唯一参数行，展示完整条件供核对。","- 曲线不自动读数；公式与元件容差估算不包含完整器件误差模型。","","## 复现","","运行 `uv run tps-evidence evaluate --split all`。单元测试另运行 `uv run pytest`。","",f"固定手册 SHA-256：`{report['source']['sha256']}`。"]
    return "\n".join(lines)+"\n"
