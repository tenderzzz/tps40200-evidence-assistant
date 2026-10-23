# TPS40200 / 反馈参考电压 VFB 是多少？

VFB 的典型值是 696 mV；上下限取决于测试条件，必须逐行读取。

状态：answered

| 参数 | 类别 | MIN | TYP | MAX | 单位 | 条件 | 证据 |
|---|---|---:|---:|---:|---|---|---|
| VFB 反馈参考电压 | 电气特性 | 689 | 696 | 702 | mV | COMP=FB；TA=25 °C；其余默认条件见表头 | reference |
| VFB 反馈参考电压 | 电气特性 | 686 | 696 | 703 | mV | 4.5 V < VDD < 52 V；TA=25 °C | reference |
| VFB 反馈参考电压 | 电气特性 | 679 | 696 | 708 | mV | 4.5 V < VDD < 52 V；−40 °C < TA < 85 °C | reference |
| VFB 反馈参考电压 | 电气特性 | 679 | 696 | 710 | mV | 4.5 V < VDD < 52 V；−40 °C < TA < 125 °C | reference |

参数注释：

- vfb-comp：默认 −40 °C < TA = TJ < 85 °C；VDD=12 V；fOSC=100 kHz，除非另有注明。
- vfb-25：默认 −40 °C < TA = TJ < 85 °C；VDD=12 V；fOSC=100 kHz，除非另有注明。
- vfb-85：默认 −40 °C < TA = TJ < 85 °C；VDD=12 V；fOSC=100 kHz，除非另有注明。
- vfb-125：默认 −40 °C < TA = TJ < 85 °C；VDD=12 V；fOSC=100 kHz，除非另有注明。

## 说明

- 典型值不等于保证上下限；空白表示手册未给出该列数值。各条件行分别有效，不自动合并或插值。

## 原文证据

### [reference] 6.5 反馈参考电压 VFB

PDF 物理页 5 / 印刷页 5；区域 (54.0, 114.0, 558.0, 181.0)（PDF pt，左上原点）

VOLTAGE REFERENCE
COMP = FB, T = 25°C 689 696 702
A
T = 25°C 686 696 703
A
V Feedback voltage mV
FB
4.5 < V < 52 –40°C < T < 85°C 679 696 708
DD A
–40°C < T < 125°C 679 696 710
A

表头／脚注上下文：
6.5 Electrical Characteristics
–40°C < T = T < 85°C, V = 12 V, f = 100 kHz (unless otherwise noted)
A J DD OSC
PARAMETER TEST CONDITIONS MIN TYP MAX UNIT

来源：https://www.ti.com/lit/ds/symlink/tps40200.pdf
版本：SLUS659G (Rev. G)
SHA-256：a3e23ec7367038ecd8f6ddbfc38392fcb87d997352eabb715b573de538a76240
