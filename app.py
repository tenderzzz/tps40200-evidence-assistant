"""Local Streamlit workspace. No external model or network requests at runtime."""
import html
from pathlib import Path
import streamlit as st
from tps_evidence.corpus import ROOT, PDF, load_corpus, load_json
from tps_evidence.engine import query
from tps_evidence.rules import check
from tps_evidence.models import RATING_LABELS, STATUS_LABELS, RULE_LABELS
from tps_evidence.export import json_export, markdown_export, number
from tps_evidence.render import evidence_image

st.set_page_config(page_title="TPS40200 手册证据助手",page_icon="🔎",layout="wide")
st.markdown("""<style>
.stApp, .stApp button, .stApp input, .stApp textarea {font-family:'PingFang SC','Microsoft YaHei',sans-serif;}
.block-container {max-width:1480px;padding-top:2.2rem;padding-bottom:3rem;}
h1 {font-size:2.1rem!important;letter-spacing:-.035em;font-weight:650!important;}
h2 {font-size:1.35rem!important;} h3 {font-size:1.05rem!important;}
.bench-title {color:#126878;font-size:.95rem;margin:0 0 .4rem;}
.bench-subtitle {color:#536b79;margin-bottom:1.5rem;line-height:1.7;}
[data-testid="stSidebar"] {border-right:1px solid #d9e5eb;}
[data-testid="stDataFrame"] {background:white;}
[data-testid="stImage"] {background:white;border:1px solid #d9e5eb;padding:4px;}
.parameter-table {border-collapse:collapse;table-layout:fixed;width:100%;background:white;font-size:13px;}
.parameter-table th,.parameter-table td {padding:9px 7px;border-bottom:1px solid #d9e5eb;text-align:left;vertical-align:top;overflow-wrap:anywhere;}
.parameter-table th:first-child {width:55%;}.parameter-table th:not(:first-child){width:15%;}
.parameter-table .condition {color:#536b79;font-size:12px;line-height:1.6;margin-top:4px;}
button p {white-space:normal!important;}
button:focus-visible,input:focus-visible {outline:3px solid #126878!important;outline-offset:2px;}
@media(max-width:1100px){[data-testid="stHorizontalBlock"]{flex-direction:column!important;}[data-testid="stColumn"]{width:100%!important;flex:1 1 auto!important;}}
@media(max-width:720px){.block-container{padding-top:1.2rem;}h1{font-size:1.6rem!important;}}
</style>""",unsafe_allow_html=True)

try:manifest,EVIDENCE,PARAMETERS=load_corpus()
except (FileNotFoundError,ValueError) as e:
    st.error(f"证据库暂不可用：{e}")
    st.code("uv run tps-evidence ingest")
    st.stop()

st.sidebar.markdown("### TPS40200")
st.sidebar.caption("芯片手册证据助手 / 本地原型")
st.sidebar.radio("工作区",["查手册","检查条件","验证结果"],key="page")
st.sidebar.divider()
st.sidebar.markdown("**固定资料**\n\nTI SLUS659G / Rev. G\n\n2014 年 11 月修订")
st.sidebar.caption(f"手册 {manifest['pages']} 页；核心正文索引 40 页")
st.sidebar.caption(f"SHA-256 {manifest['sha256'][:16]}…")
st.sidebar.caption("在本机检索和计算，无需模型或 API 密钥。")

def choose(eid):st.session_state.selected_evidence=eid

def downloads(result,key):
    cols=st.columns(2)
    cols[0].download_button("导出 Markdown",markdown_export(result),"tps40200-evidence.md","text/markdown",key=key+"md",width="stretch")
    cols[1].download_button("导出 JSON",json_export(result),"tps40200-evidence.json","application/json",key=key+"json",width="stretch")

def citations(result,key):
    st.markdown("**查看原文证据**")
    if not result.evidence_ids:
        st.caption("当前没有可支持回答的证据。")
        return
    for eid in result.evidence_ids:
        e=EVIDENCE[eid]
        st.button(f"[{eid}] {e.title} · 第 {e.printed_page} 页",key=key+eid,
                  on_click=choose,args=(eid,),width="stretch")
    more=[h for h in result.hits if h.evidence_id not in result.evidence_ids]
    if more:
        with st.expander("其他检索结果"):
            st.caption("检索得分只用于排序，不表示结论可信度。")
            for h in more:
                e=EVIDENCE[h.evidence_id]
                st.button(f"{e.title}（第 {e.page} 页）",key=key+"more"+e.id,on_click=choose,args=(e.id,))

