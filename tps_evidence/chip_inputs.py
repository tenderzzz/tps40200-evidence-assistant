"""Strict per-chip schemas and explicit SI parsing with field-level issues."""
from functools import lru_cache
from pydantic import create_model,StrictBool
from .models import Model
from .chip_specs import input_fields
from .units import quantity

@lru_cache(maxsize=8)
def schema(chip_id,kind):
    return create_model(chip_id.replace('-','_')+'_'+kind,__base__=Model,**{
        f['name']:((StrictBool|None) if f['kind']=='boolean' else (str|None),None)
        for f in input_fields(chip_id,kind)})

def parse_inputs(data,chip_id,kind="check"):
    point=schema(chip_id,kind).model_validate(data).model_dump(exclude_none=True)
    parsed,errors={},{}
    for f in input_fields(chip_id,kind):
        key=f['name'];value=point.get(key)
        try:
            if f['dimension']:
                val=quantity(value,f['dimension'])
                if val is not None and f['dimension'] in ('resistance','capacitance') and val<=0:raise ValueError("电阻和电容必须大于零。")
                if val is not None and f['dimension']=='tolerance' and not 0<=val<1:raise ValueError("容差须为0%至小于100%，且明确填写%。")
                parsed[key]=val
            else:
                if f['choices'] and value not in (None,'') and value not in [c['value'] for c in f['choices']]:raise ValueError("请选择此项支持的模式或状态。")
                parsed[key]=value if value!='' else None
        except ValueError as e:errors[key]=str(e);parsed[key]=None
    return point,parsed,errors

def labels(chip_id,kind="check"):
    return {f['name']:f['label'] for f in input_fields(chip_id,kind)}
