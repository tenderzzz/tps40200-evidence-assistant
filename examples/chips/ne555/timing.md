# TI NE555 / NE555 条件检查

推荐供电电压 VCC：满足该项。5 V；该项范围为 4.5–16 V（含边界）。18 V 是绝对最大额定值。
推荐环境温度 TA：满足该项。25 °C；该项范围为 0–70 °C（含边界）。
输出高电平时间：标称估算。0.1386 ms。根据标准接线的标称公式估算；芯片误差未计入。
输出低电平时间：标称估算。0.0693 ms。根据标准接线的标称公式估算；芯片误差未计入。
标称周期：标称估算。0.2079 ms。根据标准接线的标称公式估算；芯片误差未计入。
标称振荡频率：标称估算。4.81 kHz。根据标准接线的标称公式估算；芯片误差未计入。
输出高电平占空比：标称估算。66.6667 %。占空比指输出高电平比例，不是手册中的驱动器占空比。
应用建议：频率不超过100 kHz：满足该项。估算频率符合手册为减小失真而给出的≤100 kHz建议。这不是保证精度或绝对最大频率。
输出高电平时间 · 元件容差：标称估算。元件端点估算约 0.130353–0.146985 ms；不含器件自身误差、温漂和供电变化。
输出低电平时间 · 元件容差：标称估算。元件端点估算约 0.0651767–0.0734927 ms；不含器件自身误差、温漂和供电变化。
标称周期 · 元件容差：标称估算。元件端点估算约 0.19553–0.220478 ms；不含器件自身误差、温漂和供电变化。
标称振荡频率 · 元件容差：标称估算。元件端点估算约 4.5356–5.11431 kHz；不含器件自身误差、温漂和供电变化。
输出高电平占空比 · 元件容差：标称估算。元件端点估算约 66.4452–66.8896 %；不含器件自身误差、温漂和供电变化。

状态：answered

## 原始输入

- 供电电压 VCC：5 V
- 环境温度 TA：25 °C
- 定时模式：astable
- 定时电阻 RA：10 kΩ
- 定时电阻 RB（无稳态）：10 kΩ
- 定时电容 C：10 nF
- RA 容差（可选）：1%
- RB 容差（无稳态，可选）：1%
- C 容差（可选）：5%


## 逐项检查

- 推荐供电电压 VCC / 满足该项：5 V；该项范围为 4.5–16 V（含边界）。18 V 是绝对最大额定值。 [recommended]
- 推荐环境温度 TA / 满足该项：25 °C；该项范围为 0–70 °C（含边界）。 [recommended]
- 输出高电平时间 / 标称估算：0.1386 ms。根据标准接线的标称公式估算；芯片误差未计入。 [astable]
- 输出低电平时间 / 标称估算：0.0693 ms。根据标准接线的标称公式估算；芯片误差未计入。 [astable]
- 标称周期 / 标称估算：0.2079 ms。根据标准接线的标称公式估算；芯片误差未计入。 [astable]
- 标称振荡频率 / 标称估算：4.81 kHz。根据标准接线的标称公式估算；芯片误差未计入。 [astable]
- 输出高电平占空比 / 标称估算：66.6667 %。占空比指输出高电平比例，不是手册中的驱动器占空比。 [astable]
- 应用建议：频率不超过100 kHz / 满足该项：估算频率符合手册为减小失真而给出的≤100 kHz建议。这不是保证精度或绝对最大频率。 [astable]
- 输出高电平时间 · 元件容差 / 标称估算：元件端点估算约 0.130353–0.146985 ms；不含器件自身误差、温漂和供电变化。 [astable]
- 输出低电平时间 · 元件容差 / 标称估算：元件端点估算约 0.0651767–0.0734927 ms；不含器件自身误差、温漂和供电变化。 [astable]
- 标称周期 · 元件容差 / 标称估算：元件端点估算约 0.19553–0.220478 ms；不含器件自身误差、温漂和供电变化。 [astable]
- 标称振荡频率 · 元件容差 / 标称估算：元件端点估算约 4.5356–5.11431 kHz；不含器件自身误差、温漂和供电变化。 [astable]
- 输出高电平占空比 · 元件容差 / 标称估算：元件端点估算约 66.4452–66.8896 %；不含器件自身误差、温漂和供电变化。 [astable]

