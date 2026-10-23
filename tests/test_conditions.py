import json
import pytest
from tps_evidence.corpus import ROOT, load_corpus, load_json
from tps_evidence.engine import query
from tps_evidence.export import json_export, markdown_export

BASE={"vdd":"12 V","temperature":"25 °C","temperature_kind":"test","frequency":"100 kHz"}
def matches(question="VFB", **conditions):
    return {m.parameter_id:m for m in query(question,{**BASE,**conditions}).applicability}

def test_reference_rows_keep_overlapping_guarantees_separate():
    r=query("VFB",BASE)
    m={x.parameter_id:x.status for x in r.applicability}
    assert m=={"vfb-comp":"needs_information","vfb-25":"applicable","vfb-85":"applicable","vfb-125":"applicable"}
    assert len(r.parameters)==4
    assert [p.maximum for p in r.parameters]==[702,703,708,710]

@pytest.mark.parametrize("kind",["ambient","junction"])
def test_single_temperature_does_not_assert_test_ta_equals_tj(kind):
    assert all(m.status=="needs_information" for m in matches(temperature_kind=kind).values())

def test_temperature_kind_must_be_explicit_in_api_requests():
    r=query("VFB",{"vdd":"12 V","temperature":"25 °C","frequency":"100 kHz"})
    assert all(m.status=="needs_information" for m in r.applicability)
    assert r.condition_inputs["temperature_kind"]=="unknown"

@pytest.mark.parametrize("temperature,expected",[("100 °C",{"vfb-125"}),("85 °C",{"vfb-125"}),("125 °C",set()),("-40 °C",set())])
def test_printed_temperature_endpoints_are_strict(temperature,expected):
    assert {id for id,m in matches(temperature=temperature).items() if m.status=="applicable"}==expected

@pytest.mark.parametrize("voltage",["4.5 V","52 V"])
def test_electrical_test_bounds_are_not_recommended_inclusive_bounds(voltage):
    m=matches(vdd=voltage)
    assert all(m[id].status=="not_applicable" for id in ("vfb-25","vfb-85","vfb-125"))

def test_units_and_explicit_comp_connection():
    m=matches(vdd="12000 mV",frequency="0.1 MHz",comp_equals_fb=True)
    assert all(row.status=="applicable" for row in m.values())
    assert matches(comp_equals_fb=False)["vfb-comp"].status=="not_applicable"

def test_missing_frequency_and_invalid_units_do_not_become_matches():
    assert all(m.status=="needs_information" for m in matches(frequency="").values())
    r=query("VFB",{**BASE,"vdd":"12"})
    assert r.status=="invalid" and all(m.status=="invalid" for m in r.applicability)

def test_load_capacitance_is_not_timing_capacitance():
    m=matches("最大占空比",capacitance="470 pF")
    assert m["dmax-100"].status=="needs_information"
    assert matches("最大占空比",load_capacitance="0.47 nF")["dmax-100"].status=="applicable"

def test_oscillator_rows_match_rc_not_the_frequency_being_measured():
    m=matches("振荡频率",resistance="68.1 kΩ",capacitance="470 pF")
    assert m["fosc-300"].status=="applicable"
    assert m["fosc-100"].status=="not_applicable"
    assert m["fosc-range"].status=="not_evaluated"

def test_every_reviewed_row_has_version_bound_condition_metadata():
    manifest,_,ps=load_corpus();rules=load_json(ROOT/"data/curated/condition_rules.json")
    assert rules["source_sha256"]==manifest["sha256"]
    assert set(rules["rules"])=={p.id for p in ps}

def test_filtered_export_keeps_facts_conditions_and_exclusion_reasons():
    r=query("VFB",{**BASE,"temperature":"100 °C"})
    exported=json.loads(json_export(r))["result"]
    assert exported["condition_inputs"]["temperature"]=="100 °C"
    assert len(exported["parameters"])==4
    assert "条件不符" in markdown_export(r) and "vfb-125" in markdown_export(r)
