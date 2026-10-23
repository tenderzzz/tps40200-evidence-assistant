"""Source-derived expected facts, independent of query/check implementation.

These are self-authored regression cases, not a third-party blind benchmark.
All numeric expectations below are literal transcriptions or rational arithmetic.
No engine call or curated-parameter lookup is used to generate expectations.
"""
from fractions import Fraction
from tps_evidence.corpus import dump_json,load_json
from tps_evidence.chips import data_root

class Cases:
    def __init__(self,chip):self.chip=chip;self.cases=[]
    def q(self,split,q,eid=None,pid=None,facts=None,status='answered',conditions=None,matches=None,family=None):
        exp=dict(status=status,facts={pid:facts} if pid else {},contains=[],evidence=[eid] if eid else [])
        if matches:exp['applicability']=matches
        c=dict(id=f'{self.chip}-{len(self.cases)+1:02}',kind='query',question=q,split=split,
            category='conditions' if conditions is not None else 'parameter' if pid else 'unsupported' if status=='unsupported' else 'unanswerable' if status in ('not_found','needs_information') else 'mechanism',
            family=family or ('query-'+(eid or q)),expected=exp)
        if conditions is not None:c['conditions']=conditions
        self.cases.append(c)
    def rule(self,point,rule,status,eid,value=None,split='holdout'):
        self.cases.append(dict(id=f'{self.chip}-{len(self.cases)+1:02}',kind='check',point=point,split=split,category='rule',family='rule-'+rule,
            expected=dict(rule=rule,rule_status=status,value=float(value) if value is not None else None,evidence=[eid])))
    def done(self):
        for split in ['dev','holdout']:assert sum(c['split']==split for c in self.cases)==30,(self.chip,split,len([c for c in self.cases if c['split']==split]))
        assert {c['family'] for c in self.cases if c['split']=='dev'}.isdisjoint({c['family'] for c in self.cases if c['split']=='holdout'})
        root=data_root(self.chip)
        dump_json(root/'benchmark.json',dict(source_sha256=load_json(root/'source/manifest.json')['sha256'],
            provenance='固定PDF对照转录与有理数计算期望；未从被测实现生成。自建开发/留出分组，不是独立盲测。',cases=self.cases))
        print(self.chip,len(self.cases))

