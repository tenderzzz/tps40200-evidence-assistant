from decimal import Decimal
from .corpus import load_corpus
from .models import OperatingPoint, Result, RuleResult, Hit, RULE_LABELS
from .units import quantity

def check(operating_point: OperatingPoint | dict, *, chip_id="tps40200") -> Result:
    from .chips import profile
    profile(chip_id)
    if chip_id != "tps40200":
        from .chip_rules import check as chip_check
        return chip_check(operating_point,chip_id)
    point=OperatingPoint.model_validate(operating_point)
    manifest,_,parameters=load_corpus()
    params={p.id:p for p in parameters}
    parsed={};errors={};checks=[]
    for field,dim in [("vdd","voltage"),("tj","temperature"),("frequency","frequency"),
                      ("resistance","resistance"),("capacitance","capacitance"),("ambient_temperature","temperature")]:
        try:parsed[field]=quantity(getattr(point,field),dim)
        except ValueError as e:parsed[field]=None;errors[field]=str(e)
    def add(rule,title,status,message,ids,value=None,unit=None):
        checks.append(RuleResult(rule=rule,title=title,status=status,message=message,
                    evidence_ids=ids,value=None if value is None else float(value),unit=unit))
    def range_rule(field,title,param_id,factor,unit,eid):
        p=params[param_id];value=parsed[field]
        if field in errors:
            add(field,title,"invalid",errors[field],[eid]);return
        if value is None:
            msg=f"请提供{title}及单位。"
            if field=="tj" and point.ambient_temperature:
                msg="环境温度 TA 不能直接当成结温 TJ；需要结温或经验证的热模型。" + errors.get("ambient_temperature","")
            add(field,title,"needs_information",msg,[eid]);return
        value=value/Decimal(str(factor))
        lo,hi=Decimal(str(p.minimum)),Decimal(str(p.maximum))
        inside=lo<=value<=hi
        prefix="满足该项范围" if inside else "不满足该项范围"
        msg=f"{prefix}：{float(value):g} {unit}；允许 {float(lo):g}–{float(hi):g} {unit}（含边界）。"
        if field=="frequency":msg+="该频率范围仅由设计保证，未进行生产测试。"
        if field=="vdd" and value<lo:msg+="欠压启动阈值的典型值不能代替推荐工作条件。"
        add(field,title,"satisfied" if inside else "violated",msg,[eid],value,unit)
    range_rule("vdd","输入电压 VDD","rec-vdd",1,"V","recommended")
    range_rule("tj","结温 TJ","rec-tj",1,"°C","recommended")
    range_rule("frequency","振荡频率 fOSC","fosc-range",1000,"kHz","oscillator")
    r,c=parsed["resistance"],parsed["capacitance"]
    bad_rc=[errors[k] for k in ("resistance","capacitance") if k in errors]
    if r is not None and r<=0:bad_rc.append("定时电阻必须大于 0 Ω。")
    if c is not None and c<=0:bad_rc.append("定时电容必须大于 0 F。")
    if bad_rc:
        add("rc_frequency","RC 标称频率","invalid"," ".join(bad_rc),["timing"])
    elif r is None or c is None:
        add("rc_frequency","RC 标称频率","needs_information","需要定时电阻 RRC 和电容 CRC，并明确单位。",["timing"])
    else:
        f=1/(r*c*Decimal("0.105"))/1000
        add("rc_frequency","RC 标称频率","estimated",f"fSW=1/(RRC×CRC×0.105)≈{float(f):.6g} kHz；这是标称估算，不保证实际频率精度。",["timing"],f,"kHz")
        fp=params["fosc-range"]
        inside=Decimal(str(fp.minimum))<=f<=Decimal(str(fp.maximum))
        add("rc_range","RC 估算频率范围","satisfied" if inside else "violated",
            ("估算频率在" if inside else "估算频率超出")+"35–500 kHz 范围；实际频率仍受器件及 RC 容差影响。",["oscillator","timing"],f,"kHz")
    # Only resistance and VDD affect this constraint; unrelated capacitance errors do not.
    bad_current=[errors[k] for k in ("vdd","resistance") if k in errors]
    if r is not None and r<=0:bad_current.append("定时电阻必须大于 0 Ω。")
    if bad_current:
        add("rc_current","定时电阻电流","invalid"," ".join(bad_current),["timing"])
    elif r is None or parsed["vdd"] is None:
        add("rc_current","定时电阻电流","needs_information","需要输入电压 VDD 和定时电阻 RRC，并明确单位。",["timing"])
    elif parsed["vdd"]<0:
        add("rc_current","定时电阻电流","invalid","公式估算要求非负供电；负供电不在推荐条件内。",["timing"])
    else:
        i=parsed["vdd"]/r*Decimal("1000000")
        inside=i<=750
        add("rc_current","定时电阻电流","satisfied" if inside else "violated",
            f"VIN/RRC={float(i):.6g} μA；"+("满足" if inside else "不满足")+"≤750 μA 的约束（含边界）。",["timing"],i,"μA")
    active=[r for r in checks if r.status!="needs_information"]
    tolerance_requested=bool(point.resistance_tolerance or point.capacitance_tolerance)
    if tolerance_requested:
        checks.extend(tolerance_checks(point,parsed,errors,params["fosc-range"]))
        active=[r for r in checks if r.status!="needs_information"]
    ids=list(dict.fromkeys(eid for r in (active or checks) for eid in r.evidence_ids))
    status="invalid" if any(r.status=="invalid" for r in checks) else ("answered" if active else "needs_information")
    answer="\n".join(f"{r.title}：{RULE_LABELS[r.status]}。{r.message}" for r in (active or checks))
    return Result(status=status,question="条件检查",answer=answer,inputs=point.model_dump(exclude_none=True),checks=checks,evidence_ids=ids,
        hits=[Hit(evidence_id=eid,score=1) for eid in ids],source_sha256=manifest["sha256"],
        notices=["每项结论仅核对该项限制，不表示完整电路设计已通过。",
                 "容差区间仅含所填电阻、电容的独立有界容差，按端点计算，不含芯片本身误差、温漂或电压漂移；电流使用填写的固定 VDD。" if tolerance_requested else "RC 公式为标称估算；不包含完整器件与元件容差模型。"])


