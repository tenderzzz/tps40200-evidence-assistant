# TI NE555 / TRIG

TRIG 典型阈值约为 VCC/3；NE555 的 5 V 与 15 V 参数行分别保留。

状态：answered

| 参数 | 类别 | MIN | TYP | MAX | 单位 | 条件 | 证据 |
|---|---|---:|---:|---:|---|---|---|
| TRIG 触发阈值 | 电气特性 | 4.5 | 5 | 5.6 | V | VCC=15 V；TA=25°C | trigger |
| TRIG 触发阈值 | 电气特性 | 1.1 | 1.67 | 2.2 | V | VCC=5 V；TA=25°C | trigger |

参数注释：

- trigger-15：
- trigger-5：

## 参数行条件匹配

输入（原样保留）：

- vcc：5 V
- ambient_temperature：25 °C

| 参数行 | 匹配结果 | 原因 |
|---|---|---|
| trigger-15 | 条件不符 | 不符合 供电电压 VCC 的原表条件。 |
| trigger-5 | 已提供条件符合 | 已提供条件符合此行已整理的表头与行条件；典型值仍只按原表注明的温度有效。 |

## 说明

- 典型值不等于保证上下限；空白表示手册未给出该列数值。各条件行分别有效，不自动合并或插值。
- 本页只使用当前TI型号适用行；原文片段可能同时列出其他型号，其数值不会自动转用于当前型号。
- 没有提供的测试设置不会默认满足。TA、TJ 与芯片型号分别匹配；多个适用行不自动合并。

## 原文证据

### [trigger] 触发阈值

PDF 物理页 5 / 印刷页 5；区域 (54.0, 445.0, 558.0, 527.0)（PDF pt，左上原点）

NA555, NE555, SA555 4.5 5 5.6
V = 15V
CC
SE555 4.8 5 5.2
V = 15V, T = –55°C to +125°C SE555 3 6
CC A
TRIG voltage level V
NA555, NE555, SA555 1.1 1.67 2.2
V = 5V
CC
SE555 1.45 1.67 1.9
V = 5V, T = –55°C to +125°C SE555 1.9
CC A

表头／脚注上下文：
5.5 Electrical Characteristics
at V = 5V to 15V and T = 25°C (unless otherwise noted)
CC A
PARAMETER TEST CONDITIONS MIN TYP MAX UNIT
跨页脚注（p.6）：(1) This parameter influences the maximum value of the timing resistors R and R in the circuit of Figure 6-5. For example, when
A B
V CC = 5V, the maximum value is R = R A + R B ≅ 3.4MΩ, and for V CC = 15V, the maximum value is R A + R B ≅ 10MΩ.

来源：https://www.ti.com/lit/ds/symlink/ne555.pdf
版本：SLFS022K (Rev. K)
SHA-256：a3756e59fd06d0ba736edf9ffe71d99d2aae33fb7e49fedc86165a241179f4a6
