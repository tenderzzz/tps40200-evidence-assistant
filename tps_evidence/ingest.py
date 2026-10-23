"""Preserve unedited PDF output and build geometry-aware evidence blocks."""
import hashlib
import re
from datetime import datetime, timezone
import pdfplumber
from .corpus import ROOT, PDF, load_json, dump_json, load_corpus, _cached_corpus

def ingest(chip_id="tps40200"):
    if chip_id!="tps40200":
        from .chips import profile
        profile(chip_id)
        from scripts.prepare_multichip import lm2596,lm358,ne555
        {'lm2596-adj':lm2596,'lm358':lm358,'ne555':ne555}[chip_id]()
        _cached_corpus.cache_clear()
        from .search import enhanced_index,plain_index
        enhanced_index.cache_clear();plain_index.cache_clear()
        return {'chip_id':chip_id,'sha256':load_corpus(chip_id)[0]['sha256']}
    specs=load_json(ROOT/"data/curated/evidence_specs.json")
    review=load_json(ROOT/"data/curated/review_log.json")
    sha=hashlib.sha256(PDF.read_bytes()).hexdigest()
    if sha != review["source_sha256"]:
        raise ValueError("该 PDF 尚未经过参数复核；先复核 curated 记录并更新 review_log 的哈希。")
    manifest_path=ROOT/"data/source/manifest.json"
    prior=load_json(manifest_path) if manifest_path.exists() else {}
    raw=[]; evidence=[]
    with pdfplumber.open(PDF) as pdf:
        if "SLUS659G" not in pdf.pages[0].extract_text():
            raise ValueError("仅支持 SLUS659G Rev. G。")
        for number,page in enumerate(pdf.pages,1):
            lines=page.extract_text_lines(x_tolerance=1,return_chars=False)
            # This output is intentionally not corrected; merged cells remain null.
            raw.append(dict(page=number,width=page.width,height=page.height,
                            text=page.extract_text(x_tolerance=1) or "",lines=lines,
                            tables=[dict(bbox=list(t.bbox),cells=t.extract(x_tolerance=1))
                                    for t in page.find_tables()]))
            if number>40:
                continue  # Packaging/order appendices are preserved raw, not indexed.
            body=[l for l in lines if 74<=l["top"]<735]
            group=[]; groups=[]
            for line in body:
                isheading=bool(re.match(r"^\d+(?:\.\d+)*\s+[A-Z]",line["text"]))
                if group and (line["top"]-group[-1]["bottom"]>9 or isheading or len(group)>=12):
                    groups.append(group);group=[]
                group.append(line)
            if group:groups.append(group)
            for i,g in enumerate(groups):
                # Curated table groups replace overlapping auto chunks in the enhanced index.
                top=min(l["top"] for l in g);bottom=max(l["bottom"] for l in g)
                overlap=any(s["page"]==number and top<s["bbox"][3] and bottom>s["bbox"][1] for s in specs)
                if overlap:continue
                text="\n".join(l["text"] for l in g)
                evidence.append(dict(id=f"auto-p{number}-{i}",page=number,printed_page=str(number),
                    bbox=[54,max(74,top-2),558,min(735,bottom+2)],title=f"手册第 {number} 页 / 原文段落",
                    text=text,curated=False))
        for s in specs:
            p=pdf.pages[s["page"]-1]
            for box in [s["bbox"]]+s["context_bboxes"]:
                x0,y0,x1,y1=box
                if not 0<=x0<x1<=p.width or not 0<=y0<y1<=p.height:
                    raise ValueError(f"Invalid bbox: {s['id']}")
            evidence.append(dict(s,text=p.crop(s["bbox"]).extract_text(x_tolerance=1) or "",
                                 context="\n".join(p.crop(b).extract_text(x_tolerance=1) or "" for b in s["context_bboxes"])))
        manifest=dict(doc_id="tps40200-slus659g",title="TPS40200 Wide Input Range Non-Synchronous Voltage Mode Controller",
            revision="SLUS659G (Rev. G)",revision_date="2014-11",url="https://www.ti.com/lit/ds/symlink/tps40200.pdf",
            downloaded_at=prior.get("downloaded_at",datetime.fromtimestamp(PDF.stat().st_mtime,timezone.utc).isoformat()),
            sha256=sha,pages=len(pdf.pages),indexed_core_pages=40,pdf_file=PDF.name,
            extraction=dict(tool="pdfplumber",version=pdfplumber.__version__,x_tolerance=1),
            bbox_convention="PDF points (x0, top, x1, bottom), top-left origin; page numbers are 1-based")
    dump_json(manifest_path,manifest)
    dump_json(ROOT/"data/raw/pages.json",raw)
    dump_json(ROOT/"data/processed/evidence.json",evidence)
    _cached_corpus.cache_clear()
    load_corpus() # Validate all records and the document checksum.
    return dict(pages=len(raw),evidence_blocks=len(evidence),sha256=sha)
