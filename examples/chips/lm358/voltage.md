# TI LM358 / LM358 条件检查

推荐总供电压差：不满足该项。VS=V+−V−=32 V；推荐范围为3–30 V。不能使用 LM358B 的36 V范围。
推荐环境温度 TA：满足该项。25 °C；该项范围为 0–70 °C（含边界）。TA 不是结温 TJ。

状态：answered

## 原始输入

- 正电源 V+（相对同一参考点）：16 V
- 负电源 V−（相对同一参考点）：-16 V
- 环境温度 TA：25 °C


## 逐项检查

- 推荐总供电压差 / 不满足该项：VS=V+−V−=32 V；推荐范围为3–30 V。不能使用 LM358B 的36 V范围。 [recommended]
- 推荐环境温度 TA / 满足该项：25 °C；该项范围为 0–70 °C（含边界）。TA 不是结温 TJ。 [recommended]
- 推荐工作条件：共模范围 / 信息不足：请提供输入共模电压 VCM；不使用隐含默认值。 [recommended]
- 条件化电气特性：共模范围 / 信息不足：请提供输入共模电压 VCM；不使用隐含默认值。 [common-mode]

## 说明

- 每项仅核对该项限制，不代表完整电路设计通过。
- 推荐条件与电气特性测试范围分开报告；TA 未提供时不默认25°C。
- 输入共模满足不等于输出摆幅、带宽、稳定性或负载能力满足。

## 原文证据

### [recommended] 推荐工作条件

PDF 物理页 5 / 印刷页 5；区域 (54.0, 76.0, 558.0, 273.0)（PDF pt，左上原点）

5.3 Recommended Operating Conditions
over operating ambient temperature range (unless otherwise noted)
MIN MAX UNIT
LM358B, LM358BA, LM2904B,
3 36
LM2904BA
V Supply voltage, V = ([V+] – [V–]) LM158, LM258, LM358, LM158A, V
S S 3 30
LM258A, LM358A, LM2904V
LM2904 3 26
V Common-mode voltage V– V+ – 2 V
CM
LM358B, LM358BA –40 85
LM2904B, LM2904BA, LM2904,
–40 125
LM2904V
T Operating ambient temperature °C
A LM358, LM358A 0 70
LM258, LM258A –20 85
LM158, LM158A –55 125

表头／脚注上下文：
over operating ambient temperature range (unless otherwise noted)
MIN MAX UNIT

来源：https://www.ti.com/lit/ds/symlink/lm358.pdf
版本：SLOS068AB (Rev. AB)
SHA-256：8277dff7b89138c63b3582d37f378065a1dea3cae5ed1e2926ddc2779eb7e3a2
