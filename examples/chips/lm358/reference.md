# TI LM358 / VOS

LM358 的失调电压典型 3 mV，25°C 最大 7 mV，全环境温度最大 9 mV；不混入 LM358A 或 B 版数值。

状态：answered

| 参数 | 类别 | MIN | TYP | MAX | 单位 | 条件 | 证据 |
|---|---|---:|---:|---:|---|---|---|
| VOS 输入失调电压 | 电气特性 | — | 3 | 7 | mV | VS=5–30 V；TA=25°C；VCM=0 V；VO=1.4 V | vos |
| VOS 输入失调电压 | 电气特性 | — | — | 9 | mV | VS=5–30 V；0≤TA≤70°C；VCM=0 V；VO=1.4 V | vos |
| dVOS/dT 失调电压漂移 | 电气特性 | — | 7 | — | μV/°C | 0≤TA≤70°C；VS=5 V；开环，VCM=0 V | vos |

参数注释：

- vos-25：所有典型值只在 TA=25°C 给出；数值列按原表保留。
- vos-full：所有典型值只在 TA=25°C 给出；数值列按原表保留。
- vos-drift：所有典型值只在 TA=25°C 给出；数值列按原表保留。

## 参数行条件匹配

输入（原样保留）：

- supply_voltage：5 V
- ambient_temperature：25 °C
- common_mode_voltage：0 V
- output_voltage：1.4 V
- open_loop：True

| 参数行 | 匹配结果 | 原因 |
|---|---|---|
| vos-25 | 已提供条件符合 | 已提供条件符合此行已整理的表头与行条件；典型值仍只按原表注明的温度有效。 |
| vos-full | 已提供条件符合 | 已提供条件符合此行已整理的表头与行条件；典型值仍只按原表注明的温度有效。 |
| vos-drift | 已提供条件符合 | 已提供条件符合此行已整理的表头与行条件；典型值仍只按原表注明的温度有效。 |

## 说明

- 典型值不等于保证上下限；空白表示手册未给出该列数值。各条件行分别有效，不自动合并或插值。
- 本页只使用当前TI型号适用行；原文片段可能同时列出其他型号，其数值不会自动转用于当前型号。
- 没有提供的测试设置不会默认满足。TA、TJ 与芯片型号分别匹配；多个适用行不自动合并。

## 原文证据

### [vos] 输入失调电压

PDF 物理页 10 / 印刷页 10；区域 (54.0, 123.0, 558.0, 201.0)（PDF pt，左上原点）

OFFSET VOLTAGE
3 7
LM358
VOS Input offset voltage V
V
S = 5 V to 30 V; VC M = 0 V; VO = 1.4
LM358A
TA = 0°C to 70°C
2
9
3
mV
TA = 0°C to 70°C 5
LM358 TA = 0°C to 70°C 7
dVOS/dT Input offset voltage drift µV/°C
LM358A TA = 0°C to 70°C 7 20

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
