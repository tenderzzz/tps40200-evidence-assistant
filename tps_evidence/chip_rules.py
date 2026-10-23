"""Limited source-bound checks; no complete-circuit approval."""
from decimal import Decimal as D
from itertools import product
from .chip_inputs import parse_inputs,labels
from .chips import profile
from .corpus import load_corpus
from .models import Result,RuleResult,Hit,RULE_LABELS

class Rules:
    def __init__(self,chip_id,point):
        self.chip=chip_id;self.raw,self.p,self.errors=parse_inputs(point,chip_id)
        self.labels=labels(chip_id);self.rows=[]
        self.source,self.evidence,self.params=load_corpus(chip_id)
    def add(self,id,title,status,message,eid,value=None,unit=None,low=None,high=None,fields=None):
        self.rows.append(RuleResult(rule=id,title=title,status=status,message=message,evidence_ids=[eid],
            value=float(value) if value is not None else None,unit=unit,
            minimum=float(low) if low is not None else None,maximum=float(high) if high is not None else None,fields=fields or []))
    def ready(self,id,title,fields,eid):
        invalid=[f for f in fields if f in self.errors];missing=[f for f in fields if self.p.get(f) is None]
        if invalid:
            self.add(id,title,'invalid','；'.join(self.labels[f]+'：'+self.errors[f] for f in invalid),eid,fields=invalid);return False
        if missing:
            self.add(id,title,'needs_information','请提供'+'、'.join(self.labels[f] for f in missing)+'；不使用隐含默认值。',eid,fields=missing);return False
        return True
    def range(self,id,title,key,lo,hi,eid,unit,extra=''):
        if not self.ready(id,title,[key],eid):return
        value=self.p[key];okay=D(str(lo))<=value<=D(str(hi))
        self.add(id,title,'satisfied' if okay else 'violated',f'{value:g} {unit}；该项范围为 {lo}–{hi} {unit}（含边界）。'+extra,eid,value,unit)
    def finish(self,notices):
        active=[r for r in self.rows if r.status!='needs_information'];ids=list(dict.fromkeys(e for r in active or self.rows for e in r.evidence_ids))
        return Result(chip_id=self.chip,question=profile(self.chip)['name']+' 条件检查',
            status='invalid' if any(r.status=='invalid' for r in self.rows) else 'answered' if active else 'needs_information',
            answer='\n'.join(f'{r.title}：{RULE_LABELS[r.status]}。{r.message}' for r in active or self.rows),
            inputs=self.raw,checks=self.rows,evidence_ids=ids,hits=[Hit(evidence_id=e,score=1) for e in ids],
            source_sha256=self.source['sha256'],source_revision=self.source['revision'],
            notices=['每项仅核对该项限制，不代表完整电路设计通过。']+notices)

def check_lm2596(point):
    r=Rules('lm2596-adj',point)
    r.range('vin','工作输入电压 VIN','vin',4.5,40,'recommended','V','45 V 是绝对最大值，不能代替工作范围。')
    if r.ready('divider_voltage','反馈分压标称输出',['r_lower','r_upper'],'divider'):
        v=D('1.23')*(1+r.p['r_upper']/r.p['r_lower'])
        r.add('divider_voltage','反馈分压标称输出','estimated',f'R1 为 FB→GND，R2 为 VOUT→FB；VOUT≈1.23×(1+R2/R1)={float(v):.6g} V。仅为标称估算，不含基准与电阻误差。','divider',v,'V')
    r.range('divider_r1','应用建议：下侧电阻 R1','r_lower',240,1500,'divider','Ω','这是分压网络的应用建议，不是绝对最大额定值。')
    return r.finish(['标称输出公式不能保证压差、热、负载、补偿、磁性元件或布局满足要求。','工作温度原表未明确 TA/TJ；本页不把它转换成环境温度或结温规则。'])

def check_lm358(point):
    r=Rules('lm358',point);p=r.p;rails=['supply_positive','supply_negative']
    if r.ready('supply_voltage','推荐总供电压差',rails,'recommended'):
        vs=p['supply_positive']-p['supply_negative'];p['supply_voltage']=vs
        if vs<=0:r.add('supply_voltage','推荐总供电压差','invalid','V+ 必须高于 V−；两条电源轨须使用同一参考点。','recommended',fields=rails)
        else:r.add('supply_voltage','推荐总供电压差','satisfied' if 3<=vs<=30 else 'violated',f'VS=V+−V−={vs:g} V；推荐范围为3–30 V。不能使用 LM358B 的36 V范围。','recommended',vs,'V')
    r.range('ambient_temperature','推荐环境温度 TA','ambient_temperature',0,70,'recommended','°C','TA 不是结温 TJ。')
    required=rails+['ambient_temperature','common_mode_voltage']
    for electrical in [False,True]:
        id='common_mode_electrical' if electrical else 'common_mode_recommended'
        title='条件化电气特性：共模范围' if electrical else '推荐工作条件：共模范围';eid='common-mode' if electrical else 'recommended'
        if not r.ready(id,title,required,eid):continue
        vs=p['supply_positive']-p['supply_negative'];ta=p['ambient_temperature']
        if not 0<=ta<=70 or not (D(5) if electrical else D(3))<=vs<=30:
            r.add(id,title,'needs_information','已提供供电或环境温度超出此项依据的适用范围；不能用这条共模规格外推。',eid);continue
        margin=D('1.5') if electrical and ta==25 else D(2);lo,hi=p['supply_negative'],p['supply_positive']-margin
        value=p['common_mode_voltage'];okay=lo<=value<=hi
        r.add(id,title,'satisfied' if okay else 'violated',f'TA={ta:g}°C，VS={vs:g} V：VCM={value:g} V；该条件下范围为 {lo:g}–{hi:g} V。'+('室温行与全温行分别判断。' if electrical else '按推荐工作条件的 V− 至 V+−2 V 判断。'),eid,value,'V',lo,hi)
    return r.finish(['推荐条件与电气特性测试范围分开报告；TA 未提供时不默认25°C。','输入共模满足不等于输出摆幅、带宽、稳定性或负载能力满足。'])

