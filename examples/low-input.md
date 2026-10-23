# TPS40200 / 4.3 V 能正常工作吗？

输入电压 VDD：不满足该项。不满足该项范围：4.3 V；允许 4.5–52 V（含边界）。欠压启动阈值的典型值不能代替推荐工作条件。

状态：answered

## 原始输入

- 输入电压 VDD：4.3 V


## 逐项检查

- 输入电压 VDD / 不满足该项：不满足该项范围：4.3 V；允许 4.5–52 V（含边界）。欠压启动阈值的典型值不能代替推荐工作条件。 [recommended]
- 结温 TJ / 信息不足：请提供结温 TJ及单位。 [recommended]
- 振荡频率 fOSC / 信息不足：请提供振荡频率 fOSC及单位。 [oscillator]
- RC 标称频率 / 信息不足：需要定时电阻 RRC 和电容 CRC，并明确单位。 [timing]
- 定时电阻电流 / 信息不足：需要输入电压 VDD 和定时电阻 RRC，并明确单位。 [timing]

## 说明

- 每项结论仅核对该项限制，不表示完整电路设计已通过。
- RC 公式为标称估算；不包含完整器件与元件容差模型。

## 原文证据

### [recommended] 6.3 推荐工作条件

PDF 物理页 4 / 印刷页 4；区域 (54.0, 395.0, 558.0, 462.0)（PDF pt，左上原点）

6.3 Recommended Operating Conditions
over operating free-air temperature range (unless otherwise noted)
MIN MAX UNIT
V Input voltage 4.5 52 V
DD
T Operating temperature range –40 125 °C
J

来源：https://www.ti.com/lit/ds/symlink/tps40200.pdf
版本：SLUS659G (Rev. G)
SHA-256：a3e23ec7367038ecd8f6ddbfc38392fcb87d997352eabb715b573de538a76240
