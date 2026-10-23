"""Conservative matching of reviewed row conditions, without dropping facts."""
from decimal import Decimal
from .corpus import ROOT, load_corpus, load_json
from .models import ConditionPoint, ConditionMatch
from .units import quantity

DIMENSIONS = {"vdd":"voltage", "temperature":"temperature", "frequency":"frequency",
              "resistance":"resistance", "capacitance":"capacitance", "load_capacitance":"capacitance",
              "vfb":"voltage", "comp":"voltage"}


def annotate(result, conditions):
    if result.chip_id != "tps40200":
        from .multiconditions import annotate as chip_annotate
        return chip_annotate(result, conditions)
    point = ConditionPoint.model_validate(conditions)
    source, _, _ = load_corpus()
    spec = load_json(ROOT / "data/curated/condition_rules.json")
    if spec["source_sha256"] != source["sha256"]:
        raise ValueError("条件整理与手册版本不一致，请重新复核。")
    parsed, errors = {}, {}
    for field, dimension in DIMENSIONS.items():
        try:parsed[field] = quantity(getattr(point, field), dimension)
        except ValueError as e:errors[field] = str(e);parsed[field] = None
    for field in ("comp_equals_fb", "driver_switching"):parsed[field] = getattr(point, field)
    parsed["test_temperature"] = parsed["temperature"] if point.temperature_kind == "test" else None
    if "temperature" in errors:errors["test_temperature"] = errors["temperature"]
    result.condition_inputs = point.model_dump(exclude_none=True)
    result.condition_errors = {k:v for k,v in errors.items() if k!="test_temperature"}
    matches = []
    for parameter in result.parameters:
        rule = spec["rules"].get(parameter.id)
        if not rule or rule.get("limit"):
            matches.append(ConditionMatch(parameter_id=parameter.id,status="not_evaluated",
                reasons=(rule or {}).get("notes",["此行尚未整理可自动匹配的条件。"]),evidence_ids=parameter.evidence_ids));continue
        failed, missing, invalid = [], [], []
        for term in rule["constraints"]:
            field, label = term["field"], term["label"]
            value = parsed.get(field)
            if field in errors:invalid.append(f"{label}：{errors[field]}");continue
            if value is None:
                if field == "test_temperature" and point.temperature_kind != "test" and point.temperature:
                    missing.append("请明确温度类型；不会默认认为 TA = TJ。" if point.temperature_kind=="unknown" else "仅有环境温度 TA 或结温 TJ，不能确认手册 TA = TJ 的测试条件。")
                else:missing.append(f"待确认 {label}。")
                continue
            if term["op"] == "eq":
                expected = term["value"] if isinstance(term["value"], bool) else Decimal(str(term["value"]))
                okay = value == expected
            else:okay = Decimal(str(term["low"])) < value < Decimal(str(term["high"]))
            if not okay:failed.append(f"不符合 {label}。")
        status = "invalid" if invalid else "not_applicable" if failed else "needs_information" if missing else "applicable"
        reasons = invalid + failed + list(dict.fromkeys(missing))
        if not reasons:reasons = ["已提供条件符合此行及其继承的表头条件；原始上下限仍按该行读取。"]
        matches.append(ConditionMatch(parameter_id=parameter.id,status=status,reasons=reasons+rule.get("notes",[]),evidence_ids=parameter.evidence_ids))
    result.applicability = matches
    if errors:
        result.status = "invalid"
        result.answer = "筛选条件输入需要修改；下方仍保留原始参数行。"
    result.notices.append("条件匹配只判断已整理的测试条件；多个适用行分别保留，不自动合并保证范围。TA = TJ 表示手册测试设置，不是环境到结温的换算。")
    return result