def source_panel(result,key):
    st.subheader("核对手册原文")
    all_ids=list(dict.fromkeys(result.evidence_ids+[h.evidence_id for h in result.hits]))
    if not all_ids:
        st.info("找到证据后，这里会显示原始页面与框选区域。")
        return
    selected=st.session_state.get("selected_evidence")
    if selected not in all_ids:selected=all_ids[0]
    e=EVIDENCE[selected]
    st.markdown(f"**{e.title}**")
    st.caption(f"PDF 物理页 {e.page} / 印刷页 {e.printed_page} · {'已整理证据' if e.curated else '自动提取段落'}")
    full=st.toggle("查看完整页面",key=key+"full")
    st.image(evidence_image(selected,not full),width="stretch",caption="蓝绿色框：引用区域；棕色框：相关表头或脚注。")
    with st.expander("原文文本、表头和脚注"):
        st.text(e.text)
        if e.context:
            st.markdown("**表头／脚注上下文**")
            st.text(e.context)
    st.download_button("下载完整手册 PDF",PDF.read_bytes(),PDF.name,"application/pdf",key=key+"pdf")
    st.caption("中文说明为本项目整理；英文原文与手册条件用于核对。")

def submit_query():
    st.session_state.query_result=query(st.session_state.question)
    st.session_state.selected_evidence=None

def example_query(question):
    st.session_state.question=question
    submit_query()

def timing_example():
    st.session_state.page="检查条件"
    for k,v in {"vdd":"12 V","tj":"25 °C","frequency":"100 kHz","resistance":"200 kΩ","capacitance":"470 pF","ambient_temperature":""}.items():st.session_state["point_"+k]=v
    st.session_state.check_result=check(dict(vdd="12 V",tj="25 °C",frequency="100 kHz",resistance="200 kΩ",capacitance="470 pF"))
    st.session_state.selected_evidence="timing"

def query_page():
    st.markdown('<div class="bench-title">从一个参数，找到它成立的条件。</div>',unsafe_allow_html=True)
    st.title("查手册，也查依据。")
    st.markdown('<div class="bench-subtitle">输入参数符号或工程问题，核对数值、测试条件与原文。支持 TPS40200 Rev. G。</div>',unsafe_allow_html=True)
    if "question" not in st.session_state:st.session_state.question="反馈参考电压 VFB 是多少？"
    if "query_result" not in st.session_state:st.session_state.query_result=query(st.session_state.question)
    left,right=st.columns([1.04,1],gap="large")
    with left:
        with st.form("search_form"):
            st.text_input("你想查什么？",key="question",placeholder="例如：VFB、过流后如何恢复")
            st.form_submit_button("查找证据",on_click=submit_query,type="primary",width="stretch")
        examples=st.columns(3)
        examples[0].button("低输入电压",on_click=example_query,args=("4.3 V 能正常工作吗？",),width="stretch")
        examples[1].button("反馈参考电压",on_click=example_query,args=("反馈参考电压 VFB 是多少？",),width="stretch")
        examples[2].button("RC 定时检查",on_click=timing_example,width="stretch")
        r=st.session_state.query_result
        st.caption(f"本次问题：{r.question}")
        st.subheader("条件检查结论" if r.checks else STATUS_LABELS[r.status])
        if r.status in ("invalid","unsupported","not_found","needs_information"):st.warning(r.answer)
        else:st.write(r.answer)
        if r.parameters:
            table='<table class="parameter-table"><thead><tr><th>参数与测试条件</th><th>MIN</th><th>TYP</th><th>MAX</th></tr></thead><tbody>'
            for p in r.parameters:
                label=html.escape(p.symbol+" / "+p.name)
                condition=html.escape(RATING_LABELS[p.rating]+"；"+p.conditions)
                cells=''.join('<td>'+html.escape(number(v)+((' '+p.unit) if v is not None else ''))+'</td>' for v in [p.minimum,p.typical,p.maximum])
                table+=f'<tr><td><strong>{label}</strong><div class="condition">{condition}</div></td>{cells}</tr>'
            st.markdown(table+'</tbody></table>',unsafe_allow_html=True)
            for note in dict.fromkeys(n for p in r.parameters for n in p.notes):st.caption(note)
        for n in r.notices:st.caption(n)
        if r.checks:
            missing=[c.title for c in r.checks if c.status=="needs_information"]
            if missing:st.caption("尚未检查，需补充相应条件："+"、".join(missing)+"。")
        citations(r,"query-ref-")
        st.divider();downloads(r,"query-")
    with right:source_panel(st.session_state.query_result,"query-source-")

def submit_check():
    st.session_state.check_result=check({k:st.session_state.get("point_"+k) or None for k in ["vdd","tj","frequency","resistance","capacitance","ambient_temperature"]})
    st.session_state.selected_evidence=None

