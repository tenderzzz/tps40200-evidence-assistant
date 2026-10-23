import hashlib
import json
from io import BytesIO
from PIL import Image
from tps_evidence.corpus import ROOT,PDF,load_corpus,load_json
from tps_evidence.engine import query
from tps_evidence.export import json_export,markdown_export
from tps_evidence.render import evidence_image

def test_document_and_all_parameter_links():
    manifest,ev,rows=load_corpus()
    assert len(rows)==43
    assert manifest["sha256"]==hashlib.sha256(PDF.read_bytes()).hexdigest()
    assert manifest["pages"]==52
    for row in rows:
        assert row.conditions and row.review and row.evidence_ids
        assert all(eid in ev and ev[eid].text.strip() for eid in row.evidence_ids)
    for e in ev.values():
        x0,y0,x1,y1=e.bbox
        assert 0<=x0<x1<=612 and 0<=y0<y1<=792

def test_columns_conditions_and_design_footnotes_are_not_lost():
    _,ev,rows=load_corpus();p={r.id:r for r in rows}
    assert (p["tmin-12"].minimum,p["tmin-12"].typical,p["tmin-12"].maximum)==(None,200,400)
    assert (p["dmax-100"].minimum,p["dmax-100"].typical,p["dmax-100"].maximum)==(93,95,None)
    assert (p["ocdf"].minimum,p["ocdf"].typical,p["ocdf"].maximum)==(None,None,2)
    assert "COMP=FB" in p["vfb-comp"].conditions
    assert "4.5 V < VDD < 52 V" in p["vfb-25"].conditions
    assert p["vfb-85"].maximum!=p["vfb-125"].maximum
    assert "design-note" in p["aol"].evidence_ids
    assert ev["design-note"].page==5 and ev["amplifier"].page==6

def test_raw_extraction_stays_separate_from_reviewed_data():
    raw=load_json(ROOT/"data/raw/pages.json")
    review=load_json(ROOT/"data/curated/review_log.json")
    assert raw[4]["tables"] and len(raw)==52
    assert review["manual_transcription"] is True
    assert review["source_sha256"]==load_corpus()[0]["sha256"]

def test_reference_image_and_export_provenance():
    image=Image.open(BytesIO(evidence_image("reference")))
    assert image.width>900 and image.height>180
    r=query("VFB")
    exported=json.loads(json_export(r))
    assert exported["evidence"][0]["id"]=="reference"
    assert exported["evidence"][0]["context"]
    assert exported["source"]["sha256"]==r.source_sha256
    md=markdown_export(r)
    assert "679" in md and "710" in md and "测试" in md and "SHA-256" in md

def test_unknown_or_incomplete_requests_do_not_invent_answers():
    assert query("").status=="invalid"
    assert query("4.3 能工作吗").status=="needs_information"
    assert query("LM2596 能工作吗").status=="unsupported"
    assert query("请从曲线读出精确值").status=="unsupported"
    assert query("做一盘番茄炒蛋").status=="not_found"
    r=query("VUVLO(off)")
    assert r.status=="answered" and any(p.id=="uvlo-off" for p in r.parameters)

def test_benchmark_split_has_no_shared_paraphrase_family():
    cases=load_json(ROOT/"data/benchmark.json")["cases"]
    assert len(cases)==60
    dev={c["family"] for c in cases if c["split"]=="dev"}
    test={c["family"] for c in cases if c["split"]=="holdout"}
    assert len(dev)==len(test)==30 and dev.isdisjoint(test)

def test_check_export_preserves_original_inputs_and_units():
    from tps_evidence.rules import check
    r=check({"vdd":"12000 mV","resistance":"0.2 MΩ","capacitance":"0.47 nF"})
    exported=json.loads(json_export(r))
    assert exported["result"]["inputs"]=={"vdd":"12000 mV","resistance":"0.2 MΩ","capacitance":"0.47 nF"}
    assert "0.2 MΩ" in markdown_export(r)

import pytest

@pytest.mark.parametrize("question",["输出 3.3 V 能工作吗？","栅极 8 V 能工作吗？","12 V 和 24 V 都能用吗？"])
def test_ambiguous_voltage_roles_do_not_become_input_voltage_checks(question):
    r=query(question)
    assert r.status=="needs_information" and not r.checks

def test_source_replacement_is_rejected_even_after_cache_warmup(monkeypatch,tmp_path):
    import pytest
    import tps_evidence.corpus as corpus
    corpus.load_corpus()
    replaced=tmp_path/"replacement.pdf"
    replaced.write_bytes(b"replaced document")
    monkeypatch.setattr(corpus,"PDF",replaced)
    with pytest.raises(ValueError,match="哈希"):
        corpus.load_corpus()
