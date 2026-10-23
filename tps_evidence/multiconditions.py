"""Match only explicit conditions curated for the selected chip."""
from decimal import Decimal
from .chip_inputs import parse_inputs,labels
from .chips import data_root
from .corpus import load_corpus,load_json
from .models import ConditionMatch

def annotate(result,conditions):
    chip=result.chip_id
    raw,parsed,errors=parse_inputs(conditions,chip,'conditions');names=labels(chip,'conditions')
    source,_,_=load_corpus(chip);spec=load_json(data_root(chip)/'curated/condition_rules.json')
    if spec['source_sha256']!=source['sha256']:raise ValueError('条件整理与手册版本不一致，请重新复核。')
    matches=[]
    for p in result.parameters:
        rule=spec['rules'][p.id]
        if rule['limit'] or rule['constraints'] is None:
            matches.append(ConditionMatch(parameter_id=p.id,status='not_evaluated',reasons=rule['notes'] or ['这是额定或推荐限制，请在条件检查页判断；不作为电气特性测试行筛选。'],evidence_ids=p.evidence_ids));continue
        failed,missing,invalid=[],[],[]
        for term in rule['constraints']:
            key=term['field'];value=parsed.get(key);name=names[key]
            if key in errors:invalid.append(name+'：'+errors[key]);continue
            if value is None:missing.append('待确认 '+name+'。');continue
            expected=term.get('value');op=term['op']
            if isinstance(expected,(int,float)) and not isinstance(expected,bool):expected=Decimal(str(expected))
            okay=(value==expected) if op=='eq' else (Decimal(str(term['low']))<=value<=Decimal(str(term['high']))) if op=='range' else value>=expected if op=='ge' else value<=expected
            if not okay:failed.append('不符合 '+name+' 的原表条件。')
        status='invalid' if invalid else 'not_applicable' if failed else 'needs_information' if missing else 'applicable'
        matches.append(ConditionMatch(parameter_id=p.id,status=status,reasons=invalid+failed+missing or ['已提供条件符合此行已整理的表头与行条件；典型值仍只按原表注明的温度有效。'],evidence_ids=p.evidence_ids))
    result.condition_inputs=raw;result.condition_errors=errors;result.applicability=matches
    if errors:result.status='invalid';result.answer='筛选条件需要修改；原始参数行保留。'
    result.notices.append('没有提供的测试设置不会默认满足。TA、TJ 与芯片型号分别匹配；多个适用行不自动合并。')
    return result
