from fractions import Fraction
import pytest
from tps_evidence.rules import check

BASE={"vdd":"12 V","resistance":"200 kΩ","capacitance":"470 pF","resistance_tolerance":"1%","capacitance_tolerance":"5%"}
def checks(**values):return {c.rule:c for c in check({**BASE,**values}).checks}

def test_interval_endpoints_against_independent_fraction_arithmetic():
    rows=checks();r=rows["rc_tolerance_frequency"]
    nominal=Fraction(1,1)/(200000*Fraction(470,10**12)*Fraction(105,1000))/1000
    assert r.minimum==pytest.approx(float(nominal/Fraction(101,100)/Fraction(105,100)))
    assert r.maximum==pytest.approx(float(nominal/Fraction(99,100)/Fraction(95,100)))
    assert rows["rc_worst_current"].maximum==pytest.approx(float(Fraction(60,1)/Fraction(99,100)))
    assert "芯片自身误差未计入" in r.message

def test_zero_tolerance_collapses_to_nominal_and_includes_current_boundary():
    rows=checks(vdd="48 V",resistance="64 kΩ",resistance_tolerance="0%",capacitance_tolerance="0%")
    assert rows["rc_tolerance_frequency"].minimum==rows["rc_tolerance_frequency"].maximum
    assert rows["rc_worst_current"].value==750 and rows["rc_worst_current"].status=="satisfied"
    assert checks(vdd="48 V",resistance="64 kΩ")["rc_worst_current"].status=="violated"

@pytest.mark.parametrize("value",["-1%","100%","101%","NaN%","1","1 V"])
def test_invalid_percentage_cannot_produce_estimated_interval(value):
    r=checks(resistance_tolerance=value)["rc_tolerance_frequency"]
    assert r.status=="invalid" and "resistance_tolerance" in r.fields

def test_missing_tolerance_is_unknown_not_zero_and_c_does_not_affect_current():
    rows=checks(capacitance_tolerance="")
    assert rows["rc_tolerance_frequency"].status=="needs_information"
    assert rows["rc_worst_current"].status=="satisfied"
    assert checks(capacitance_tolerance="bad")["rc_worst_current"].maximum==rows["rc_worst_current"].maximum

def test_nominal_can_fit_but_tolerance_interval_cross_frequency_limit():
    rows=checks(resistance="200 kΩ",capacitance="100 pF",resistance_tolerance="5%",capacitance_tolerance="5%")
    assert rows["rc_range"].status=="satisfied"
    assert rows["rc_tolerance_range"].status=="violated"

@pytest.mark.parametrize("field,value",[("resistance","0 Ω"),("capacitance","-1 pF"),("vdd","-1 V")])
def test_invalid_nominal_components_or_supply_do_not_get_worst_case_pass(field,value):
    rows=checks(**{field:value})
    assert rows["rc_worst_current" if field=="vdd" else "rc_tolerance_frequency"].status=="invalid"
