# TI LM2596-ADJ / VFB

可调版本 VFB 的典型值为 1.23 V；室温和完整结温范围的保证上下限分别列出，且有输入、负载和输出设置条件。

状态：answered

| 参数 | 类别 | MIN | TYP | MAX | 单位 | 条件 | 证据 |
|---|---|---:|---:|---:|---|---|---|
| VFB 反馈基准 | 电气特性 | 1.193 | 1.23 | 1.267 | V | TJ = 25°C；4.5≤VIN≤40 V；0.2≤ILOAD≤3 A；VOUT programmed for 3 V | vfb, vfb-note |
| VFB 反馈基准 | 电气特性 | 1.18 | — | 1.28 | V | −40≤TJ≤125°C；4.5≤VIN≤40 V；0.2≤ILOAD≤3 A；VOUT programmed for 3 V | vfb, vfb-note |
| η 效率 | 电气特性 | — | 73 | — | % | VIN=12 V；VOUT=3 V；ILOAD=3 A；TJ=25°C；Figure 9-13 外部元件 | vfb, vfb-note |

参数注释：

- vfb-25：
- vfb-full：TYP 只在 TJ=25°C 给出；全温行留空表示未单独给出全温典型值，不否认同组的室温典型值。
- efficiency：典型效率不保证其他电路、负载或布局下的效率。

## 参数行条件匹配

输入（原样保留）：

- vin：12 V
- tj：25 °C
- load_current：0.5 A
- output_voltage：3 V

| 参数行 | 匹配结果 | 原因 |
|---|---|---|
| vfb-25 | 已提供条件符合 | 已提供条件符合此行已整理的表头与行条件；典型值仍只按原表注明的温度有效。 |
| vfb-full | 已提供条件符合 | 已提供条件符合此行已整理的表头与行条件；典型值仍只按原表注明的温度有效。 |
| efficiency | 额定限制／未筛选 | 此行含未建模的测试设置，请核对原文与脚注；不自动判断全部测试条件。 |

## 说明

- 典型值不等于保证上下限；空白表示手册未给出该列数值。各条件行分别有效，不自动合并或插值。
- 本页只使用当前TI型号适用行；原文片段可能同时列出其他型号，其数值不会自动转用于当前型号。
- 没有提供的测试设置不会默认满足。TA、TJ 与芯片型号分别匹配；多个适用行不自动合并。

## 原文证据

### [vfb] 反馈基准

PDF 物理页 6 / 印刷页 6；区域 (54.0, 589.0, 558.0, 695.0)（PDF pt，左上原点）

7.8 Electrical Characteristics – Adjustable Voltage Version
Specifications are for T = 25°C (unless otherwise noted)
J
PARAMETER TEST CONDITIONS MIN(1) TYP(2) MAX(1) UNIT
SYSTEM PARAMETERS (3) (see Figure 9-13 for test circuit)
4.5 V ≤ VIN ≤ 40 V, 0.2 A ≤ ILOAD ≤ 3 A 1.23
VFB Feedback voltage VOUT programmed for 3 V TJ = 25°C 1.193 1.267 V
(see Figure 9-13 for test circuit) –40°C ≤ TJ ≤ 125°C 1.18 1.28
η Efficiency VIN = 12 V, VOUT = 3 V, ILOAD = 3 A 73%

表头／脚注上下文：
(1) All room temperature limits are 100% production tested. All limits at temperature extremes are specified via correlation using standard
Statistical Quality Control (SQC) methods. All limits are used to calculate Average Outgoing Quality Level (AOQL).
(2) Typical numbers are at 25°C and represent the most likely norm.

### [vfb-note] 系统参数外部元件脚注

PDF 物理页 7 / 印刷页 7；区域 (54.0, 71.0, 558.0, 93.0)（PDF pt，左上原点）

(3) External components such as the catch diode, inductor, input and output capacitors can affect switching regulator system performance.
When the LM2596 is used as shown in Figure 9-13, system performance is shown in the test conditions column.

来源：https://www.ti.com/lit/ds/symlink/lm2596.pdf
版本：SNVS124G (Rev. G)
SHA-256：2eec90879908cf711b84d4f0c5d534c3cd12c576d25254b7019247435af4ab0f
