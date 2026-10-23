"""Input capabilities and educational examples shared by HTTP UI and CLI."""
def field(name,label,dimension=None,hint="",choices=None,kind="text"):
    return dict(name=name,label=label,dimension=dimension,hint=hint,choices=choices,kind="select" if choices else kind)

VIN=field("vin","输入电压 VIN","voltage","12 V")
TA=field("ambient_temperature","环境温度 TA","temperature","25 °C")
VS=field("supply_voltage","总供电压差 VS","voltage","5 V")
VCC=field("vcc","供电电压 VCC","voltage","5 V")
SPECS={
 "lm2596-adj":dict(
  check_fields=[VIN,field("r_lower","下侧电阻 R1（FB → GND）","resistance","1 kΩ"),field("r_upper","上侧电阻 R2（VOUT → FB）","resistance","3 kΩ")],
  condition_fields=[VIN,field("tj","结温 TJ","temperature","25 °C"),field("load_current","负载电流 ILOAD","current","0.5 A"),field("output_voltage","稳压输出 VOUT（不是开关节点）","voltage","3 V"),field("feedback_voltage","反馈引脚测试电压","voltage","1.3 V"),field("on_off","ON/OFF 测试电压","voltage","2.5 V")],
  filter_example=dict(vin="12 V",tj="25 °C",load_current="0.5 A",output_voltage="3 V"),
  check_caption="R1 是下侧电阻，R2 是上侧电阻。分压公式是标称估算，不能保证完整降压电路可用。",
  cases=[dict(id="voltage",title="工作范围检查",subtitle="41 V 与 45 V 绝对最大值的区别",request=dict(kind="query",question="输入电压 41 V 能正常工作吗？")),
         dict(id="reference",title="反馈基准条件",subtitle="室温与全结温范围分行读取",request=dict(kind="query",question="VFB",conditions=dict(vin="12 V",tj="25 °C",load_current="0.5 A",output_voltage="3 V"))),
         dict(id="timing",title="反馈分压计算",subtitle="下侧 1 kΩ，上侧 3 kΩ",request=dict(kind="check",point=dict(vin="12 V",r_lower="1 kΩ",r_upper="3 kΩ")))],
  pins=[(1,"VIN","输入供电，需要本地输入旁路。","推荐输入电压"),(2,"Output","开关节点，经外部电感和电容滤波后才形成稳压输出。","引脚功能"),(3,"GND","器件地。","引脚功能"),(4,"Feedback","反馈输入，连接上下侧分压电阻中点。","反馈分压"),(5,"ON/OFF","低电平启用，高电平关闭。","ON/OFF")]),
 "lm358":dict(
  check_fields=[field("supply_positive","正电源 V+（相对同一参考点）","voltage","5 V"),field("supply_negative","负电源 V−（相对同一参考点）","voltage","0 V"),TA,field("common_mode_voltage","输入共模电压 VCM","voltage","4.5 V")],
  condition_fields=[VS,TA,field("common_mode_voltage","输入共模测试电压 VCM","voltage","0 V"),field("output_voltage","输出测试电压 VO","voltage","1.4 V"),field("load_resistance","负载电阻 RL","resistance","10 kΩ"),field("signal_frequency","信号频率 f","frequency","1 kHz"),field("open_loop","开环测试设置已确认？",kind="boolean")],
  filter_example=dict(supply_voltage="5 V",ambient_temperature="25 °C",common_mode_voltage="0 V",output_voltage="1.4 V",open_loop=True),
  check_caption="正负电源和共模输入使用同一个参考点。TA 是环境温度；不根据输入共模范围推断输出摆幅。",
  cases=[dict(id="voltage",title="供电压差检查",subtitle="3–30 V 是总压差，不是每条电源轨",request=dict(kind="check",point=dict(supply_positive="16 V",supply_negative="-16 V",ambient_temperature="25 °C"))),
         dict(id="reference",title="失调电压条件",subtitle="7 mV 与全温 9 mV 的区别",request=dict(kind="query",question="VOS",conditions=dict(supply_voltage="5 V",ambient_temperature="25 °C",common_mode_voltage="0 V",output_voltage="1.4 V",open_loop=True))),
         dict(id="timing",title="共模范围检查",subtitle="5 V 供电时，4.5 V 输入是否满足",request=dict(kind="check",point=dict(supply_positive="5 V",supply_negative="0 V",ambient_temperature="25 °C",common_mode_voltage="4.5 V")))],
  pins=[(1,"OUT1","通道1输出。","输出摆幅"),(2,"IN1−","通道1反相输入。","输入共模范围"),(3,"IN1+","通道1同相输入。","VOS"),(4,"V−","负电源；单电源时可接0 V参考点。","供电范围"),(8,"V+","正电源。","供电范围"),(7,"OUT2","通道2输出。","输出摆幅"),(6,"IN2−","通道2反相输入。","输入共模范围"),(5,"IN2+","通道2同相输入。","输入偏置电流")]),
 "ne555":dict(
  check_fields=[VCC,TA,field("mode","定时模式",choices=[dict(value="monostable",label="单稳态 · 单次脉冲"),dict(value="astable",label="无稳态 · 连续振荡")]),field("ra","定时电阻 RA","resistance","10 kΩ"),field("rb","定时电阻 RB（无稳态）","resistance","10 kΩ"),field("capacitance","定时电容 C","capacitance","10 nF"),field("ra_tolerance","RA 容差（可选）","tolerance","1%"),field("rb_tolerance","RB 容差（无稳态，可选）","tolerance","1%"),field("capacitance_tolerance","C 容差（可选）","tolerance","5%")],
  condition_fields=[VCC,TA,field("load_current","输出负载电流（源电流填负数）","current","-100 mA"),field("trigger_voltage","TRIG 测试电压","voltage","0 V"),field("reset_voltage","RESET 测试电压","voltage","0 V"),field("output_state","输出状态",choices=[dict(value="low",label="低电平"),dict(value="high",label="高电平")]),field("control_open","CONT 是否开路？",kind="boolean"),field("discharge_off","DISCH 是否关断？",kind="boolean")],
  filter_example=dict(vcc="5 V",ambient_temperature="25 °C"),
  check_caption="计算对应手册标准接线。占空比指输出高电平所占比例；容差只计算元件端点，空白不会按0%处理。",
  cases=[dict(id="voltage",title="推荐供电检查",subtitle="17 V 未超过应力值，仍超出推荐范围",request=dict(kind="query",question="供电 17 V 能正常工作吗？")),
         dict(id="reference",title="触发阈值条件",subtitle="5 V 与 15 V 供电的两行参数",request=dict(kind="query",question="TRIG",conditions=dict(vcc="5 V",ambient_temperature="25 °C"))),
         dict(id="timing",title="频率与占空比",subtitle="RA / RB 各 10 kΩ，C 为 10 nF",request=dict(kind="check",point=dict(vcc="5 V",ambient_temperature="25 °C",mode="astable",ra="10 kΩ",rb="10 kΩ",capacitance="10 nF",ra_tolerance="1%",rb_tolerance="1%",capacitance_tolerance="5%")))],
  pins=[(1,"GND","器件地。","引脚功能"),(2,"TRIG","下降到触发阈值以下可置位。","TRIG"),(3,"OUT","输出，高低电平随负载变化。","输出摆幅"),(4,"RESET","低有效复位，覆盖其他控制输入。","RESET"),(8,"VCC","供电输入。","供电范围"),(7,"DISCH","内部放电开关。","DISCH"),(6,"THRES","定时电容阈值输入。","THRES"),(5,"CONT","控制阈值电平；接法见原文。","CONT")]),
}

def capabilities(chip_id):
    from .chips import profile
    profile(chip_id)
    if chip_id=="tps40200":return {}
    return SPECS[chip_id]

def input_fields(chip_id,kind):
    return capabilities(chip_id)["condition_fields" if kind=="conditions" else "check_fields"]