def _timing(mode,ra,rb,c):
    if mode=='monostable':return {'pulse_width':D('1.1')*ra*c*1000}
    th=D('.693')*(ra+rb)*c;tl=D('.693')*rb*c;period=th+tl
    return dict(high_time=th*1000,low_time=tl*1000,period=period*1000,frequency=1/period/1000,duty=th/period*100)

TIMING_TITLES=dict(pulse_width='单稳态标称脉宽',high_time='输出高电平时间',low_time='输出低电平时间',period='标称周期',frequency='标称振荡频率',duty='输出高电平占空比')
def check_ne555(point):
    r=Rules('ne555',point);p=r.p
    r.range('vcc','推荐供电电压 VCC','vcc',4.5,16,'recommended','V','18 V 是绝对最大额定值。')
    r.range('ambient_temperature','推荐环境温度 TA','ambient_temperature',0,70,'recommended','°C')
    mode=p.get('mode');eid='monostable' if mode=='monostable' else 'astable'
    required=['mode','ra','capacitance']+(['rb'] if mode=='astable' else [])
    if r.ready('timing','定时公式输入',required,eid):
        values=_timing(mode,p['ra'],p.get('rb'),p['capacitance'])
        for key,value in values.items():
            unit='kHz' if key=='frequency' else '%' if key=='duty' else 'ms'
            definition='占空比指输出高电平比例，不是手册中的驱动器占空比。' if key=='duty' else '根据标准接线的标称公式估算；芯片误差未计入。'
            r.add(key,TIMING_TITLES[key],'estimated',f'{float(value):.6g} {unit}。'+definition,eid,value,unit)
        if mode=='astable':
            okay=values['frequency']<=100
            r.add('frequency_guidance','应用建议：频率不超过100 kHz','satisfied' if okay else 'violated',('估算频率符合' if okay else '估算频率超出')+'手册为减小失真而给出的≤100 kHz建议。这不是保证精度或绝对最大频率。',eid,values['frequency'],'kHz')
        else:r.add('pulse_guidance','应用时序：脉宽与触发','estimated','手册讨论了10 μs最小脉宽与TRIG在结束前至少10 μs回高的条件；输入波形未提供，本工具不核验这些时序。',eid)
    tolerance_keys=['ra_tolerance','capacitance_tolerance']+(['rb_tolerance'] if mode=='astable' else [])
    if any(r.raw.get(k) for k in ('ra_tolerance','rb_tolerance','capacitance_tolerance')):
        if r.ready('timing_tolerance','元件容差区间',required+tolerance_keys,eid):
            keys=['ra','capacitance']+(['rb'] if mode=='astable' else []);ranges=[]
            for k in keys:
                tol=p[{'ra':'ra_tolerance','rb':'rb_tolerance','capacitance':'capacitance_tolerance'}[k]];ranges.append((p[k]*(1-tol),p[k]*(1+tol)))
            corners=[]
            for corner in product(*ranges):
                inputs=dict(zip(keys,corner));corners.append(_timing(mode,inputs['ra'],inputs.get('rb'),inputs['capacitance']))
            for key in corners[0]:
                lo=min(c[key] for c in corners);hi=max(c[key] for c in corners);unit='kHz' if key=='frequency' else '%' if key=='duty' else 'ms'
                r.add('tolerance_'+key,TIMING_TITLES[key]+' · 元件容差','estimated',f'元件端点估算约 {float(lo):.6g}–{float(hi):.6g} {unit}；不含器件自身误差、温漂和供电变化。',eid,unit=unit,low=lo,high=hi)
    return r.finish(['供电与温度检查独立于标称定时估算；公式可算不代表器件在超范围供电下可用。','容差须显式提供，空白不当0%；单稳态不使用RB或RB容差。','频率按1/(tH+tL)计算，避免1.44与0.693两个近似系数导致内部不一致。'])

def check(point,chip_id):
    return {'lm2596-adj':check_lm2596,'lm358':check_lm358,'ne555':check_ne555}[chip_id](point)