def tolerance_checks(point,parsed,errors,frequency_parameter):
    """Monotone interval endpoints; no probability or device-accuracy claim."""
    tolerances,issues={},{}
    for field in ("resistance_tolerance","capacitance_tolerance"):
        text=getattr(point,field)
        try:
            value=quantity(text,"tolerance")
            if value is not None and not Decimal(0)<=value<Decimal(1):
                raise ValueError("容差须为 0% 至小于 100%。")
            tolerances[field]=value
        except ValueError as e:
            tolerances[field]=None;issues[field]=str(e)
    rows=[]
    def problem(rule,title,required):
        bad={f:issues.get(f) or errors.get(f) for f in required if f in issues or f in errors}
        for f in ("resistance","capacitance"):
            if f in required and parsed[f] is not None and parsed[f]<=0:bad[f]="定时电阻、电容必须大于零。"
        if bad:
            rows.append(RuleResult(rule=rule,title=title,status="invalid",message="；".join(f"{'电阻容差' if f=='resistance_tolerance' else '电容容差' if f=='capacitance_tolerance' else f}：{m}" for f,m in bad.items()),fields=list(bad),evidence_ids=["timing"]))
            return True
        missing=[f for f in required if (tolerances if f.endswith("_tolerance") else parsed).get(f) is None]
        if missing:
            names={"resistance":"定时电阻 RRC","capacitance":"定时电容 CRC","vdd":"固定输入电压 VDD","resistance_tolerance":"电阻容差","capacitance_tolerance":"电容容差"}
            rows.append(RuleResult(rule=rule,title=title,status="needs_information",message="请补充"+"、".join(names[f] for f in missing)+"及单位；空白容差不会当作 0%。",fields=missing,evidence_ids=["timing"]))
            return True
        return False
    r,c=parsed["resistance"],parsed["capacitance"]
    tr,tc=tolerances["resistance_tolerance"],tolerances["capacitance_tolerance"]
    if not problem("rc_tolerance_frequency","RC 元件容差频率区间",["resistance","capacitance","resistance_tolerance","capacitance_tolerance"]):
        lo=1/(r*(1+tr)*c*(1+tc)*Decimal("0.105"))/1000
        hi=1/(r*(1-tr)*c*(1-tc)*Decimal("0.105"))/1000
        rows.append(RuleResult(rule="rc_tolerance_frequency",title="RC 元件容差频率区间",status="estimated",
            message=f"仅由 RRC ±{tr*100:g}%、CRC ±{tc*100:g}% 得到约 {lo:.6g}–{hi:.6g} kHz；下界取 Rmax、Cmax，上界取 Rmin、Cmin。芯片自身误差未计入。",
            minimum=float(lo),maximum=float(hi),unit="kHz",evidence_ids=["timing"]))
        inside=Decimal(str(frequency_parameter.minimum))<=lo and hi<=Decimal(str(frequency_parameter.maximum))
        rows.append(RuleResult(rule="rc_tolerance_range",title="容差区间与频率限制",status="satisfied" if inside else "violated",
            message=("元件容差估算区间全部落入" if inside else "元件容差估算区间未全部落入")+"35–500 kHz；这项检查不包含芯片振荡器误差。",
            minimum=float(lo),maximum=float(hi),unit="kHz",evidence_ids=["oscillator","timing"]))
    if not problem("rc_worst_current","电阻容差下最大电流",["vdd","resistance","resistance_tolerance"]):
        vdd=parsed["vdd"]
        if vdd<0:
            rows.append(RuleResult(rule="rc_worst_current",title="电阻容差下最大电流",status="invalid",message="公式估算要求非负供电。",fields=["vdd"],evidence_ids=["timing"]))
        else:
            lo=vdd/(r*(1+tr))*Decimal(1000000)
            hi=vdd/(r*(1-tr))*Decimal(1000000)
            inside=hi<=750
            rows.append(RuleResult(rule="rc_worst_current",title="电阻容差下最大电流",status="satisfied" if inside else "violated",
                message=f"固定 VDD={vdd:g} V，Rmin={r*(1-tr):g} Ω 时 Imax≈{hi:.6g} μA；"+("满足" if inside else "不满足")+"≤750 μA。未计入供电变化；电容容差不影响此项。",
                value=float(hi),minimum=float(lo),maximum=float(hi),unit="μA",evidence_ids=["timing"]))
    return rows
