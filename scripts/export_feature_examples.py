"""Generate reproducible v0.3 examples without adding user records."""
import json
from pathlib import Path
from tps_evidence.engine import query
from tps_evidence.rules import check
from tps_evidence.export import json_export, markdown_export
from tps_evidence.workbench import present
from tps_evidence.records import compare, comparison_markdown

OUT=Path(__file__).resolve().parents[1]/"examples"
point={"vdd":"12 V","tj":"25 °C","frequency":"100 kHz","resistance":"200 kΩ","capacitance":"470 pF","resistance_tolerance":"1%","capacitance_tolerance":"5%"}
conditions={"vdd":"12 V","temperature":"100 °C","temperature_kind":"test","frequency":"100 kHz"}
for name,result in [("vfb-conditions",query("VFB",conditions)),("rc-tolerance",check(point))]:
    (OUT/f"{name}.json").write_text(json_export(result)+"\n")
    (OUT/f"{name}.md").write_text(markdown_export(result))
def snapshot(id,name,point):return dict(id=id,name=name,created_at="2026-10-22T00:00:00+00:00",request=dict(kind="check",point=point),snapshot=present(check(point)))
comparison=compare(snapshot("example-a","示例：200 kΩ，1% / 5%",point),snapshot("example-b","示例：改为 1 kΩ",{**point,"resistance":"1 kΩ"}))
(OUT/"tolerance-comparison.json").write_text(json.dumps(comparison,ensure_ascii=False,indent=2)+"\n")
(OUT/"tolerance-comparison.md").write_text(comparison_markdown(comparison))
print("Exported filtered-query, tolerance and comparison examples; user storage untouched.")
