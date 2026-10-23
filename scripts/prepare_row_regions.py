"""Per-row PDF coordinates, checked against the Rev.G table grid.

Merged cells are deliberately split at the printed horizontal row boundaries.
This adds navigation metadata without changing any transcribed parameter values.
"""
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
regions={}
def region(id,page,top,bottom):regions[id]={"page":page,"bbox":[54.14,top,557.76,bottom]}

for id,y0,y1 in [
 ("abs-vdd",138.21,151.35),("abs-rc-fb",151.35,164.55),("abs-ss",164.55,177.75),
 ("abs-comp",177.75,190.95),("abs-gdrv",190.95,204.15),("abs-tj",204.15,217.35),
 ("abs-lead",217.35,230.55),("rec-vdd",435.21,448.35),("rec-tj",448.35,461.55)]:region(id,4,y0,y1)
for id,y0,y1 in [
 ("vfb-comp",127.45,140.65),("vfb-25",140.65,153.85),("vfb-85",153.85,167.05),("vfb-125",167.05,180.25),
 ("gate-source",193.45,206.65),("gate-sink",206.65,219.85),("gate-voltage",219.85,233.05),
 ("iqq",246.25,259.45),("uvlo-on",272.65,285.85),("uvlo-off",285.85,299.05),("uvlo-hyst",299.05,312.25),
 ("rss-charge",325.45,347.65),("rss-discharge",347.65,369.85),("ss-reset",369.85,383.05),
 ("ilim-0",396.25,409.45),("ilim-40",409.45,422.65),("ocdf",422.65,435.85),("ilim-reset",435.85,449.05),
 ("fosc-range",462.25,475.45),("fosc-100",475.45,488.65),("fosc-300",488.65,501.85),
 ("line-high",501.85,515.05),("line-low",515.05,528.25),("ramp",528.25,541.45)]:region(id,5,y0,y1)
for id,y0,y1 in [
 ("tmin-12",131.85,145.05),("tmin-30",145.05,158.25),("dmax-100",158.25,171.45),
 ("dmax-300",171.45,184.65),("kpwm",184.65,206.85),("iib",220.05,233.25),
 ("aol",233.25,246.45),("gbwp",246.45,259.65),("comp-source",259.65,272.85),("comp-sink",272.85,286.05)]:region(id,6,y0,y1)
out={"source_sha256":"a3e23ec7367038ecd8f6ddbfc38392fcb87d997352eabb715b573de538a76240",
     "method":"Fixed PDF-point regions reviewed against the printed grid of pp.4-6; not automatic semantic extraction.","regions":regions}
(ROOT/"data/curated/row_regions.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
print(f"Prepared {len(regions)} parameter-row navigation regions.")
