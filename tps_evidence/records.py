"""Immutable local snapshots, one atomic JSON file per record, outside iCloud."""
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import uuid4
import json
import os
import re
import threading

from .models import Result
from .units import quantity

LOCK = threading.RLock()


def home():
    override = os.environ.get("TPS_RECORDS_HOME")
    return Path(override) if override else Path.home()/"Library/Application Support/TPS40200 Evidence/records"


def _path(id):
    if not isinstance(id,str) or not re.fullmatch(r"[0-9a-f]{32}",id):raise KeyError("记录不存在。")
    return home()/f"{id}.json"


def read(id):
    path = _path(id)
    if not path.exists():raise KeyError("记录不存在。")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        if value["schema_version"] not in (1,2) or value["id"] != id:raise ValueError()
        Result.model_validate(value["snapshot"]["result"])
        if not isinstance(value["name"],str) or not isinstance(value["request"],dict):raise ValueError()
        # Compatibility is in memory only. Never rewrite an old user's file.
        value.setdefault("chip_id",value['snapshot']['result'].get('chip_id','tps40200'))
        value['request'].setdefault('chip_id',value['chip_id'])
        from .chips import profile
        profile(value['chip_id'])
        return value
    except (KeyError, ValueError, TypeError) as e:
        raise ValueError(f"记录 {id} 无法读取。原文件已保留，请先备份后检查。") from e


def list_records(chip_id=None):
    if not home().exists():return []
    with LOCK:
        records = [read(p.stem) for p in home().glob("*.json") if re.fullmatch(r"[0-9a-f]{32}",p.stem)]
    return sorted([r for r in records if chip_id is None or r['chip_id']==chip_id],key=lambda r:r["created_at"],reverse=True)


