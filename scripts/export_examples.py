from pathlib import Path
from tps_evidence.engine import query
from tps_evidence.rules import check
from tps_evidence.export import markdown_export,json_export
from tps_evidence.render import evidence_image

OUT=Path(__file__).resolve().parents[1]/"examples"
OUT.mkdir(exist_ok=True)
examples={
 "low-input":query("4.3 V 能正常工作吗？"),
 "feedback-reference":query("反馈参考电压 VFB 是多少？"),
 "rc-timing":check(dict(vdd="12 V",tj="25 °C",frequency="100 kHz",resistance="200 kΩ",capacitance="470 pF"))}
for name,result in examples.items():
 (OUT/f"{name}.md").write_text(markdown_export(result))
 (OUT/f"{name}.json").write_text(json_export(result))
 eid="timing" if name=="rc-timing" else result.evidence_ids[0]
 (OUT/f"{name}-evidence.png").write_bytes(evidence_image(eid))
print("Exported 3 reproducible examples, JSON/Markdown and source images.")