def lm2596():
    b=Cases('lm2596-adj')
    for q in ['VFB','反馈参考电压是多少','反馈基准的上下限']:
        b.q('dev',q,'vfb','vfb-25',dict(minimum=1.193,typical=1.23,maximum=1.267,unit='V'))
    for q in ['推荐输入电压','工作温度']:
        b.q('dev',q,'recommended','rec-vin',dict(minimum=4.5,maximum=40))
    for q in ['ICL','峰值限流']:
        b.q('dev',q,'current-limit','icl-25',dict(minimum=3.6,typical=4.5,maximum=6.9))
    for q in ['IQ','工作静态电流']:
        b.q('dev',q,'quiescent','iq',dict(typical=5,maximum=10,unit='mA'))
    for q in ['ISTBY','待机电流']:
        b.q('dev',q,'standby','standby-full',dict(typical=None,maximum=250,unit='μA'))
    for q in ['Ib','反馈偏置电流']:
        b.q('dev',q,'bias','ib-25',dict(typical=10,maximum=50,unit='nA'))
    for q in ['VSAT','饱和电压']:
        b.q('dev',q,'saturation','vsat-full',dict(typical=None,maximum=1.5))
    for q in ['反馈分压','R1']:
        b.q('dev',q,'divider',status='evidence_only')
    b.q('dev','引脚功能','pins',status='evidence_only')
    base=dict(vin='12 V',tj='25 °C',load_current='0.5 A',output_voltage='3 V')
    for changes,expected in [({},dict(**{'vfb-25':'applicable','vfb-full':'applicable'})),
        ({'tj':'100 °C'},{'vfb-25':'not_applicable','vfb-full':'applicable'}),
        ({'tj':None},{'vfb-25':'needs_information'}),
        ({'load_current':'100 mA'},{'vfb-25':'not_applicable'}),
        ({'vin':'4.4 V'},{'vfb-full':'not_applicable'}),
        ({'output_voltage':'5 V'},{'vfb-25':'not_applicable'})]:
        b.q('dev','VFB','vfb','vfb-full',dict(minimum=1.18,maximum=1.28),conditions={**base,**changes},matches=expected)
    b.q('dev','η','vfb','efficiency',dict(typical=73,maximum=None,unit='%'))
    b.q('dev','VFB','vfb',conditions={**base,'vin':'12000 mV','load_current':'500 mA'},matches={'vfb-25':'applicable'})
    b.q('dev','VFB','vfb',status='invalid',conditions={**base,'vin':'12'},matches={'vfb-25':'invalid'})
    for q in ['qzxw987654','做一盘番茄炒蛋']:b.q('dev',q,status='not_found',family='unknown-dev')
    b.q('dev','MP1584 的参考电压是多少',status='unsupported',family='foreign-dev')
    for q in ['fO','振荡频率','开关频率上下限']:
        b.q('holdout',q,'oscillator','fosc-full',dict(minimum=110,typical=None,maximum=173,unit='kHz'))
    for q in ['ON/OFF','关闭控制阈值']:
        b.q('holdout',q,'shutdown','on-full',dict(maximum=.6))
    b.q('holdout','逻辑输入电流','logic-current','logic-off',dict(typical=5,maximum=15,unit='μA'))
    for q in ['输出漏电流','漏电流']:
        b.q('holdout',q,'leakage','leakage-negative',dict(typical=2,maximum=30,unit='mA'))
    for q in ['绝对最大额定值','极限电压']:
        b.q('holdout',q,'abs','abs-vin',dict(maximum=45))
    for text,status in [('4.5 V','satisfied'),('40 V','satisfied'),('4.499 V','violated'),('40.001 V','violated'),('45 V','violated'),('4500 mV','satisfied')]:b.rule(dict(vin=text),'vin',status,'recommended')
    for text,status in [('240 Ω','satisfied'),('1.5 kΩ','satisfied'),('239 Ω','violated'),('1501 Ω','violated')]:b.rule(dict(r_lower=text),'divider_r1',status,'divider')
    for point,status in [(dict(r_lower='0 Ω',r_upper='3 kΩ'),'invalid'),(dict(r_lower='1 kΩ',r_upper='-1 Ω'),'invalid'),(dict(r_lower='1 kΩ'),'needs_information')]:b.rule(point,'divider_voltage',status,'divider')
    b.rule(dict(r_lower='1000 Ω',r_upper='0.003 MΩ'),'divider_voltage','estimated','divider',Fraction(492,100))
    for q in ['LM2596-5 的电压','LM358 参数','从曲线读出精确值','生成完整电路BOM']:b.q('holdout',q,status='unsupported',family='unsupported-holdout')
    b.q('holdout','输入4.3能工作吗',status='needs_information',family='missing-unit')
    b.q('holdout','qzxw555000',status='not_found',family='unknown-holdout');b.done()