def save(name, request, snapshot):
    if not isinstance(name,str) or not 1<=len(name.strip())<=60:
        raise ValueError("方案名称须为 1–60 个字符。")
    Result.model_validate(snapshot["result"])
    from . import __version__
    chip_id=snapshot['result'].get('chip_id','tps40200')
    if request.get('chip_id',chip_id)!=chip_id:raise ValueError('记录请求与快照的芯片型号不一致。')
    request={**request,'chip_id':chip_id}
    record = dict(schema_version=2,chip_id=chip_id,app_version=__version__,id=uuid4().hex,name=name.strip(),
                  created_at=datetime.now(timezone.utc).isoformat(),request=request,snapshot=snapshot)
    with LOCK:
        folder=home();folder.mkdir(parents=True,exist_ok=True,mode=0o700)
        if len(list(folder.glob("*.json")))>=200:raise ValueError("本机记录已达 200 条，请先备份并整理记录目录。")
        temp=None
        try:
            with NamedTemporaryFile(mode="w",encoding="utf-8",dir=folder,prefix=".saving-",suffix=".tmp",delete=False) as f:
                temp=Path(f.name)
                json.dump(record,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
            os.replace(temp,_path(record["id"]))
        finally:
            if temp and temp.exists():temp.unlink()
    return record


INPUT_LABELS={"vdd":"输入电压 VDD","tj":"结温 TJ","frequency":"振荡频率 fOSC","resistance":"定时电阻 RRC",
    "capacitance":"定时电容 CRC","ambient_temperature":"环境温度 TA","resistance_tolerance":"电阻容差",
    "capacitance_tolerance":"电容容差","temperature":"筛选温度","temperature_kind":"筛选温度类型",
    "comp_equals_fb":"COMP = FB","driver_switching":"驱动切换","load_capacitance":"负载电容 CL","vfb":"VFB 测试值","comp":"COMP 测试值"}
DIMENSIONS={"vdd":"voltage","tj":"temperature","temperature":"temperature","ambient_temperature":"temperature",
    "frequency":"frequency","resistance":"resistance","capacitance":"capacitance","load_capacitance":"capacitance",
    "resistance_tolerance":"tolerance","capacitance_tolerance":"tolerance","vfb":"voltage","comp":"voltage"}

from .chip_specs import SPECS
for _spec in SPECS.values():
    for _field in _spec['check_fields']+_spec['condition_fields']:
        INPUT_LABELS[_field['name']]=_field['label']
        if _field['dimension']:DIMENSIONS[_field['name']]=_field['dimension']


def _same(field,a,b):
    if field in DIMENSIONS:
        try:return quantity(a,DIMENSIONS[field])==quantity(b,DIMENSIONS[field])
        except (ValueError,TypeError):pass
    return a==b


def compare(a,b):
    ra,rb=a["snapshot"]["result"],b["snapshot"]["result"]
    chip_a=a.get('chip_id',ra.get('chip_id','tps40200'));chip_b=b.get('chip_id',rb.get('chip_id','tps40200'))
    if chip_a!=chip_b:
        from .chips import profile
        def meta(record,chip):
            return dict(id=record['id'],name=record['name'],created_at=record['created_at'],chip_id=chip,chip_name=profile(chip)['name'],
                question=record['snapshot']['result']['question'],source_sha256=record['snapshot']['source']['sha256'],source_revision=record['snapshot']['source']['revision'])
        return dict(a=meta(a,chip_a),b=meta(b,chip_b),same_chip=False,same_source=False,same_kind=a['request']['kind']==b['request']['kind'],
            inputs=[],checks=[],parameters=[],snapshot_a=a['snapshot'],snapshot_b=b['snapshot'],evidence_a=a['snapshot']['evidence'],evidence_b=b['snapshot']['evidence'],
            notice='两条记录来自不同型号。仅并列展示保存的原始记录，不生成参数差值、替代关系或兼容结论。')
    ia=ra.get("condition_inputs",{}) if a["request"]["kind"]=="query" else ra["inputs"]
    ib=rb.get("condition_inputs",{}) if b["request"]["kind"]=="query" else rb["inputs"]
    provided=lambda values:{k:v for k,v in values.items() if v is not None and (not isinstance(v,str) or v.strip())}
    ia,ib=provided(ia),provided(ib)
    inputs=[dict(field=k,label=INPUT_LABELS.get(k,k),a=ia.get(k),b=ib.get(k),changed=not _same(k,ia.get(k),ib.get(k)),
                 representation_changed=ia.get(k)!=ib.get(k)) for k in dict.fromkeys([*ia,*ib])]
    ca,cb={c["rule"]:c for c in ra["checks"]},{c["rule"]:c for c in rb["checks"]}
    checks=[]
    for key in dict.fromkeys([*ca,*cb]):
        left,right=ca.get(key),cb.get(key)
        values=lambda c:None if c is None else tuple(c.get(k) for k in ("status","value","minimum","maximum","unit"))
        checks.append(dict(rule=key,title=(left or right)["title"],a=left,b=right,changed=values(left)!=values(right)))
    pa,pb={p["id"]:p for p in ra["parameters"]},{p["id"]:p for p in rb["parameters"]}
    ma={m["parameter_id"]:m for m in ra.get("applicability",[])}
    mb={m["parameter_id"]:m for m in rb.get("applicability",[])}
    parameters=[]
    for key in dict.fromkeys([*pa,*pb]):
        left,right=pa.get(key),pb.get(key)
        values=lambda p,m:None if p is None else tuple(p.get(k) for k in ("minimum","typical","maximum","unit","conditions"))+(m.get("status") if m else None,)
        parameters.append(dict(id=key,symbol=(left or right)["symbol"],conditions=(left or right)["conditions"],
            a=left,b=right,match_a=ma.get(key),match_b=mb.get(key),changed=values(left,ma.get(key))!=values(right,mb.get(key))))
    meta=lambda r:dict(id=r["id"],name=r["name"],created_at=r["created_at"],chip_id=chip_a,question=r["snapshot"]["result"]["question"],
                       source_sha256=r["snapshot"]["source"]["sha256"],source_revision=r["snapshot"]["source"]["revision"])
    return dict(a=meta(a),b=meta(b),same_chip=True,same_source=a["snapshot"]["source"]["sha256"]==b["snapshot"]["source"]["sha256"],
                same_kind=a["request"]["kind"]==b["request"]["kind"],inputs=inputs,checks=checks,parameters=parameters,
                evidence_a=a["snapshot"]["evidence"],evidence_b=b["snapshot"]["evidence"],
                notice="对比保留保存时的快照，不自动重算或给出整个电路通过的结论。单位不同但物理数值相同的输入单独标注。")


def comparison_markdown(comparison):
    def cell(v):return str(v if v is not None else "未提供").replace("|","\\|").replace("\n"," ")
    def summary(c):return "无此项" if c is None else f"{c['status']}；{c['message']}"
    lines=["# 芯片手册方案对比","",f"A：{comparison['a']['name']}",f"B：{comparison['b']['name']}","",comparison["notice"],"",
           "| 输入 | A | B | 变化 |","|---|---|---|---|"]
    for r in comparison["inputs"]:
        lines.append("| "+" | ".join(map(cell,[r["label"],r["a"],r["b"],"数值／条件变化" if r["changed"] else "仅写法不同" if r["representation_changed"] else "相同"]))+" |")
    lines += ["","| 检查 | A | B |","|---|---|---|"]
    for r in comparison["checks"]:lines.append("| "+" | ".join(map(cell,[r["title"],summary(r["a"]),summary(r["b"])]))+" |")
    for r in comparison["parameters"]:
        lines += ["",f"## 参数行 {r['id']}",r["conditions"],"", "| 方案 | MIN | TYP | MAX | 单位 | 条件匹配 |","|---|---|---|---|---|---|"]
        for side in ("a","b"):
            p,m=r[side],r[f"match_{side}"]
            if p:
                values=[side.upper(),p["minimum"],p["typical"],p["maximum"],p["unit"],(m["status"]+"；"+"；".join(m["reasons"])) if m else "未筛选"]
                lines.append("| "+" | ".join(map(cell,values))+" |")
    if comparison.get('same_chip') is False:
        for side in ('a','b'):
            snap=comparison['snapshot_'+side];res=snap['result']
            lines += ['',f"## {side.upper()} / {comparison[side]['chip_name']}",res['answer'],'', '原始输入：']
            lines += [f'- {k}：{v}' for k,v in (res.get('condition_inputs') or res.get('inputs',{})).items()]
            for p in res['parameters']:
                lines.append(f"- {p['symbol']}：MIN {p['minimum']} / TYP {p['typical']} / MAX {p['maximum']} {p['unit']}；{p['conditions']}")
    for side in ("a","b"):
        m=comparison[side]
        lines += ["",f"## {side.upper()} 来源",m["source_revision"],f"SHA-256：{m['source_sha256']}"]
        for e in comparison[f"evidence_{side}"]:
            lines += ["",f"[{e['id']}] {e['title']} / PDF 页 {e['page']}",e["text"],e.get("context","")]
    return "\n".join(lines)+"\n"
