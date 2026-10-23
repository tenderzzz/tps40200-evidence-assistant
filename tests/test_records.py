import json
from concurrent.futures import ThreadPoolExecutor
import pytest
from tps_evidence import records
from tps_evidence.engine import query
from tps_evidence.rules import check
from tps_evidence.workbench import present

@pytest.fixture(autouse=True)
def local_store(monkeypatch,tmp_path):monkeypatch.setenv("TPS_RECORDS_HOME",str(tmp_path/"records"))

def saved(name="方案",**point):
    request=dict(kind="check",point=point)
    return records.save(name,request,present(check(point)))

def test_snapshots_persist_and_list_without_mutating_old_result():
    a=saved(vdd="12 V",resistance="200 kΩ",capacitance="470 pF")
    saved("修改方案",vdd="24 V",resistance="1 kΩ")
    reread=records.read(a["id"])
    assert reread["snapshot"]["result"]["inputs"]["vdd"]=="12 V"
    assert len(records.list_records())==2
    assert all(p.stat().st_mode & 0o077==0 for p in records.home().glob("*.json"))

def test_comparison_distinguishes_unit_notation_from_physical_change():
    a=saved(vdd="12 V",resistance="200 kΩ")
    b=saved(vdd="12000 mV",resistance="1 kΩ")
    comparison=records.compare(a,b)
    inputs={r["field"]:r for r in comparison["inputs"]}
    assert not inputs["vdd"]["changed"] and inputs["vdd"]["representation_changed"]
    assert inputs["resistance"]["changed"]
    current=next(r for r in comparison["checks"] if r["rule"]=="rc_current")
    assert current["changed"] and current["a"]["status"]=="satisfied" and current["b"]["status"]=="violated"

def test_filter_comparison_and_export_keep_conditions_and_sources():
    def snapshot(temp):
        request=dict(kind="query",question="VFB",conditions=dict(vdd="12 V",temperature=temp,temperature_kind="test",frequency="100 kHz"))
        return records.save(temp,request,present(query("VFB",request["conditions"])))
    comparison=records.compare(snapshot("25 °C"),snapshot("100 °C"))
    p=next(r for r in comparison["parameters"] if r["id"]=="vfb-85")
    assert p["changed"] and p["match_a"]["status"]=="applicable" and p["match_b"]["status"]=="not_applicable"
    text=records.comparison_markdown(comparison)
    assert "SHA-256" in text and "vfb-85" in text and "100 °C" in text

def test_corrupt_record_is_preserved_and_never_overwritten():
    a=saved();path=records.home()/f"{a['id']}.json";path.write_text("broken")
    with pytest.raises(ValueError,match="原文件已保留"):records.list_records()
    assert path.read_text()=="broken"

def test_parallel_saves_do_not_lose_records():
    payload=present(check({"vdd":"12 V"}));request=dict(kind="check",point={"vdd":"12 V"})
    with ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(lambda n:records.save(str(n),request,payload),range(8)))
    assert len(records.list_records())==8

@pytest.mark.parametrize("name",["", "  ", "x"*61, None])
def test_record_names_are_required_and_bounded(name):
    with pytest.raises(ValueError):saved(name)

def test_record_identifier_cannot_be_a_path():
    with pytest.raises(KeyError):records.read("../../source")