def checks_page():
    st.title("逐项核对工作条件")
    st.write("填写已知条件，留空的项目会提示缺少的信息。数值请附单位。")
    left,right=st.columns([1.04,1],gap="large")
    with left:
        with st.form("condition_form"):
            a,b=st.columns(2)
            a.text_input("输入电压 VDD",key="point_vdd",placeholder="12 V")
            b.text_input("结温 TJ",key="point_tj",placeholder="25 °C")
            st.text_input("振荡频率 fOSC",key="point_frequency",placeholder="100 kHz")
            a,b=st.columns(2)
            a.text_input("定时电阻 RRC",key="point_resistance",placeholder="200 kΩ")
            b.text_input("定时电容 CRC",key="point_capacitance",placeholder="470 pF")
            with st.expander("只有环境温度？"):
                st.text_input("环境温度 TA（不会自动转换为结温）",key="point_ambient_temperature",placeholder="25 °C")
            st.form_submit_button("检查条件",on_click=submit_check,type="primary",width="stretch")
        if "check_result" not in st.session_state:
            st.session_state.check_result=check({})
        r=st.session_state.check_result
        st.subheader("检查结果")
        active=[c for c in r.checks if c.status!="needs_information"]
        for c in active:
            fn=st.success if c.status=="satisfied" else st.info if c.status=="estimated" else st.error
            fn(f"**{c.title} / {RULE_LABELS[c.status]}**\n\n{c.message}")
        pending=[c for c in r.checks if c.status=="needs_information"]
        if pending:
            with st.expander(f"待补充信息（{len(pending)} 项）",expanded=not active):
                for c in pending:st.write(f"**{c.title}**：{c.message}")
        for n in r.notices:st.caption(n)
        citations(r,"check-ref-");st.divider();downloads(r,"check-")
    with right:source_panel(st.session_state.check_result,"check-source-")

def validation_page():
    from tps_evidence.evaluate import evaluate,markdown_report
    st.title("结果怎样验证")
    st.write("60 个预定义案例，开发组与留出组各 30 个。对比原文检索与加入表格条件、人工别名后的检索。")
    report_path=ROOT/"reports/evaluation-all.json"
    if st.button("重新运行固定验证集"):
        r=evaluate("all");(ROOT/"reports/evaluation.md").write_text(markdown_report(r))
        st.success("固定验证集已重新运行。")
    if not report_path.exists():
        st.info("点击上方按钮运行验证，或在终端运行 uv run tps-evidence evaluate --split all。")
        return
    r=load_json(report_path)
    def pct(n):return "—" if n is None else f"{n:.1%}"
    table=[]
    for group,m in r["splits"].items():
        table.append({"分组":"开发组" if group=="dev" else "留出组","案例通过":f"{m['passed']}/{m['cases']}","证据前三命中":pct(m["top3_recall"]),"原文基线":pct(m["plain_top3_recall"]),"参数事实正确":pct(m["fact_accuracy"]),"参数回答覆盖":pct(m["fact_coverage"])})
    st.dataframe(table,hide_index=True,width="stretch")
    st.caption("证据命中只统计有预标注证据的查询题；参数正确率只统计给出参数回答的题目，覆盖率同时报告。")
    for limitation in r["limitations"]:st.write("• "+limitation)
    if r.get("benchmark_corrections"):
        with st.expander("首轮结果与验证数据修正"):
            st.write("首轮留出组 29/30 通过；1 个预期频率值抄算有误。独立复算后修正验证数据，计算引擎未修改。首轮输出已保留。")
    st.write("增强检索包含人工别名和整理说明。与原文基线的差异不能单独归因于分块方法。")
    failed=[c for c in r["cases"] if not c["passed"]]
    st.subheader("失败案例与能力边界")
    if failed:
        for c in failed:st.error(c["question"]+"："+"；".join(c["errors"]))
    else:st.write("本组固定案例未观察到失败。下列能力仍需要保留边界：")
    st.markdown("- 无别名的中文表述可能只返回相关原文或无结果。\n- 不自动把全部温度、电压条件收敛为唯一参数行。\n- 不读取曲线，也不为完整电路的稳定性或效率作保证。")
    with st.expander("查看每个案例"):
        st.dataframe([{"编号":c["id"],"分组":c["split"],"类别":c["category"],"问题":c["question"],"通过":c["passed"],"证据":", ".join(c["top3"])} for c in r["cases"]],hide_index=True,width="stretch")
    st.download_button("导出验证报告",markdown_report(r),"tps40200-validation.md","text/markdown")
    st.caption("资料复核由 Codex 对照原图完成，尚无独立第三方复核。")

{"查手册":query_page,"检查条件":checks_page,"验证结果":validation_page}[st.session_state.page]()
