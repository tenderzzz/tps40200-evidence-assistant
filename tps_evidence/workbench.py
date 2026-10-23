"""Presentation adapter: preserve existing query/check Result contracts."""
from functools import lru_cache
from io import BytesIO
import pdfplumber
from . import __version__
from .corpus import ROOT,PDF,load_corpus,load_json
from .export import bundle
from .pdf_runtime import PDF_RENDER_LOCK

PINS=[
 dict(number=1,name="RC",side="left",description="定时电阻从 VDD 接至 RC，定时电容从 RC 接至 GND。",question="RC 引脚接线",followup="RC 频率公式在哪里？"),
 dict(number=2,name="SS",side="left",description="外接到 GND 的电容控制软启动，并参与过流重启计时。",question="软启动原理是什么",followup="RSS(chg) 内部充电电阻"),
 dict(number=3,name="COMP",side="left",description="误差放大器输出；在 COMP 与 FB 之间连接环路补偿网络。",question="误差放大器参数",followup="GBWP"),
 dict(number=4,name="FB",side="left",description="误差放大器反相输入；连接反馈电阻网络的中间节点。",question="反馈参考电压 VFB 是多少？",followup="VFB 的测试条件"),
 dict(number=8,name="VDD",side="right",description="系统输入电压；VDD 与 GND 之间连接本地旁路电容。",question="推荐输入电压上下限",followup="欠压启动阈值"),
 dict(number=7,name="ISNS",side="right",description="电流检测比较器输入；在 ISNS 与 VDD 之间连接采样电阻。",question="VILIM 过流阈值",followup="过流后如何恢复"),
 dict(number=6,name="GDRV",side="right",description="外部 P 沟道 MOSFET 的驱动输出。",question="栅极驱动电流",followup="VGATE"),
 dict(number=5,name="GND",side="right",description="器件地。",question="GND 引脚接线",followup="引脚功能"),
]

def present(result):
    from .chips import data_root
    source,evidence,_=load_corpus(result.chip_id)
    regions=load_json(data_root(result.chip_id)/"curated/row_regions.json")
    if regions["source_sha256"]!=source["sha256"]:raise ValueError("参数行定位资料与手册版本不一致。")
    payload=bundle(result)
    payload["related_evidence"]=[evidence[h.evidence_id].model_dump() for h in result.hits if h.evidence_id not in result.evidence_ids]
    payload["row_regions"]={p.id:regions["regions"][p.id] for p in result.parameters if p.id in regions["regions"]}
    return payload

def bootstrap(chip_id="tps40200"):
    from .engine import query
    from .chips import profile,data_root,catalogue
    from .chip_specs import capabilities
    spec=profile(chip_id);caps=capabilities(chip_id)
    manifest,evidence,parameters=load_corpus(chip_id)
    pins=PINS if chip_id=='tps40200' else [dict(number=n,name=name,side='left' if i<4 else 'right',description=d,question=q,followup=q) for i,(n,name,d,q) in enumerate(caps['pins'])]
    return dict(version=__version__,source=manifest,parameter_rows=len(parameters),
                chip=spec,chips=catalogue(),capabilities={k:v for k,v in caps.items() if k!='pins'},
                reviewed_evidence_groups=sum(e.curated for e in evidence.values()),pins=pins,
                page_sizes=[dict(page=p["page"],width=p["width"],height=p["height"]) for p in load_json(data_root(chip_id)/"raw/pages.json")],
                initial=present(query(spec['initial'],chip_id=chip_id)))

@lru_cache(maxsize=16)
def _page_image(page_number,chip_id="tps40200",source_hash=None):
    from .chips import pdf_path
    with PDF_RENDER_LOCK, pdfplumber.open(pdf_path(chip_id)) as pdf:
        page=pdf.pages[page_number-1];img=page.to_image(resolution=144)
        out=BytesIO();img.save(out,format="PNG");return out.getvalue()

def page_image(page_number,chip_id="tps40200"):
    manifest,_,_=load_corpus(chip_id)
    if not 1<=page_number<=manifest["pages"]:raise KeyError("页码超出手册范围。")
    return _page_image(page_number,chip_id,manifest['sha256'])
