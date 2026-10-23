"""Reviewed transcriptions for three pinned TI manuals; not a PDF table guesser.

Values and column placement were checked against rendered original pages.
The uncorrected pdfplumber output, review decisions, conditions and geometry
are stored separately. Re-run only against these document revisions.
"""
from pathlib import Path
import hashlib
import pdfplumber
from tps_evidence.corpus import dump_json,load_json
from tps_evidence.chips import profile,data_root,pdf_path

REVIEW="Codex 对照固定 PDF 页面整理；尚无独立第三方复核。"

def eq(field,value):return dict(field=field,op="eq",value=value)
def between(field,low,high):return dict(field=field,op="range",low=low,high=high)
def bound(field,op,value):return dict(field=field,op=op,value=value)

class Builder:
    def __init__(self,chip):
        self.chip=chip;self.root=data_root(chip);self.pdf=pdfplumber.open(pdf_path(chip))
        if hashlib.sha256(pdf_path(chip).read_bytes()).hexdigest()!=load_json(self.root/'source/download.json')['sha256']:
            raise ValueError('文件与下载时固定的哈希不同，请重新复核，禁止沿用坐标。')
        self.evs={};self.params=[];self.rules={};self.regions={};self.decisions=[]
    def ev(self,id,page,top,bottom,aliases,summary,contexts=None):
        p=self.pdf.pages[page-1];box=[54,top,558,bottom]
        contexts=contexts or []
        self.evs[id]=dict(id=id,title=aliases[0],page=page,printed_page=str(page),bbox=box,
            context_bboxes=contexts,text=p.crop(box).extract_text(x_tolerance=1) or "",
            context="\n".join(p.crop(b).extract_text(x_tolerance=1) or "" for b in contexts),
            aliases=aliases,summary=summary,curated=True)
        return id
    def p(self,id,symbol,name,values,unit,conditions,eid,top=None,bottom=None,rating="electrical",terms=None,notes=None):
        e=self.evs[eid]
        self.params.append(dict(id=id,symbol=symbol,name=name,rating=rating,minimum=values[0],typical=values[1],maximum=values[2],
            unit=unit,conditions=conditions,notes=notes or [],evidence_ids=[eid],review=REVIEW))
        self.regions[id]=dict(page=e["page"],bbox=[54,top if top is not None else e["bbox"][1],558,bottom if bottom is not None else e["bbox"][3]])
        self.rules[id]=dict(limit=rating!="electrical",constraints=terms,notes=[] if terms is not None else ["此行含未建模的测试设置，请核对原文与脚注；不自动判断全部测试条件。"])
    def finish(self):
        spec=profile(self.chip);first=self.pdf.pages[0].extract_text()
        if spec["revision"].split()[0] not in first:raise ValueError("手册修订号已变化，禁止复用旧整理")
        download=load_json(self.root/"source/download.json")
        sha=hashlib.sha256(pdf_path(self.chip).read_bytes()).hexdigest()
        raw=[]
        table_pages={e["page"] for e in self.evs.values()}
        for n,p in enumerate(self.pdf.pages,1):
            raw.append(dict(page=n,width=p.width,height=p.height,text=p.extract_text(x_tolerance=1) or "",
                lines=p.extract_text_lines(x_tolerance=1,return_chars=False),
                tables=[dict(bbox=list(t.bbox),cells=t.extract(x_tolerance=1)) for t in p.find_tables()] if n in table_pages else []))
        manifest=dict(doc_id=self.chip+"-"+spec["revision"].split()[0].lower(),chip_id=self.chip,manufacturer="TI",model=spec["name"],
            title=spec.get('title',self.chip.upper()),revision=spec["revision"],revision_date=spec["revision_date"],
            url=download["url"],downloaded_at=download["downloaded_at"],sha256=sha,pages=len(raw),indexed_core_pages=spec["core_pages"],pdf_file=spec["pdf"],
            extraction=dict(tool="pdfplumber",version=pdfplumber.__version__,x_tolerance=1),
            bbox_convention="PDF points (x0, top, x1, bottom), top-left origin; page numbers are 1-based")
        dump_json(self.root/"source/manifest.json",manifest)
        dump_json(self.root/"raw/pages.json",raw)
        dump_json(self.root/"curated/evidence_specs.json",[{k:v for k,v in e.items() if k not in ("text","context")} for e in self.evs.values()])
        dump_json(self.root/"processed/evidence.json",list(self.evs.values()))
        dump_json(self.root/"curated/parameters.json",self.params)
        dump_json(self.root/"curated/row_regions.json",dict(source_sha256=sha,regions=self.regions))
        dump_json(self.root/"curated/condition_rules.json",dict(source_sha256=sha,rules=self.rules))
        dump_json(self.root/"curated/review_log.json",dict(source_sha256=sha,manual_transcription=True,review=REVIEW,decisions=self.decisions,
            coverage="适用型号的绝对最大额定值、工作条件和电气特性；NE555 另含开关特性。排除项见 decisions；ESD、热阻和封装不是本轮结构化参数表。"))
        print(self.chip,len(self.params),"rows",len(self.evs),"groups",len(raw),"pages")
        self.pdf.close()

