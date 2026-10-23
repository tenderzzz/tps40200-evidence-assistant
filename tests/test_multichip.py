import hashlib
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from fractions import Fraction as F
from http.client import HTTPConnection
import pytest
from pydantic import ValidationError
from tps_evidence.chips import CHIPS,data_root,pdf_path
from tps_evidence.corpus import load_corpus,load_json
from tps_evidence.engine import query
from tps_evidence.rules import check
from tps_evidence.evaluate import evaluate
from tps_evidence.export import json_export,markdown_export
from tps_evidence.workbench import bootstrap,page_image,present
from tps_evidence import records

NEW=['lm2596-adj','lm358','ne555']

@pytest.mark.parametrize('chip',NEW)
def test_reviewed_records_source_and_region_integrity(chip):
    source,evidence,parameters=load_corpus(chip)
    assert source['chip_id']==chip and source['sha256']==hashlib.sha256(pdf_path(chip).read_bytes()).hexdigest()
    assert all(p.review and p.conditions for p in parameters)
    regions=load_json(data_root(chip)/'curated/row_regions.json')
    conditions=load_json(data_root(chip)/'curated/condition_rules.json')
    assert regions['source_sha256']==conditions['source_sha256']==source['sha256']
    assert set(regions['regions'])==set(conditions['rules'])=={p.id for p in parameters}
    for p in parameters:
        region=regions['regions'][p.id];x0,y0,x1,y1=region['bbox']
        assert 0<=x0<x1<=612 and 0<=y0<y1<=792
        assert any(evidence[e].page==region['page'] and evidence[e].bbox[1]<=y0<y1<=evidence[e].bbox[3] for e in p.evidence_ids),p.id
        assert all(evidence[e].text.strip() for e in p.evidence_ids)

@pytest.mark.parametrize('chip',NEW)
def test_sixty_source_bound_cases_and_group_isolation(chip):
    cases=load_json(data_root(chip)/'benchmark.json')['cases']
    assert len(cases)==60
    assert sum(c['split']=='dev' for c in cases)==sum(c['split']=='holdout' for c in cases)==30
    assert {c['family'] for c in cases if c['split']=='dev'}.isdisjoint({c['family'] for c in cases if c['split']=='holdout'})
    report=evaluate(save=False,chip_id=chip)
    assert report['metrics']['passed']==60,[(c['id'],c['errors']) for c in report['cases'] if not c['passed']]
    held=report['splits']['holdout']
    assert held['top3_recall']>=.9 and held['fact_accuracy']>=.95 and held['fact_coverage']>=.9

def test_shared_family_columns_and_merged_limits_are_preserved():
    lm={p.id:p for p in load_corpus('lm358')[2]}
    assert (lm['vos-25'].typical,lm['vos-25'].maximum,lm['vos-full'].maximum)==(3,7,9)
    assert (lm['ib-25'].typical,lm['ib-25'].maximum,lm['ib-full'].maximum)==(-20,-250,-500)
    assert lm['source-25'].minimum==-20 and lm['source-25'].typical==-30
    assert lm['gbw'].typical==.7 and lm['sr'].typical==.3
    assert lm['abs-short'].typical is None and 'Unlimited' in lm['abs-short'].conditions
    ne={p.id:p for p in load_corpus('ne555')[2]}
    assert (ne['rec-current'].minimum,ne['rec-current'].maximum)==(None,'±200')
    assert (ne['abs-current'].minimum,ne['abs-current'].maximum)==(None,'±225')
    assert (ne['reset-low-current'].typical,ne['reset-low-current'].maximum)==(-.4,-1.5)
    assert ne['voh-15-200'].typical==12.5 and ne['voh-15-200'].minimum is None
    assert ne['timing-temp-mono'].maximum is None
    buck={p.id:p for p in load_corpus('lm2596-adj')[2]}
    assert (buck['abs-output'].minimum,buck['abs-output'].maximum)==(None,-1)
    assert buck['abs-pd'].typical is None and 'Internally limited' in buck['abs-pd'].conditions
    assert not any('SD/SS' in p.symbol or 'Flag' in p.symbol for p in buck.values())

def test_cross_page_footnotes_have_their_own_citable_geometry():
    result=query('VFB',chip_id='lm2596-adj')
    assert {'vfb','vfb-note'}<=set(result.evidence_ids)
    data=json.loads(json_export(result));assert {e['page'] for e in data['evidence']}=={6,7}
    data=json.loads(json_export(query('THRES电流',chip_id='ne555')))
    assert {e['page'] for e in data['evidence']}=={5,6}
    assert query('系统参数外部元件脚注',chip_id='lm2596-adj').status=='evidence_only'

@pytest.mark.parametrize('chip,q',[
 ('tps40200','NE555 参数'),('tps40200','LM358 供电'),('lm2596-adj','LM2596-3.3 的反馈电压'),
 ('lm358','LM358B 的供电'),('lm358','LM358A 的参数'),('ne555','NE556 的供电'),('ne555','SA555 的温度'),('ne555','LMC555 的频率')])
