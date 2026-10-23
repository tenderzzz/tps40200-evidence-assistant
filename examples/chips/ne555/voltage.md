# TI NE555 / 供电 17 V 能正常工作吗？

推荐供电电压 VCC：不满足该项。17 V；该项范围为 4.5–16 V（含边界）。18 V 是绝对最大额定值。

状态：answered

## 原始输入

- 供电电压 VCC：17 V


## 逐项检查

- 推荐供电电压 VCC / 不满足该项：17 V；该项范围为 4.5–16 V（含边界）。18 V 是绝对最大额定值。 [recommended]
- 推荐环境温度 TA / 信息不足：请提供环境温度 TA；不使用隐含默认值。 [recommended]
- 定时公式输入 / 信息不足：请提供定时模式、定时电阻 RA、定时电容 C；不使用隐含默认值。 [astable]

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

来源：https://www.ti.com/lit/ds/symlink/ne555.pdf
版本：SLFS022K (Rev. K)
SHA-256：a3756e59fd06d0ba736edf9ffe71d99d2aae33fb7e49fedc86165a241179f4a6