def lm2596():
    b=Builder("lm2596-adj")
    b.ev("abs",5,94,304,["绝对最大额定值","absolute maximum","极限电压"],"绝对最大额定值属于应力限制，不能作为正常工作范围。SD/SS、Delay、Flag 与本型号引脚表不一致，保留原文，暂不转录这些行。",[[54,312,558,380]])
    for id,sym,name,v,u,t0,t1,cond in [
        ("abs-vin","VIN","最大供电电压",(None,None,45),"V",138,151,"应力额定值"),
        ("abs-fb","VFB","反馈引脚应力电压",(-.3,None,25),"V",194,205,"相对 GND"),
        ("abs-output","VSW","输出开关引脚稳态电压（原表列）",(None,None,-1),"V",208,220,"原表 MAX 列为−1 V，按原列保留，解释待核对；不用于自动电压约束"),
        ("abs-pd","PD","功耗",(None,None,None),"",222,234,"原表合并限制栏：Internally limited；不是任意散热条件下的可用功率"),
        ("abs-lead-vapor","Tlead","引线温度：汽相",(None,None,215),"°C",237,249,"KTW；汽相 60 s"),
        ("abs-lead-ir","Tlead","引线温度：红外",(None,None,245),"°C",250,262,"KTW；红外 10 s"),
        ("abs-lead-solder","Tlead","引线焊接温度",(None,None,260),"°C",264,276,"NDZ；焊接 10 s；封装旧代码照录"),
        ("abs-tj","TJ","最大结温",(None,None,150),"°C",278,290,"应力额定值"),
        ("abs-storage","Tstg","储存温度",(-65,None,150),"°C",292,304,"储存，不代表工作温度")]:b.p(id,sym,name,v,u,cond,"abs",t0,t1,"absolute_maximum")
    b.decisions.append("第5页 SD/SS、Delay、Flag 引脚无法与第4页5引脚表对应，排除结构化答案及规则；原文完整保留。工作温度行未明确写 TA/TJ，按原表 Temperature 保存，不据此换算环境温度与结温。")
    b.ev("recommended",5,459,519,["推荐工作条件","推荐输入电压","供电范围","输入范围","工作温度","VIN","operating conditions"],"LM2596-ADJ 工作供电范围为 4.5–40 V；45 V 是绝对最大值。工作温度行原表未明确温度类型。")
    b.p("rec-vin","VIN","工作输入电压",(4.5,None,40),"V","Operating Conditions","recommended",493,505,"recommended")
    b.p("rec-temperature","Temperature","工作温度",(-40,None,125),"°C","原表 Temperature，未明确 TA/TJ","recommended",507,518,"recommended")
    b.ev("vfb",6,589,695,["反馈基准","反馈参考电压","VFB","VREF","参考电压"],"可调版本 VFB 的典型值为 1.23 V；室温和完整结温范围的保证上下限分别列出，且有输入、负载和输出设置条件。",[[54,703,558,733]])
    base=[between("vin",4.5,40),between("load_current",.2,3),eq("output_voltage",3)]
    b.p("vfb-25","VFB","反馈基准",(1.193,1.23,1.267),"V","TJ = 25°C；4.5≤VIN≤40 V；0.2≤ILOAD≤3 A；VOUT programmed for 3 V","vfb",647,670,terms=base+[eq("tj",25)])
    b.p("vfb-full","VFB","反馈基准",(1.18,None,1.28),"V","−40≤TJ≤125°C；4.5≤VIN≤40 V；0.2≤ILOAD≤3 A；VOUT programmed for 3 V","vfb",670,683,terms=base+[between("tj",-40,125)])
    b.p("efficiency","η","效率",(None,73,None),"%","VIN=12 V；VOUT=3 V；ILOAD=3 A；TJ=25°C；Figure 9-13 外部元件","vfb",684,695,notes=["典型效率不保证其他电路、负载或布局下的效率。"])
    context=[[54,99,558,151],[54,492,558,590]]
    groups=[("bias",169,195,["反馈偏置电流","Ib"],"反馈偏置电流须按结温条件读取。"),
        ("oscillator",197,223,["振荡频率","开关频率","fO","fOSC","频率范围"],"内部振荡器固定为标称 150 kHz；上下限随结温条件分别给出，不能使用 TPS40200 的外部 RC 公式。"),
        ("saturation",225,251,["饱和电压","VSAT"],"饱和电压测试采用手册脚注指定的强制导通设置。"),
        ("duty",252,278,["占空比","DC"],"表中 ON/OFF 占空比数值按原列保留，不能据此保证任意降压比。"),
        ("current-limit",281,307,["限流","过流阈值","ICL","current limit"],"ICL 是开关峰值限流参数，不是持续负载电流保证。"),
        ("leakage",309,334,["输出漏电流","漏电流","IL"],"输出漏电流使用强制关断且无外接二极管、电感、电容的测试设置。"),
        ("quiescent",337,357,["静态电流","工作电流","IQ"],"工作静态电流典型 5 mA；须保留脚注中的强制关断测试。"),
        ("standby",360,386,["待机电流","ISTBY","standby"],"待机电流的室温与全结温上限不同，VIN=40 V 且 ON/OFF=5 V。"),
        ("shutdown",389,456,["关闭控制","关闭阈值","ON/OFF","VIH","VIL","如何关闭"],"ON/OFF 低电平启用、高电平关闭。原表 VIH/VIL 名称照录，具体逻辑以 Low ON / High OFF 为准。"),
        ("logic-current",458,484,["ON/OFF输入电流","IH","逻辑输入电流"],"ON/OFF 输入电流分别对应 2.5 V 关闭和 0.5 V 启用。")]
    for id,t0,t1,aliases,summary in groups:b.ev(id,7,t0,t1,aliases,summary,context)
    default=[eq("vin",12),eq("load_current",.5)]
    rows=[
      ("ib-25","Ib","反馈偏置电流",(None,10,50),"nA","bias",170,181,[eq("feedback_voltage",1.3),eq("tj",25)]),
      ("ib-full","Ib","反馈偏置电流",(None,None,100),"nA","bias",181,194,[eq("feedback_voltage",1.3),between("tj",-40,125)]),
      ("fosc-25","fO","振荡频率",(127,150,173),"kHz","oscillator",198,209,[eq("tj",25)]),
      ("fosc-full","fO","振荡频率",(110,None,173),"kHz","oscillator",211,222,[between("tj",-40,125)]),
      ("vsat-25","VSAT","饱和电压",(None,1.16,1.4),"V","saturation",226,239,None),
      ("vsat-full","VSAT","饱和电压",(None,None,1.5),"V","saturation",240,250,None),
      ("duty-on","DC","最大 ON 占空比",(None,100,None),"%","duty",253,265,None),
      ("duty-off","DC","最小 OFF 占空比",(None,0,None),"%","duty",266,278,None),
      ("icl-25","ICL","峰值限流",(3.6,4.5,6.9),"A","current-limit",282,295,None),
      ("icl-full","ICL","峰值限流",(3.4,None,7.5),"A","current-limit",296,306,None),
      ("leakage-zero","IL","输出漏电流",(None,None,50),"μA","leakage",310,323,None),
      ("leakage-negative","IL","输出漏电流",(None,2,30),"mA","leakage",324,333,None),
      ("iq","IQ","工作静态电流",(None,5,10),"mA","quiescent",337,357,None),
      ("standby-25","ISTBY","待机电流",(None,80,200),"μA","standby",361,373,None),
      ("standby-full","ISTBY","待机电流",(None,None,250),"μA","standby",373,386,None),
      ("on-25","VIH","低电平启用阈值",(None,1.3,None),"V","shutdown",402,417,None),
      ("on-full","VIH","低电平启用阈值",(None,None,.6),"V","shutdown",417,429,None),
      ("off-25","VIL","高电平关闭阈值",(None,1.3,None),"V","shutdown",429,442,None),
      ("off-full","VIL","高电平关闭阈值",(2,None,None),"V","shutdown",443,455,None),
      ("logic-off","IH","关闭输入电流",(None,5,15),"μA","logic-current",459,469,[eq("on_off",2.5),eq("tj",25)]),
      ("logic-on","IL","启用输入电流",(None,.02,5),"μA","logic-current",472,483,[eq("on_off",.5),eq("tj",25)])]
    extra={"vsat-25":"TJ=25°C；IOUT=3 A；脚注(4)(5)","vsat-full":"−40≤TJ≤125°C；IOUT=3 A；脚注(4)(5)",
      "duty-on":"脚注(5) 强制开关导通","duty-off":"脚注(6) 强制开关关断","icl-25":"TJ=25°C；Peak current；脚注(4)(5)","icl-full":"−40≤TJ≤125°C；Peak current；脚注(4)(5)",
      "leakage-zero":"TJ=25°C；Output=0 V；VIN=40 V；脚注(4)(6)","leakage-negative":"TJ=25°C；Output=−1 V；脚注(4)(6)","iq":"TJ=25°C；VIN=12 V；ILOAD=500 mA；脚注(6)",
      "standby-25":"TJ=25°C；VIN=40 V；ON/OFF=5 V","standby-full":"−40≤TJ≤125°C；VIN=40 V；ON/OFF=5 V",
      "on-25":"TJ=25°C；Low (regulator ON)","on-full":"−40≤TJ≤125°C；Low (regulator ON)","off-25":"TJ=25°C；High (regulator OFF)","off-full":"−40≤TJ≤125°C；High (regulator OFF)"}
    for id,s,n,v,u,e,t0,t1,terms in rows:
        names={'feedback_voltage':('VFB','V'),'on_off':('ON/OFF','V'),'tj':('TJ','°C')}
        text=[]
        for term in terms or []:
            label,unit=names[term['field']]
            text.append(f"{term['low']}≤{label}≤{term['high']} {unit}" if term['op']=='range' else f"{label}={term['value']} {unit}")
        cond=extra.get(id,"VIN=12 V；ILOAD=500 mA；"+'；'.join(text))
        b.p(id,s,n,v,u,cond,e,t0,t1,terms=default+terms if terms is not None else None)
    b.ev("divider",28,222,405,["反馈分压","分压电阻","输出电压计算","输出公式","R1","R2"],"标称 VOUT≈1.23×(1+R2/R1)，R1 是 FB 到 GND 的下侧电阻，建议取 240 Ω–1.5 kΩ；R2 是输出到 FB 的上侧电阻。")
    b.ev("pins",4,78,414,["引脚","接线","pinout","引脚功能"],"5 引脚包括 VIN、开关 Output、GND、Feedback 和 ON/OFF。Output 是开关节点，不能当作滤波后的稳压输出。")
    b.ev("protection",3,123,179,["保护机制","过流后如何恢复","过流恢复","热关断"],"手册说明有两级降频限流和过温关断保护；此段未给出完整恢复时序，不能据此承诺恢复时间。")
    b.ev('vfb-note',7,71,93,['系统参数外部元件脚注'],'系统参数受外部二极管、电感与电容影响；系统性能按 Figure 9-13 测试设置读取。')
    b.evs['vfb-note']['context_only']=True
    for p in b.params:
        if p['id'] in ('vfb-25','vfb-full','efficiency'):p['evidence_ids'].append('vfb-note')
        if p['id'].endswith('-full'):
            p['notes'].append('TYP 只在 TJ=25°C 给出；全温行留空表示未单独给出全温典型值，不否认同组的室温典型值。')
    b.decisions.append('按温度拆行时，共享的室温典型值放入25°C行；全温保证限值行不伪造全温典型值，原始合并单元格在PDF与raw中保留。')
    b.finish()