def test_foreign_models_and_suffixes_are_never_reused(chip,q):
    r=query(q,chip_id=chip);assert r.status=='unsupported' and not r.parameters and not r.checks

def test_parallel_queries_keep_evidence_and_units_independent():
    tasks=[('tps40200','VFB','vfb-25',696,'mV'),('lm2596-adj','VFB','vfb-25',1.23,'V'),('lm358','VOS','vos-25',3,'mV'),('ne555','TRIG','trigger-5',1.67,'V')]*6
    def run(t):
        chip,q,pid,value,unit=t;r=query(q,chip_id=chip);p=next(p for p in r.parameters if p.id==pid)
        assert (r.chip_id,p.typical,p.unit)==(chip,value,unit)
        assert json.loads(json_export(r))['source']['sha256']==load_corpus(chip)[0]['sha256']
    with ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(run,tasks))

@pytest.mark.parametrize('chip',NEW)
def test_replaced_manual_is_rejected_after_all_caches_are_warm(chip,monkeypatch,tmp_path):
    import tps_evidence.chips as registry
    load_corpus(chip);bootstrap(chip)
    actual=registry.pdf_path;replacement=tmp_path/'replaced.pdf';replacement.write_bytes(b'new content')
    monkeypatch.setattr(registry,'pdf_path',lambda selected='tps40200':replacement if selected==chip else actual(selected))
    with pytest.raises(ValueError,match='哈希'):query('供电范围',chip_id=chip)
    with pytest.raises(ValueError,match='哈希'):page_image(4,chip)
    assert query('VFB').status=='answered'

@pytest.mark.parametrize('chip,point',[
 ('lm2596-adj',{'vdd':'12 V'}),('lm358',{'tj':'25 °C'}),('lm358',{'supply_voltage':'5 V'}),('ne555',{'resistance':'10 kΩ'})])
def test_input_schemas_do_not_accept_another_chips_fields(chip,point):
    with pytest.raises(ValidationError):check(point,chip_id=chip)

def test_lm358_room_temperature_row_is_separate_from_recommended_range():
    p=dict(supply_positive='5 V',supply_negative='0 V',ambient_temperature='25 °C',common_mode_voltage='3.5 V')
    rows={x.rule:x for x in check(p,chip_id='lm358').checks}
    assert rows['common_mode_recommended'].status=='violated'
    assert rows['common_mode_electrical'].status=='satisfied'
    p['ambient_temperature']='70 °C'
    assert next(x for x in check(p,chip_id='lm358').checks if x.rule=='common_mode_electrical').status=='violated'
    del p['ambient_temperature']
    assert next(x for x in check(p,chip_id='lm358').checks if x.rule=='common_mode_electrical').status=='needs_information'

def test_boolean_test_setting_is_not_parsed_as_a_decimal():
    p=dict(supply_voltage='5 V',ambient_temperature='25 °C',common_mode_voltage='0 V',output_voltage='1.4 V',open_loop=True)
    assert next(m for m in query('VOS',p,chip_id='lm358').applicability if m.parameter_id=='vos-25').status=='applicable'
    p['open_loop']=False
    assert next(m for m in query('VOS',p,chip_id='lm358').applicability if m.parameter_id=='vos-25').status=='not_applicable'

def test_ne555_independent_rational_timing_and_component_endpoints():
    p=dict(mode='astable',ra='10 kΩ',rb='20 kΩ',capacitance='10 nF',ra_tolerance='1%',rb_tolerance='2%',capacitance_tolerance='5%')
    rows={x.rule:x for x in check(p,chip_id='ne555').checks}
    assert rows['high_time'].value==pytest.approx(float(F(2079,10000)))
    assert rows['low_time'].value==pytest.approx(float(F(1386,10000)))
    assert rows['frequency'].value==pytest.approx(float(F(2000,693)))
    assert rows['duty'].value==60
    expected=[]
    for ra in [9900,10100]:
        for rb in [19600,20400]:
            for cap in [F(95,10**10),F(105,10**10)]:
                high=F(693,1000)*(ra+rb)*cap;low=F(693,1000)*rb*cap
                expected.append((1/(high+low)/1000,high/(high+low)*100))
    assert rows['tolerance_frequency'].minimum==pytest.approx(float(min(v[0] for v in expected)))
    assert rows['tolerance_frequency'].maximum==pytest.approx(float(max(v[0] for v in expected)))
    assert rows['tolerance_duty'].minimum==pytest.approx(float(min(v[1] for v in expected)))
    assert rows['tolerance_duty'].maximum==pytest.approx(float(max(v[1] for v in expected)))

@pytest.mark.parametrize('field,value',[('ra','0 Ω'),('rb','-1 kΩ'),('capacitance','0 F'),('ra','10'),('ra_tolerance','100%'),('capacitance_tolerance','-1%'),('ra','NaN Ω'),('ra','1e99 Ω')])
def test_ne555_invalid_components_never_produce_a_valid_interval(field,value):
    p=dict(mode='astable',vcc='5 V',ra='10 kΩ',rb='10 kΩ',capacitance='10 nF',ra_tolerance='1%',rb_tolerance='1%',capacitance_tolerance='5%');p[field]=value
    r=check(p,chip_id='ne555');assert r.status=='invalid'
    assert not any(x.rule=='tolerance_frequency' for x in r.checks)
    assert next(x for x in r.checks if x.rule=='vcc').status=='satisfied'