def lm358():
    b=Cases('lm358')
    for q in ['VOS','输入失调电压','失调电压是多少']:b.q('dev',q,'vos','vos-25',dict(typical=3,maximum=7,unit='mV'))
    for q in ['推荐工作条件','供电范围']:b.q('dev',q,'recommended','rec-vs',dict(minimum=3,maximum=30))
    for q in ['IB','输入偏置电流']:b.q('dev',q,'bias','ib-25',dict(typical=-20,maximum=-250,unit='nA'))
    for q in ['输入噪声','噪声密度']:b.q('dev',q,'noise','noise',dict(typical=40,unit='nV/√Hz'))
    for q in ['AOL','开环增益']:b.q('dev',q,'gain','aol-full',dict(minimum=15,typical=None))
    for q in ['输出摆幅','输出电压范围']:b.q('dev',q,'output-swing','swing-high-10k',dict(typical=2,maximum=3))
    for q in ['IQ','静态电流']:b.q('dev',q,'quiescent','iq-5v',dict(typical=350,maximum=600,unit='μA'))
    for q in ['IO','输出电流']:b.q('dev',q,'output-current','source-25',dict(minimum=-20,typical=-30,maximum=None))
    for q in ['PSRR','电源抑制比']:b.q('dev',q,'rejection','psrr',dict(minimum=65,typical=100,unit='dB'))
    b.q('dev','通道隔离','rejection','separation',dict(typical=120))
    base=dict(supply_voltage='5 V',ambient_temperature='25 °C',common_mode_voltage='0 V',output_voltage='1.4 V',open_loop=True)
    for changes,expected,status in [({}, {'vos-25':'applicable'},'answered'),({'ambient_temperature':'70 °C'},{'vos-25':'not_applicable','vos-full':'applicable'},'answered'),({'open_loop':None},{'vos-25':'needs_information'},'answered'),({'ambient_temperature':None},{'vos-25':'needs_information'},'answered'),({'supply_voltage':'35 V'},{'vos-full':'not_applicable'},'answered'),({'ambient_temperature':'25 K'},{'vos-25':'invalid'},'invalid')]:
        b.q('dev','VOS','vos',conditions={**base,**changes},matches=expected,status=status)
    for q in ['引脚','接线']:b.q('dev',q,'pins',status='evidence_only')
    for q in ['qzxw987654','做一盘番茄炒蛋']:b.q('dev',q,status='not_found',family='unknown-dev')
    for q in ['GBW','增益带宽积']:b.q('holdout',q,'frequency','gbw',dict(typical=.7,unit='MHz'))
    for q in ['SR','压摆率']:b.q('holdout',q,'frequency','sr',dict(typical=.3,unit='V/μs'))
    for q in ['VCM','输入共模范围']:b.q('holdout',q,'common-mode','vcm-full',dict(minimum='V−',maximum='V+ − 2'))
    for q in ['绝对最大额定值','极限电压','absolute maximum']:b.q('holdout',q,'abs','abs-vs',dict(maximum=32))
    b.q('holdout','输入失调电流漂移','bias','ios-drift',dict(typical=10,unit='pA/°C'),family='ios-drift')
    # Different requests from the input-bias questions; no paraphrase crosses splits.
    b.cases[-1]['family']='query-ios-drift'
    for pos,neg,status in [('3 V','0 V','satisfied'),('15 V','-15 V','satisfied'),('30.001 V','0 V','violated'),('2.999 V','0 V','violated'),('0 V','0 V','invalid'),('0 V','5 V','invalid'),('5000 mV','0 V','satisfied')]:b.rule(dict(supply_positive=pos,supply_negative=neg),'supply_voltage',status,'recommended')
    for ta,status in [('0 °C','satisfied'),('70 °C','satisfied'),('-0.01 °C','violated'),('70.01 °C','violated')]:b.rule(dict(ambient_temperature=ta),'ambient_temperature',status,'recommended')
    for cm,ta,status in [('4.5 V','25 °C','violated'),('3.5 V','25 °C','satisfied'),('3 V',None,'needs_information')]:b.rule(dict(supply_positive='5 V',supply_negative='0 V',common_mode_voltage=cm,ambient_temperature=ta),'common_mode_electrical',status,'common-mode')
    for q in ['LM358B 的供电','LM358A 的失调电压','从曲线读出精确值','生成完整电路BOM']:b.q('holdout',q,status='unsupported',family='unsupported-holdout')
    b.q('holdout','5能工作吗',status='needs_information',family='missing-unit')
    b.q('holdout','qzxw555000',status='not_found',family='unknown-holdout');b.done()