def lm358():
    b=Builder("lm358")
    b.ev("abs",4,93,465,["绝对最大额定值","absolute maximum","极限电压"],"LM358 的最大供电压差为 32 V，应力限制不能替代 3–30 V 推荐工作范围。仅整理 LM358 适用行。",[[54,473,558,523]])
    for id,s,n,v,u,t0,t1,cond in [
      ("abs-vs","VS","供电压差",(None,None,32),"V",162,192,"总压差；原文 ±16 or 32 V"),
      ("abs-vid","VID","差分输入电压",(-32,None,32),"V",210,249,"IN+ 相对 IN−"),
      ("abs-vi","VI","单端输入应力电压",(-.3,None,32),"V",290,319,"Either input；原表数值"),
      ("abs-short","tSC","输出对地短路持续时间",(None,None,None),"s",337,358,"原表合并限制栏：Unlimited；一个放大器；TA≤25°C；VS≤15 V；不适用于输出短接正电源"),
      ("abs-ta","TA","环境温度",(0,None,70),"°C",402,412,"LM358；absolute maximum 表"),
      ("abs-tj","TJ","虚结温",(None,None,150),"°C",439,451,"应力额定值"),
      ("abs-storage","Tstg","储存温度",(-65,None,150),"°C",453,465,"储存条件")]:b.p(id,s,n,v,u,cond,"abs",t0,t1,"absolute_maximum")
    b.ev("recommended",5,76,273,["推荐工作条件","供电范围","推荐供电电压","工作温度","VS","环境温度"],"LM358 推荐总供电压差为 3–30 V，环境温度为 0–70°C；推荐共模范围为 V− 到 V+−2 V。",[[54,95,558,117]])
    b.p("rec-vs","VS","总供电压差",(3,None,30),"V","VS = V+−V−；LM358","recommended",144,165,"recommended")
    b.p("rec-vcm","VCM","推荐输入共模电压",("V−",None,"V+ − 2"),"V","LM358；推荐工作条件","recommended",182,194,"recommended")
    b.p("rec-ta","TA","推荐环境温度",(0,None,70),"°C","LM358；不是结温 TJ","recommended",229,244,"recommended")
    context=[[54,82,558,119],[54,702,558,732]]
    groups=[("vos",123,201,["输入失调电压","失调电压","VOS","失调温漂"],"LM358 的失调电压典型 3 mV，25°C 最大 7 mV，全环境温度最大 9 mV；不混入 LM358A 或 B 版数值。"),
      ("rejection",204,232,["电源抑制比","PSRR","通道隔离","串扰"],"电源抑制和通道隔离需按供电、频率与表头测试条件分别读取。"),
      ("common-mode",234,301,["输入共模范围","共模电压","VCM","CMRR","共模抑制比","输入能到电源吗"],"共模范围的 25°C 与全温条件分别列出；满足输入共模不等于输出可以到达同样电压。"),
      ("bias",303,428,["输入偏置电流","偏置电流","IB","IOS","输入失调电流"],"保留 LM358 偏置电流的负号和各温度行；负号表达电流方向，不把负数列当成通用幅值比较。"),
      ("noise",431,451,["输入噪声","en","噪声密度"],"输入噪声密度典型值在 1 kHz 条件给出，不是任意带宽的积分噪声。"),
      ("gain",454,486,["开环增益","AOL"],"开环增益的供电、输出范围、负载和温度条件须同时保留。"),
      ("frequency",488,520,["增益带宽积","带宽","GBW","压摆率","SR","slew rate"],"LM358 的 GBW 典型 0.7 MHz、压摆率典型 0.3 V/μs；它们不是保证的闭环带宽或输出能力。"),
      ("output-swing",523,578,["输出摆幅","输出电压范围","VO","能输出5V吗","轨到轨"],"输出离正负电源轨的余量与供电、负载和温度有关；不能合并成无条件轨到轨答案。"),
      ("output-current",580,659,["输出电流","IO","短路电流","ISC"],"源电流、灌电流和短路电流按方向与测试设置分别展示，不能直接当作持续负载保证。"),
      ("quiescent",662,695,["静态电流","IQ","供电电流"],"静态电流按每个放大器给出，且依赖供电、输出与零负载设置。")]
    for e,t0,t1,aliases,summary in groups:b.ev(e,10,t0,t1,aliases,summary,context)
    standard=[eq("supply_voltage",5),eq("ambient_temperature",25),eq("common_mode_voltage",0),eq("open_loop",True)]
    def terms(temp=25,vs=5,others=None):
        return ([between("ambient_temperature",0,70)] if temp=="full" else [eq("ambient_temperature",temp)])+([between("supply_voltage",5,30)] if vs=="range" else [eq("supply_voltage",vs)])+[eq("open_loop",True)]+(others if others is not None else [eq("common_mode_voltage",0)])
    rows=[
      ("vos-25","VOS","输入失调电压",(None,3,7),"mV","vos",134,146,"VS=5–30 V；TA=25°C；VCM=0 V；VO=1.4 V",terms(vs="range",others=[eq("common_mode_voltage",0),eq("output_voltage",1.4)])),
      ("vos-full","VOS","输入失调电压",(None,None,9),"mV","vos",146,156,"VS=5–30 V；0≤TA≤70°C；VCM=0 V；VO=1.4 V",terms("full","range",[eq("common_mode_voltage",0),eq("output_voltage",1.4)])),
      ("vos-drift","dVOS/dT","失调电压漂移",(None,7,None),"μV/°C","vos",180,190,"0≤TA≤70°C；VS=5 V；开环，VCM=0 V",terms("full")),
      ("psrr","PSRR","电源抑制比",(65,100,None),"dB","rejection",204,220,"VS=5–30 V；TA=25°C；开环，VCM=0 V",terms(vs="range")),
      ("separation","VO1/VO2","通道隔离",(None,120,None),"dB","rejection",222,232,"f=1–20 kHz；VS=5 V；TA=25°C；开环，VCM=0 V",standard+[between("signal_frequency",1000,20000)]),
      ("vcm-25","VCM","输入共模范围",("V−",None,"V+ − 1.5"),"V","common-mode",245,259,"VS=5–30 V；TA=25°C；LM358",terms(vs="range",others=[])),
      ("vcm-full","VCM","输入共模范围",("V−",None,"V+ − 2"),"V","common-mode",269,283,"VS=5–30 V；0≤TA≤70°C；LM358",terms("full","range",[])),
      ("cmrr","CMRR","共模抑制比",(65,80,None),"dB","common-mode",291,301,"VS=5–30 V；VCM=0 V；TA=25°C",terms(vs="range")),
      ("ib-25","IB","输入偏置电流",(None,-20,-250),"nA","bias",314,328,"VS=5 V；VO=1.4 V；TA=25°C；开环，VCM=0 V",terms(others=[eq("common_mode_voltage",0),eq("output_voltage",1.4)])),
      ("ib-full","IB","输入偏置电流",(None,None,-500),"nA","bias",327,336,"VS=5 V；VO=1.4 V；0≤TA≤70°C；开环，VCM=0 V",terms("full",others=[eq("common_mode_voltage",0),eq("output_voltage",1.4)])),
      ("ios-25","IOS","输入失调电流",(None,2,50),"nA","bias",361,374,"VS=5 V；VO=1.4 V；TA=25°C；开环，VCM=0 V",terms(others=[eq("common_mode_voltage",0),eq("output_voltage",1.4)])),
      ("ios-full","IOS","输入失调电流",(None,None,150),"nA","bias",373,383,"VS=5 V；VO=1.4 V；0≤TA≤70°C；开环，VCM=0 V",terms("full",others=[eq("common_mode_voltage",0),eq("output_voltage",1.4)])),
      ("ios-drift","dIOS/dT","失调电流漂移",(None,10,None),"pA/°C","bias",406,420,"VS=5 V；TA=25°C；开环，VCM=0 V",standard),
      ("noise","en","输入电压噪声密度",(None,40,None),"nV/√Hz","noise",441,451,"f=1 kHz；VS=5 V；TA=25°C；开环，VCM=0 V",standard+[eq("signal_frequency",1000)]),
      ("aol-25","AOL","开环电压增益",(25,100,None),"V/mV","gain",465,478,"VS=15 V；VO=1–11 V；RL≥2 kΩ；TA=25°C",terms(vs=15,others=[eq("common_mode_voltage",0),between("output_voltage",1,11),bound("load_resistance","ge",2000)])),
      ("aol-full","AOL","开环电压增益",(15,None,None),"V/mV","gain",477,486,"VS=15 V；VO=1–11 V；RL≥2 kΩ；0≤TA≤70°C",terms("full",15,[eq("common_mode_voltage",0),between("output_voltage",1,11),bound("load_resistance","ge",2000)])),
      ("gbw","GBW","增益带宽积",(None,.7,None),"MHz","frequency",499,509,"VS=5 V；TA=25°C；典型值，按表头",standard),
      ("sr","SR","压摆率",(None,.3,None),"V/μs","frequency",511,520,"G=+1；VS=5 V；TA=25°C；典型值",None),
      ("swing-high-2k","VO","离正电源轨余量",(None,None,4),"V","output-swing",534,544,"VS=30 V；RL=2 kΩ；0≤TA≤70°C",None),
      ("swing-high-10k","VO","离正电源轨余量",(None,2,3),"V","output-swing",546,556,"VS=30 V；RL≥10 kΩ；TA=25°C",None),
      ("swing-high-5v","VO","离正电源轨余量",(None,1.5,None),"V","output-swing",557,567,"VS=5 V；RL≥2 kΩ；TA=25°C",None),
      ("swing-low","VO","离负电源轨余量",(None,5,20),"mV","output-swing",569,578,"VS=5 V；RL≤10 kΩ；0≤TA≤70°C",None),
      ("source-25","IO","源输出电流",(-20,-30,None),"mA","output-current",580,604,"VS=15 V；VO=0 V；VID=1 V；TA=25°C",None),
      ("source-full","IO","源输出电流",(-10,None,None),"mA","output-current",604,614,"VS=15 V；VO=0 V；VID=1 V；0≤TA≤70°C",None),
      ("sink-25","IO","灌输出电流",(10,20,None),"mA","output-current",615,628,"VS=15 V；VO=15 V；VID=−1 V；TA=25°C",None),
      ("sink-full","IO","灌输出电流",(5,None,None),"mA","output-current",625,637,"VS=15 V；VO=15 V；VID=−1 V；0≤TA≤70°C",None),
      ("sink-low","IO","低输出电压灌电流",(12,30,None),"μA","output-current",638,648,"VID=−1 V；VO=200 mV；VS=5 V；TA=25°C",None),
      ("isc","ISC","短路电流",(None,"±40","±60"),"mA","output-current",649,659,"VS=10 V；VO=VS/2；TA=25°C",None),
      ("iq-5v","IQ","每放大器静态电流",(None,350,600),"μA","quiescent",672,686,"VS=5 V；VO=2.5 V；IO=0 A；0≤TA≤70°C",None),
      ("iq-30v","IQ","每放大器静态电流",(None,500,1000),"μA","quiescent",684,695,"VS=30 V；VO=15 V；IO=0 A；0≤TA≤70°C",None)]
    for id,s,n,v,u,e,t0,t1,cond,t in rows:
        notes=["所有典型值只在 TA=25°C 给出；数值列按原表保留。"]
        if id.startswith(("ib-","source-")):notes.append("负号表示原表电流方向，列名按原表保留，不将其重排为幅值上下界。")
        b.p(id,s,n,v,u,cond,e,t0,t1,terms=t,notes=notes)
    b.ev("pins",3,75,730,["引脚","引脚功能","接线","pinout"],"LM358 有两个运放通道；引脚图按 SOIC（D）顶视图显示，电源用 V+ 与 V− 表示。")
    b.decisions.append("只转录 LM358（无 A/B/BA 后缀）行及明确共享行；LM358A 的 SR/共同行保留，专属偏置、输出源电流 −60 mA 等排除。推荐共模范围第5页为 V− 至 V+−2 V，与第10页室温电气特性分开。")
    b.finish()

