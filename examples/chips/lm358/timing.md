# TI LM358 / LM358 条件检查

推荐总供电压差：满足该项。VS=V+−V−=5 V；推荐范围为3–30 V。不能使用 LM358B 的36 V范围。
推荐环境温度 TA：满足该项。25 °C；该项范围为 0–70 °C（含边界）。TA 不是结温 TJ。
推荐工作条件：共模范围：不满足该项。TA=25°C，VS=5 V：VCM=4.5 V；该条件下范围为 0–3 V。按推荐工作条件的 V− 至 V+−2 V 判断。
条件化电气特性：共模范围：不满足该项。TA=25°C，VS=5 V：VCM=4.5 V；该条件下范围为 0–3.5 V。室温行与全温行分别判断。

状态：answered

## 原始输入

- 正电源 V+（相对同一参考点）：5 V
- 负电源 V−（相对同一参考点）：0 V
- 环境温度 TA：25 °C
- 输入共模电压 VCM：4.5 V


## 逐项检查

- 推荐总供电压差 / 满足该项：VS=V+−V−=5 V；推荐范围为3–30 V。不能使用 LM358B 的36 V范围。 [recommended]
- 推荐环境温度 TA / 满足该项：25 °C；该项范围为 0–70 °C（含边界）。TA 不是结温 TJ。 [recommended]
- 推荐工作条件：共模范围 / 不满足该项：TA=25°C，VS=5 V：VCM=4.5 V；该条件下范围为 0–3 V。按推荐工作条件的 V− 至 V+−2 V 判断。 [recommended]
- 条件化电气特性：共模范围 / 不满足该项：TA=25°C，VS=5 V：VCM=4.5 V；该条件下范围为 0–3.5 V。室温行与全温行分别判断。 [common-mode]

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

### [common-mode] 输入共模范围

PDF 物理页 10 / 印刷页 10；区域 (54.0, 234.0, 558.0, 301.0)（PDF pt，左上原点）

INPUT VOLTAGE RANGE
VS = 5 V to 30 V LM358
(V–) (V+) – 1.5
VS = 30 V LM358A
VCM Common-mode voltage range V
VS = 5 V to 30 V LM358
TA = 0°C to 70°C (V–) (V+) – 2
VS = 30 V LM358A
CMRR Common-mode rejection ratio VS = 5 V to 30 V; VCM = 0 V 65 80 dB

表头／脚注上下文：
5.7 Electrical Characteristics: LM358, LM358A
For V = (V+) – (V–) = 5 V, T = 25°C (unless otherwise noted)
S A
PARAMETER TEST CONDITIONS(1) MIN TYP(2) MAX UNIT
(1) All characteristics are measured under open-loop conditions, with zero common-mode input voltage, unless otherwise specified.
Maximum V for testing purposes is 30 V for LM358 and LM358A.
S
(2) All typical values are T = 25°C.
A

来源：https://www.ti.com/lit/ds/symlink/lm358.pdf
版本：SLOS068AB (Rev. AB)
SHA-256：8277dff7b89138c63b3582d37f378065a1dea3cae5ed1e2926ddc2779eb7e3a2
