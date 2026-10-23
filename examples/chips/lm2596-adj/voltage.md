# TI LM2596-ADJ / 输入电压 41 V 能正常工作吗？

工作输入电压 VIN：不满足该项。41 V；该项范围为 4.5–40 V（含边界）。45 V 是绝对最大值，不能代替工作范围。

状态：answered

## 原始输入

- 输入电压 VIN：41 V


## 逐项检查

- 工作输入电压 VIN / 不满足该项：41 V；该项范围为 4.5–40 V（含边界）。45 V 是绝对最大值，不能代替工作范围。 [recommended]
- 反馈分压标称输出 / 信息不足：请提供下侧电阻 R1（FB → GND）、上侧电阻 R2（VOUT → FB）；不使用隐含默认值。 [divider]
- 应用建议：下侧电阻 R1 / 信息不足：请提供下侧电阻 R1（FB → GND）；不使用隐含默认值。 [divider]

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

来源：https://www.ti.com/lit/ds/symlink/lm2596.pdf
版本：SNVS124G (Rev. G)
SHA-256：2eec90879908cf711b84d4f0c5d534c3cd12c576d25254b7019247435af4ab0f