def ne555():
    b=Builder("ne555")
    b.ev("abs",4,93,237,["绝对最大额定值","absolute maximum","极限电压"],"NE555 的供电绝对最大值为 18 V；推荐供电为 4.5–16 V，二者不能互换。",[[54,245,558,293]])
    for id,s,n,v,u,t0,t1,cond in [
      ("abs-vcc","VCC","供电应力电压",(None,None,18),"V",141,153,"相对 GND"),
      ("abs-input","VI","输入应力电压",(None,None,"VCC"),"V",155,167,"CONT、RESET、THRES、TRIG；相对 GND"),
      ("abs-current","IO","输出应力电流",(None,None,"±225"),"mA",169,181,"±225 mA 在原表MAX列；保留列位置与双向含义"),
      ("abs-tj","TJ","虚结温",(None,None,150),"°C",183,195,"应力限制；不能替代 TA"),
      ("abs-storage","Tstg","储存温度",(-65,None,150),"°C",225,237,"储存条件")]:b.p(id,s,n,v,u,cond,"abs",t0,t1,"absolute_maximum")
    b.decisions.append("第4页 FK/JG 焊接额定条目不适用于本轮 NE555 支持的 D/P/PS/PW 封装，保留原文不转录。所有 SE555、SA555、NA555 专属行排除。")
    b.ev("recommended",4,399,542,["推荐工作条件","推荐供电电压","供电范围","工作温度","VCC","环境温度"],"NE555 推荐供电 4.5–16 V，环境温度 0–70°C。电气特性表另有 5–15 V 测试范围，不能把测试范围与推荐范围混为一谈。")
    b.p("rec-vcc","VCC","推荐供电",(4.5,None,16),"V","NE555；相对 GND","recommended",447,467,"recommended")
    b.p("rec-current","IO","推荐输出电流",(None,None,"±200"),"mA","原文MAX列为±200 mA；还需按输出电压与散热核对","recommended",475,487,"recommended")
    b.p("rec-ta","TA","环境温度",(0,None,70),"°C","NE555；Operating free-air temperature","recommended",503,522,"recommended")
    context5=[[54,329,558,373],[54,708,558,730]]
    specs=[("threshold",5,376,428,["阈值电压","THRES","threshold"],"THRES 阈值的典型值约为供电的 2/3，但保证范围须按 5 V、15 V 条件分别读取。"),
      ("threshold-current",5,430,442,["THRES电流","阈值输入电流"],"THRES 电流会影响定时电阻可用范围，见跨页脚注。"),
      ("trigger",5,445,527,["触发阈值","触发电压","TRIG","trigger"],"TRIG 典型阈值约为 VCC/3；NE555 的 5 V 与 15 V 参数行分别保留。"),
      ("trigger-current",5,529,554,["触发输入电流","TRIG电流"],"TRIG 输入电流在 TRIG=0 V 条件给出。"),
      ("reset",5,557,624,["复位阈值","RESET","复位电流","如何复位"],"RESET 低有效，并覆盖触发和阈值输入；电压与电流测试条件分开读取。"),
      ("discharge",5,627,653,["放电开关","DISCH","放电漏电流"],"DISCH 关断漏电和导通电压分别列出；导通电压在 5 V、8 mA 条件给出。"),
      ("control",6,119,201,["控制电压","CONT","control voltage"],"CONT 开路电压随供电条件变化，不能默认把外部控制电压接入后仍按开路值计算。"),
      ("output-low",6,203,471,["低电平输出电压","VOL","灌电流"],"输出低电平电压依赖供电和灌电流，200 mA 行只给典型值。"),
      ("output-high",6,474,589,["高电平输出电压","VOH","源电流","输出摆幅"],"NE555 高电平输出不能无条件视为等于 VCC；按供电和源电流读取。"),
      ("supply-current",6,591,700,["供电电流","静态电流","ICC","IQ"],"供电电流与输出高低状态、零负载和供电电压有关。"),
      ("switching",7,76,357,["定时温漂","定时电源敏感度","上升时间","下降时间","tr","tf"],"开关特性按设计或表征给出、非生产测试；单稳态与无稳态的元件设置和参数分别读取。")]
    for e,p,t0,t1,a,s in specs:
        ctx=context5 if p==5 else [[54,73,558,116],[54,708,558,730]] if p==6 else [[54,366,558,415]]
        # Cross-page footnote is represented explicitly in the context text.
        b.ev(e,p,t0,t1,a,s,ctx if not (p==5) else [[54,329,558,373]])
    for eid in ["threshold-current","threshold","trigger"]:
        b.evs[eid]["context"]+="\n跨页脚注（p.6）："+b.pdf.pages[5].crop([54,708,558,730]).extract_text()
    default=[between("vcc",5,15),eq("ambient_temperature",25)]
    def conds(vcc=None,extras=None):return ([eq("vcc",vcc)] if vcc is not None else [between("vcc",5,15)])+[eq("ambient_temperature",25)]+(extras or [])
    rows=[
      ("threshold-15","THRES","阈值电压",(8.8,10,11.2),"V","threshold",376,400,"VCC=15 V；TA=25°C",conds(15)),
      ("threshold-5","THRES","阈值电压",(2.4,3.3,4.2),"V","threshold",404,428,"VCC=5 V；TA=25°C",conds(5)),
      ("threshold-current","ITHRES","阈值输入电流",(None,30,250),"nA","threshold-current",430,442,"VCC=5–15 V；TA=25°C；见 p.6 脚注",default),
      ("trigger-15","TRIG","触发阈值",(4.5,5,5.6),"V","trigger",445,470,"VCC=15 V；TA=25°C",conds(15)),
      ("trigger-5","TRIG","触发阈值",(1.1,1.67,2.2),"V","trigger",488,512,"VCC=5 V；TA=25°C",conds(5)),
      ("trigger-current","ITRIG","触发输入电流",(None,.5,2),"μA","trigger-current",529,554,"TRIG=0 V；VCC=5–15 V；TA=25°C",conds(extras=[eq("trigger_voltage",0)])),
      ("reset-voltage","RESET","复位阈值",(.3,.7,1),"V","reset",557,581,"VCC=5–15 V；TA=25°C",default),
      ("reset-high-current","IRESET","复位输入电流",(None,.1,.4),"mA","reset",585,597,"RESET=VCC；VCC=5–15 V；TA=25°C",None),
      ("reset-low-current","IRESET","复位输入电流",(None,-.4,-1.5),"mA","reset",599,624,"RESET=0 V；VCC=5–15 V；TA=25°C",conds(extras=[eq("reset_voltage",0)])),
      ("discharge-off","IDISCH","放电关断漏电",(None,20,100),"nA","discharge",627,639,"DISCH off；VCC=5–15 V；TA=25°C",conds(extras=[eq("discharge_off",True)])),
      ("discharge-on","VDISCH","放电开关导通电压",(None,.15,.4),"V","discharge",641,653,"VCC=5 V；IO=8 mA；TA=25°C",conds(5,[eq("load_current",.008)])),
      ("control-15","CONT","开路控制电压",(9,10,11),"V","control",119,144,"CONT 开路；VCC=15 V；TA=25°C",conds(15,[eq("control_open",True)])),
      ("control-5","CONT","开路控制电压",(2.6,3.3,4),"V","control",161,185,"CONT 开路；VCC=5 V；TA=25°C",conds(5,[eq("control_open",True)])),
    ]
    for current,typ,maxi,t0,t1 in [(10,.1,.25,203,227),(50,.4,.75,255,279),(100,2,2.5,306,331),(200,2.5,None,357,369)]:
        rows.append((f"vol-15-{current}","VOL","低电平输出电压",(None,typ,maxi),"V","output-low",t0,t1,f"VCC=15 V；IOL={current} mA；TA=25°C",conds(15,[eq("load_current",current/1000)])))
    for current,typ,maxi,t0,t1 in [(5,.1,.35,395,419),(8,.15,.4,447,471)]:
        rows.append((f"vol-5-{current}","VOL","低电平输出电压",(None,typ,maxi),"V","output-low",t0,t1,f"VCC=5 V；IOL={current} mA；TA=25°C",conds(5,[eq("load_current",current/1000)])))
    for vcc,current,mi,typ,t0,t1 in [(15,-100,12.75,13.3,474,499),(15,-200,None,12.5,526,538),(5,-100,2.75,3.3,540,564)]:
        rows.append((f"voh-{vcc}-{abs(current)}","VOH","高电平输出电压",(mi,typ,None),"V","output-high",t0,t1,f"VCC={vcc} V；IOH={current} mA；TA=25°C",conds(vcc,[eq("load_current",current/1000)])))
    for vcc,state,typ,maxi,t0,t1 in [(15,"low",10,15,591,615),(5,"low",3,6,619,643),(15,"high",9,13,647,671),(5,"high",2,5,675,699)]:
        rows.append((f"icc-{vcc}-{state}","ICC","零负载供电电流",(None,typ,maxi),"mA","supply-current",t0,t1,f"VCC={vcc} V；output {state}；no load；TA=25°C",conds(vcc,[eq("output_state",state),eq("load_current",0)])))
    for id,s,n,v,u,e,t0,t1,cond,t in rows:b.p(id,s,n,v,u,cond,e,t0,t1,terms=t)
    switchrows=[
      ("timing-temp-mono","αt","定时温度系数",(None,50,None),"ppm/°C",135,163,"单稳态；TA=MIN–MAX；RA=2–100 kΩ；C=0.1 μF"),
      ("timing-temp-astable","αt","定时温度系数",(None,150,None),"ppm/°C",175,201,"无稳态；TA=MIN–MAX；RA=1–100 kΩ；C=0.1 μF"),
      ("timing-supply-mono","SVt","定时电源敏感度",(None,.1,.5),"%/V",210,233,"单稳态；RA=2–100 kΩ；C=0.1 μF；TA=25°C"),
      ("timing-supply-astable","SVt","定时电源敏感度",(None,.3,None),"%/V",246,270,"无稳态；RA=1–100 kΩ；C=0.1 μF；TA=25°C"),
      ("rise","tr","输出上升时间",(None,100,300),"ns",285,319,"CL=15 pF；TA=25°C；20%→80%"),
      ("fall","tf","输出下降时间",(None,100,300),"ns",323,356,"CL=15 pF；TA=25°C；80%→20%")]
    for id,s,n,v,u,t0,t1,cond in switchrows:b.p(id,s,n,v,u,cond+"；设计/表征，非生产测试","switching",t0,t1,notes=["VCC=5–15 V；此表按设计或表征给出，非生产测试。"])
    b.ev("monostable",11,76,395,["单稳态","单次脉冲","脉宽公式","1.1RC","monostable"],"单稳态标称脉宽约为 1.1×RA×C；应核对触发回高至少 10 μs 等时序条件，公式不能保证精度。")
    b.ev("astable",12,76,720,["无稳态","自激","频率公式","定时公式","占空比","RA","RB","astable"],"无稳态 tH≈0.693(RA+RB)C，tL≈0.693 RB C，f=1/(tH+tL)，输出高电平占空比=tH/(tH+tL)。手册建议频率不超过100 kHz以减小失真。")
    b.ev("pins",3,76,720,["引脚","引脚功能","接线","pinout"],"NE555：GND、TRIG、OUT、RESET、CONT、THRES、DISCH、VCC；RESET 低有效。仅显示8引脚 SOIC（D）顶视图。")
    b.ev('resistor-note',6,708,730,['定时电阻上限脚注'],'手册脚注给出特定供电下 RA+RB 的近似上限；不要对其他供电自动插值。')
    b.evs['resistor-note']['context_only']=True
    for p in b.params:
        if p['id']=='threshold-current':p['evidence_ids'].append('resistor-note')
    b.finish()

if __name__=="__main__":
    lm2596();lm358();ne555()