def test_ne555_missing_tolerance_is_unknown_and_mono_ignores_rb():
    p=dict(mode='astable',ra='10 kΩ',rb='10 kΩ',capacitance='10 nF',ra_tolerance='0%',capacitance_tolerance='0%')
    assert next(x for x in check(p,chip_id='ne555').checks if x.rule=='timing_tolerance').status=='needs_information'
    p['rb_tolerance']='0%';rows={x.rule:x for x in check(p,chip_id='ne555').checks}
    assert rows['tolerance_frequency'].minimum==rows['frequency'].value==rows['tolerance_frequency'].maximum
    p.update(mode='monostable',rb='-1 Ω',rb_tolerance='100%')
    r=check(p,chip_id='ne555');assert r.status=='answered'
    assert next(x for x in r.checks if x.rule=='pulse_width').value==.11
    assert not any(x.rule=='frequency' for x in r.checks)

def test_records_keep_chip_identity_legacy_bytes_and_cross_chip_snapshots(monkeypatch,tmp_path):
    monkeypatch.setenv('TPS_RECORDS_HOME',str(tmp_path))
    old=records.save('旧TPS',dict(kind='query',question='VFB'),present(query('VFB')))
    legacy=dict(old);legacy['schema_version']=1
    for key in ['chip_id','app_version']:legacy.pop(key,None)
    legacy['request'].pop('chip_id',None);legacy['snapshot']['result'].pop('chip_id',None)
    path=tmp_path/(old['id']+'.json');path.write_text(json.dumps(legacy));before=path.read_bytes()
    reread=records.read(old['id']);assert reread['chip_id']=='tps40200' and reread['request']['chip_id']=='tps40200'
    assert path.read_bytes()==before
    req=dict(kind='query',question='VOS',chip_id='lm358');new=records.save('LM358',req,present(query('VOS',chip_id='lm358')))
    assert new['schema_version']==2 and new['app_version']=='0.4.0'
    assert len(records.list_records('lm358'))==1
    c=records.compare(reread,new)
    assert not c['same_chip'] and not c['parameters'] and not c['checks'] and not c['inputs']
    assert c['snapshot_a']['source']['sha256']!=c['snapshot_b']['source']['sha256']
    md=records.comparison_markdown(c)
    assert 'LM358' in md and 'SLUS659G' in md and 'SLOS068AB' in md and 'SHA-256' in md

@pytest.fixture(scope='module')
def http():
    from tps_evidence.server import Handler,WorkbenchServer
    server=WorkbenchServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    def request(path,data=None):
        conn=HTTPConnection('127.0.0.1',server.server_port,timeout=20)
        conn.request('GET' if data is None else 'POST',path,None if data is None else json.dumps(data),{} if data is None else {'Content-Type':'application/json'})
        response=conn.getresponse();result=response.status,response.read();conn.close();return result
    yield request
    server.shutdown();server.server_close();thread.join(timeout=2)

def test_http_chip_catalogue_unknown_identity_and_selected_manual(http):
    status,body=http('/api/chips');chips=json.loads(body)['chips']
    assert status==200 and {c['id'] for c in chips}==set(CHIPS) and all(c['features'] for c in chips)
    assert http('/api/bootstrap?chip_id=not-a-chip')[0]==409
    assert http('/api/query',dict(question='VFB',chip_id='not-a-chip'))[0]==400
    images=[]
    for chip in ['tps40200','lm358']:
        status,body=http('/api/bootstrap?chip_id='+chip);b=json.loads(body)
        assert status==200 and b['initial']['result']['chip_id']==chip
        status,body=http('/api/pages/5.png?chip_id='+chip);assert status==200 and body.startswith(b'\x89PNG');images.append(body)
    assert images[0]!=images[1]
    assert http('/chip-ui.js')[0]==200

def test_http_check_save_export_preserve_chip_and_original_units(http,monkeypatch,tmp_path):
    monkeypatch.setenv('TPS_RECORDS_HOME',str(tmp_path))
    req=dict(kind='check',chip_id='lm2596-adj',point=dict(vin='12000 mV',r_lower='0.001 MΩ',r_upper='3000 Ω'))
    status,body=http('/api/check',req);payload=json.loads(body);assert status==200 and payload['result']['chip_id']=='lm2596-adj'
    status,body=http('/api/export',{**req,'format':'json'});assert status==200 and json.loads(body)['result']==payload['result']
    status,body=http('/api/records',dict(name='分压验证',request=req));record=json.loads(body)
    assert status==201 and record['chip_id']==record['request']['chip_id']=='lm2596-adj'
    assert record['snapshot']['result']['inputs']==req['point']
    assert len(json.loads(http('/api/records?chip_id=lm2596-adj')[1])['records'])==1
    assert json.loads(http('/api/records?chip_id=ne555')[1])['records']==[]
