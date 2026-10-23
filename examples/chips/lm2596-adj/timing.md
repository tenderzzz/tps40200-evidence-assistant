# TI LM2596-ADJ / LM2596-ADJ 条件检查

工作输入电压 VIN：满足该项。12 V；该项范围为 4.5–40 V（含边界）。45 V 是绝对最大值，不能代替工作范围。
反馈分压标称输出：标称估算。R1 为 FB→GND，R2 为 VOUT→FB；VOUT≈1.23×(1+R2/R1)=4.92 V。仅为标称估算，不含基准与电阻误差。
应用建议：下侧电阻 R1：满足该项。1000 Ω；该项范围为 240–1500 Ω（含边界）。这是分压网络的应用建议，不是绝对最大额定值。

状态：answered

## 原始输入

- 输入电压 VIN：12 V
- 下侧电阻 R1（FB → GND）：1 kΩ
- 上侧电阻 R2（VOUT → FB）：3 kΩ


## 逐项检查

- 工作输入电压 VIN / 满足该项：12 V；该项范围为 4.5–40 V（含边界）。45 V 是绝对最大值，不能代替工作范围。 [recommended]
- 反馈分压标称输出 / 标称估算：R1 为 FB→GND，R2 为 VOUT→FB；VOUT≈1.23×(1+R2/R1)=4.92 V。仅为标称估算，不含基准与电阻误差。 [divider]
- 应用建议：下侧电阻 R1 / 满足该项：1000 Ω；该项范围为 240–1500 Ω（含边界）。这是分压网络的应用建议，不是绝对最大额定值。 [divider]

## 说明

- 每项仅核对该项限制，不代表完整电路设计通过。
- 标称输出公式不能保证压差、热、负载、补偿、磁性元件或布局满足要求。
- 工作温度原表未明确 TA/TJ；本页不把它转换成环境温度或结温规则。

## 原文证据

### [recommended] 推荐工作条件

PDF 物理页 5 / 印刷页 5；区域 (54.0, 459.0, 558.0, 519.0)（PDF pt，左上原点）

7.3 Operating Conditions
MIN MAX UNIT
Supply voltage 4.5 40 V
Temperature –40 125 °C

### [divider] 反馈分压

PDF 物理页 28 / 印刷页 28；区域 (54.0, 222.0, 558.0, 405.0)（PDF pt，左上原点）

9.2.2.2.1 Programming Output Voltage
Select R and R , as shown in Table 9-6
1 2
Use Equation 5 to select the appropriate resistor values.
(5)
R2
Select a V O v U a T lu = e V f R o E r F R 1 + b R e1tw w ee h n er e 2 V 4 R 0 E F Ω = a 1 n .2 d 3 1 V .5 kΩ. The lower resistor values minimize noise pickup in the
1
sensitive feedback pin. (For the lowest temperature coefficient and the best stability with time, use 1% metal film
resistors.). Calculate R with Equation 6.
2
(6)
VOUT
Select R R2 to = b R e 1 1 V kRΩEF, 1 − % 1 . Solve for R in Equation 7.
1 2

来源：https://www.ti.com/lit/ds/symlink/lm2596.pdf
版本：SNVS124G (Rev. G)
SHA-256：2eec90879908cf711b84d4f0c5d534c3cd12c576d25254b7019247435af4ab0f