## 说明

- 每项仅核对该项限制，不代表完整电路设计通过。
- 供电与温度检查独立于标称定时估算；公式可算不代表器件在超范围供电下可用。
- 容差须显式提供，空白不当0%；单稳态不使用RB或RB容差。
- 频率按1/(tH+tL)计算，避免1.44与0.693两个近似系数导致内部不一致。

## 原文证据

### [recommended] 推荐工作条件

PDF 物理页 4 / 印刷页 4；区域 (54.0, 399.0, 558.0, 542.0)（PDF pt，左上原点）

5.3 Recommended Operating Conditions
over operating free-air temperature range (unless otherwise noted)
MIN MAX UNIT
NA555, NE555, SA555 4.5 16
V Supply voltage V
CC
SE555 4.5 18
I Output current ±200 mA
O
NA555 –40 105
NE555 0 70
T Operating free-air temperature °C
A
SA555 –40 85
SE555 –55 125

### [astable] 无稳态

PDF 物理页 12 / 印刷页 12；区域 (54.0, 76.0, 558.0, 720.0)（PDF pt，左上原点）

6.3.2 Astable Operation
Figure 6-5 shows that adding a second resistor, R , to the circuit of Figure 6-2 and connecting the trigger input
B
to the threshold input causes the timer to self-trigger and run as a multivibrator. Capacitor C charges through R
A
and R and then discharges through R only. Therefore, the duty cycle is controlled by the values of R and R .
B B A B
VCC
(5 V to 15 V)
0.01 µF
(see Note A) RA
CONT VCC
RL
RESET
DISCH
OUT Output
RB
THRES
TRIG
GND
C
Î
Î
Î
Open
5 8
4
7
3
6
2
1
Pin numbers shown are for the D, JG, P, PS, and PW packages.
NOTE A: Decoupling CONT voltage to ground with a capacitor can
improve operation. This should be evaluated for individual
applications.
Figure 6-5. Circuit for Astable Operation
vid/V
1 − egatloV
tH
tL Output Voltage
Capacitor Voltage
Time − 0.5 ms/div
Î
Î
Î
Î
Î
Î
Î
Î
Î
Î
Î
Î
Î
Î
Î
Î
Î
Î
Î
Î
Î
Î
Î
Î
Î
Î
Î
Î
Î
Î
Î
Î
Î
Î
Î
Î
Î
Î
Î
Î
RA = 5 k(cid:1) RL = 1 k(cid:1)
RB = 3 k(cid:1) See Figure 12
C = 0.15 µF
Figure 6-6. Typical Astable Waveforms
This astable connection results in capacitor C charging and discharging between the threshold-voltage level
(≅ 0.67 × V ) and the trigger-voltage level (≅ 0.33 × V ). As in the mono-stable circuit, charge and discharge
CC CC
times (and, therefore, the frequency and duty cycle) are independent of the supply voltage. To reduce distortion,
use at maximum frequency of 100kHz or below. If higher-frequency operation is required, consider using the
TLC555 CMOS Timer instead.
Figure 6-6 shows typical waveforms generated during astable operation. The output high-level duration t and
H
low-level duration t are calculated as follows:
L
(1)
tH ≅ 0.693 × RA + RB × C (2)
Other u t sLe ≅ fu 0 l .6 re 9 l 3 a × tio R nBs × hi C ps for period, frequency, and driver-referred and waveform-referred duty cycle are
calculated as follows:
(3)
T = tH + tL ≅ 0.693 × RA + 2RB × C
(4)
1 1.44
f = T ≅ RA + 2RB × C
(5)
tL RB
Output driver duty cycle = T ≅ RA + 2RB
(6)
tH RB RA + RB
Output waveform duty cycle = T ≅ 1 − RA + 2RB = RA + 2RB

来源：https://www.ti.com/lit/ds/symlink/ne555.pdf
版本：SLFS022K (Rev. K)
SHA-256：a3756e59fd06d0ba736edf9ffe71d99d2aae33fb7e49fedc86165a241179f4a6
