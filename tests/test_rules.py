from decimal import Decimal
import pytest
from tps_evidence.rules import check
from tps_evidence.units import quantity

def rule(point,name):return next(c for c in check(point).checks if c.rule==name)

@pytest.mark.parametrize("value,status",[("4.4999 V","violated"),("4.5 V","satisfied"),("52 V","satisfied"),("52.0001 V","violated"),("-0.3 V","violated"),("4500 mV","satisfied")])
def test_recommended_voltage_inclusive_boundaries(value,status):
    assert rule({"vdd":value},"vdd").status==status

@pytest.mark.parametrize("value,status",[("-40 °C","satisfied"),("125 °C","satisfied"),("125.001 °C","violated"),("-40.001 °C","violated")])
def test_junction_bounds(value,status):assert rule({"tj":value},"tj").status==status

@pytest.mark.parametrize("value,status",[("35000 Hz","satisfied"),("0.5 MHz","satisfied"),("34.999 kHz","violated"),("500001 Hz","violated")])
def test_frequency_units(value,status):assert rule({"frequency":value},"frequency").status==status

def test_ambient_temperature_is_not_junction_temperature():
    r=rule({"ambient_temperature":"25 °C"},"tj")
    assert r.status=="needs_information" and "不能" in r.message

def test_exact_current_boundary_and_next_value():
    r=rule({"vdd":"48 V","resistance":"64 kΩ"},"rc_current")
    assert r.value==750 and r.status=="satisfied"
    assert rule({"vdd":"48 V","resistance":"63999 Ω"},"rc_current").status=="violated"

def test_nominal_formula_uses_farad_and_ohm():
    r=rule({"resistance":"200000 Ω","capacitance":"0.47 nF"},"rc_frequency")
    assert r.status=="estimated" and r.value==pytest.approx(101.3171225937)
    assert "不保证" in r.message

def test_frequency_with_independent_exact_rational_arithmetic():
    from fractions import Fraction
    expected=Fraction(1,1)/(68100*Fraction(470,10**12)*Fraction(105,1000))/1000
    r=rule({"resistance":"68.1 kΩ","capacitance":"470 pF"},"rc_frequency")
    assert r.value==pytest.approx(float(expected),rel=1e-12)

@pytest.mark.parametrize("field,value,name",[("resistance","0 Ω","rc_frequency"),("resistance","-1 kΩ","rc_current"),("capacitance","-1 pF","rc_frequency"),("resistance","200","rc_frequency"),("resistance","200 kHz","rc_frequency"),("vdd","NaN V","vdd"),("frequency","inf Hz","frequency"),("capacitance","1e-2000 F","rc_frequency")])
def test_invalid_inputs_are_not_calculated(field,value,name):
    point={"vdd":"12 V","resistance":"200 kΩ","capacitance":"470 pF"}
    point[field]=value
    assert rule(point,name).status=="invalid"

def test_partial_input_and_unrelated_errors():
    r=check({"vdd":"12 V","resistance":"200 kΩ","capacitance":"bad"})
    states={c.rule:c.status for c in r.checks}
    assert states["vdd"]=="satisfied" and states["rc_current"]=="satisfied"
    assert states["rc_frequency"]=="invalid" and states["tj"]=="needs_information"

def test_case_sensitive_prefixes_and_unicode_units():
    assert quantity("0.2 MΩ","resistance")==Decimal(200000)
    assert quantity("470 µF","capacitance")==Decimal("0.000470")
    assert quantity("−40 ℃","temperature")==Decimal(-40)
    with pytest.raises(ValueError):quantity("1 mHz","frequency")