def ne555():
    b=Cases('ne555')
    for q in ['TRIG','触发阈值','触发电压']:b.q('dev',q,'trigger','trigger-5',dict(minimum=1.1,typical=1.67,maximum=2.2))
    for q in ['THRES','阈值电压']:b.q('dev',q,'threshold','threshold-15',dict(minimum=8.8,typical=10,maximum=11.2))
    for q in ['RESET','复位阈值']:b.q('dev',q,'reset','reset-voltage',dict(minimum=.3,typical=.7,maximum=1))
    for q in ['CONT','控制电压']:b.q('dev',q,'control','control-5',dict(minimum=2.6,typical=3.3,maximum=4))
    for q in ['ICC','供电电流']:b.q('dev',q,'supply-current','icc-5-high',dict(typical=2,maximum=5))
    for q in ['VOL','低电平输出电压']:b.q('dev',q,'output-low','vol-15-200',dict(typical=2.5,maximum=None))
    for q in ['VOH','高电平输出电压']:b.q('dev',q,'output-high','voh-5-100',dict(minimum=2.75,typical=3.3))
    for q in ['DISCH','放电开关']:b.q('dev',q,'discharge','discharge-on',dict(typical=.15,maximum=.4))
    b.q('dev','THRES电流','threshold-current','threshold-current',dict(typical=30,maximum=250,unit='nA'))
    b.q('dev','单稳态','monostable',status='evidence_only')
    b.q('dev','无稳态','astable',status='evidence_only')
    base=dict(vcc='5 V',ambient_temperature='25 °C')
    for changes,matches,status in [({}, {'trigger-5':'applicable','trigger-15':'not_applicable'},'answered'),({'vcc':'15 V'},{'trigger-15':'applicable','trigger-5':'not_applicable'},'answered'),({'vcc':'5000 mV'},{'trigger-5':'applicable'},'answered'),({'ambient_temperature':None},{'trigger-5':'needs_information'},'answered'),({'ambient_temperature':'70 °C'},{'trigger-5':'not_applicable'},'answered'),({'vcc':'5'},{'trigger-5':'invalid'},'invalid')]:b.q('dev','TRIG','trigger',conditions={**base,**changes},matches=matches,status=status)
    for q in ['引脚','接线']:b.q('dev',q,'pins',status='evidence_only')
    for q in ['qzxw987654','做一盘番茄炒蛋']:b.q('dev',q,status='not_found',family='unknown-dev')
    for q in ['推荐工作条件','供电范围']:b.q('holdout',q,'recommended','rec-vcc',dict(minimum=4.5,maximum=16))
    for q in ['绝对最大额定值','极限电压']:b.q('holdout',q,'abs','abs-vcc',dict(maximum=18))
    for q,pid,facts in [('上升时间','rise',dict(typical=100,maximum=300,unit='ns')),('下降时间','fall',dict(typical=100,maximum=300)),('定时温漂','timing-temp-mono',dict(typical=50,maximum=None)),('定时电源敏感度','timing-supply-mono',dict(typical=.1,maximum=.5))]:b.q('holdout',q,'switching',pid,facts)
    b.q('holdout','触发输入电流','trigger-current','trigger-current',dict(typical=.5,maximum=2,unit='μA'))
    b.q('holdout','输出高电平占空比','astable',status='evidence_only',family='duty-definition')
    for text,status in [('4.5 V','satisfied'),('16 V','satisfied'),('4.499 V','violated'),('16.001 V','violated')]:b.rule(dict(vcc=text),'vcc',status,'recommended')
    for text,status in [('0 °C','satisfied'),('70 °C','satisfied'),('-1 °C','violated'),('71 °C','violated')]:b.rule(dict(ambient_temperature=text),'ambient_temperature',status,'recommended')
    p=dict(mode='astable',ra='10 kΩ',rb='10 kΩ',capacitance='10 nF')
    b.rule(p,'frequency','estimated','astable',Fraction(10000,2079))
    b.rule(p,'duty','estimated','astable',Fraction(200,3))
    b.rule(dict(mode='monostable',ra='10 kΩ',capacitance='10 nF'),'pulse_width','estimated','monostable',Fraction(11,100))
    b.rule({**p,'ra':'0 Ω'},'timing','invalid','astable')
    b.rule({**p,'ra_tolerance':'1%'},'timing_tolerance','needs_information','astable')
    b.rule({**p,'ra_tolerance':'100%','rb_tolerance':'1%','capacitance_tolerance':'5%'},'timing_tolerance','invalid','astable')
    for q in ['SE555 的供电范围','TLC555 的参数','从曲线读出精确值','生成完整电路BOM']:b.q('holdout',q,status='unsupported',family='unsupported-holdout')
    b.q('holdout','供电5能工作吗',status='needs_information',family='missing-unit')
    b.q('holdout','qzxw555000',status='not_found',family='unknown-holdout');b.done()

if __name__=='__main__':lm2596();lm358();ne555()
