"""Explicit, case-sensitive SI units. Decimal preserves inclusive boundaries."""
import re
from decimal import Decimal, InvalidOperation

UNITS={
 "voltage":{"V":"1","mV":"0.001"},
 "frequency":{"Hz":"1","kHz":"1000","MHz":"1000000"},
 "resistance":{"Ω":"1","ohm":"1","Ohm":"1","kΩ":"1000","kohm":"1000","MΩ":"1000000"},
 "capacitance":{"F":"1","mF":"0.001","μF":"0.000001","uF":"0.000001","nF":"1e-9","pF":"1e-12"},
 "temperature":{"°C":"1","C":"1"},
 "tolerance":{"%":"0.01"},
 "current":{"A":"1","mA":"0.001","μA":"0.000001","uA":"0.000001","nA":"1e-9"},
 "time":{"s":"1","ms":"0.001","μs":"0.000001","us":"0.000001","ns":"1e-9"},
}
NORMALIZE=str.maketrans({"µ":"μ","Ω":"Ω","℃":"°C","−":"-","，":","})
PATTERN=re.compile(r"^([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)\s*([^\d\s]+)$")

def quantity(text: str | None, dimension: str) -> Decimal | None:
    if text is None or not text.strip():return None
    text=text.strip().translate(NORMALIZE)
    m=PATTERN.fullmatch(text)
    if not m:
        raise ValueError("请输入有限数值并明确单位，例如 12 V、100 kHz、200 kΩ、470 pF、25 °C。")
    value,unit=m.groups()
    if unit not in UNITS[dimension]:
        raise ValueError(f"单位 {unit} 不适用于此项；可用：{'、'.join(UNITS[dimension])}。")
    try:result=Decimal(value)*Decimal(UNITS[dimension][unit])
    except InvalidOperation as e:raise ValueError("数值无效。") from e
    if not result.is_finite() or abs(result)>Decimal("1e30") or (result and abs(result)<Decimal("1e-30")):
        raise ValueError("数值超出可处理范围（非零绝对值限 1e-30 至 1e30）。")
    return result
