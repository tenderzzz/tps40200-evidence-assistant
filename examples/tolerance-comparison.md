# TPS40200 方案对比

A：示例：200 kΩ，1% / 5%
B：示例：改为 1 kΩ

对比保留保存时的快照，不自动重算或给出整个电路通过的结论。单位不同但物理数值相同的输入单独标注。

| 输入 | A | B | 变化 |
|---|---|---|---|
| 输入电压 VDD | 12 V | 12 V | 相同 |
| 结温 TJ | 25 °C | 25 °C | 相同 |
| 振荡频率 fOSC | 100 kHz | 100 kHz | 相同 |
| 定时电阻 RRC | 200 kΩ | 1 kΩ | 数值／条件变化 |
| 定时电容 CRC | 470 pF | 470 pF | 相同 |
| 电阻容差 | 1% | 1% | 相同 |
| 电容容差 | 5% | 5% | 相同 |

| 检查 | A | B |
|---|---|---|
| 输入电压 VDD | satisfied；满足该项范围：12 V；允许 4.5–52 V（含边界）。 | satisfied；满足该项范围：12 V；允许 4.5–52 V（含边界）。 |
| 结温 TJ | satisfied；满足该项范围：25 °C；允许 -40–125 °C（含边界）。 | satisfied；满足该项范围：25 °C；允许 -40–125 °C（含边界）。 |
| 振荡频率 fOSC | satisfied；满足该项范围：100 kHz；允许 35–500 kHz（含边界）。该频率范围仅由设计保证，未进行生产测试。 | satisfied；满足该项范围：100 kHz；允许 35–500 kHz（含边界）。该频率范围仅由设计保证，未进行生产测试。 |
| RC 标称频率 | estimated；fSW=1/(RRC×CRC×0.105)≈101.317 kHz；这是标称估算，不保证实际频率精度。 | estimated；fSW=1/(RRC×CRC×0.105)≈20263.4 kHz；这是标称估算，不保证实际频率精度。 |
| RC 估算频率范围 | satisfied；估算频率在35–500 kHz 范围；实际频率仍受器件及 RC 容差影响。 | violated；估算频率超出35–500 kHz 范围；实际频率仍受器件及 RC 容差影响。 |
| 定时电阻电流 | satisfied；VIN/RRC=60 μA；满足≤750 μA 的约束（含边界）。 | violated；VIN/RRC=12000 μA；不满足≤750 μA 的约束（含边界）。 |
| RC 元件容差频率区间 | estimated；仅由 RRC ±1.00%、CRC ±5.00% 得到约 95.5371–107.727 kHz；下界取 Rmax、Cmax，上界取 Rmin、Cmin。芯片自身误差未计入。 | estimated；仅由 RRC ±1.00%、CRC ±5.00% 得到约 19107.4–21545.4 kHz；下界取 Rmax、Cmax，上界取 Rmin、Cmin。芯片自身误差未计入。 |
| 容差区间与频率限制 | satisfied；元件容差估算区间全部落入35–500 kHz；这项检查不包含芯片振荡器误差。 | violated；元件容差估算区间未全部落入35–500 kHz；这项检查不包含芯片振荡器误差。 |
| 电阻容差下最大电流 | satisfied；固定 VDD=12 V，Rmin=198000.00 Ω 时 Imax≈60.6061 μA；满足≤750 μA。未计入供电变化；电容容差不影响此项。 | violated；固定 VDD=12 V，Rmin=990.00 Ω 时 Imax≈12121.2 μA；不满足≤750 μA。未计入供电变化；电容容差不影响此项。 |

## A 来源
SLUS659G (Rev. G)
SHA-256：a3e23ec7367038ecd8f6ddbfc38392fcb87d997352eabb715b573de538a76240

[recommended] 6.3 推荐工作条件 / PDF 页 4
6.3 Recommended Operating Conditions
over operating free-air temperature range (unless otherwise noted)
MIN MAX UNIT
V Input voltage 4.5 52 V
DD
T Operating temperature range –40 125 °C
J


[oscillator] 6.5 振荡器频率 / PDF 页 5
OSCILLATOR
Oscillator frequency range(1) 35 500
f R = 200 kΩ, C = 470 pF 85 100 115 kHz
OSC RC RC
Oscillator frequency
R = 68.1 kΩ, C = 470 pF 255 300 345
RC RC
6.5 Electrical Characteristics
–40°C < T = T < 85°C, V = 12 V, f = 100 kHz (unless otherwise noted)
A J DD OSC
PARAMETER TEST CONDITIONS MIN TYP MAX UNIT
(1) Ensured by design. Not production tested.

[timing] 7.3.3 RC 定时公式与电流约束 / PDF 页 12
7.3.3 Selecting the Operating Frequency
The operating frequency of the controller is determined by an external resistor R that is connected from the RC
RC
pin to VDD and a capacitor attached from the RC pin to ground. This connection and the two oscillator
comparators inside the device, are shown in Figure 24. The oscillator frequency can be calculated in Equation 1.
1
f =
SW R ´ C ´ 0.105
RC RC (1)
where
f is the clock frequency
SW
R is the timing resistor value in Ω
RC
C is the timing capacitor value in F
RC
R must be kept large enough that the current through it does not exceed 750 μA when the internal switch
RC
(shown in Figure 24) is discharging the timing capacitor. This condition may be expressed by Equation 2.
V
IN £ 750 mA
R
RC (2)


## B 来源
SLUS659G (Rev. G)
SHA-256：a3e23ec7367038ecd8f6ddbfc38392fcb87d997352eabb715b573de538a76240

[recommended] 6.3 推荐工作条件 / PDF 页 4
6.3 Recommended Operating Conditions
over operating free-air temperature range (unless otherwise noted)
MIN MAX UNIT
V Input voltage 4.5 52 V
DD
T Operating temperature range –40 125 °C
J


[oscillator] 6.5 振荡器频率 / PDF 页 5
OSCILLATOR
Oscillator frequency range(1) 35 500
f R = 200 kΩ, C = 470 pF 85 100 115 kHz
OSC RC RC
Oscillator frequency
R = 68.1 kΩ, C = 470 pF 255 300 345
RC RC
6.5 Electrical Characteristics
–40°C < T = T < 85°C, V = 12 V, f = 100 kHz (unless otherwise noted)
A J DD OSC
PARAMETER TEST CONDITIONS MIN TYP MAX UNIT
(1) Ensured by design. Not production tested.

[timing] 7.3.3 RC 定时公式与电流约束 / PDF 页 12
7.3.3 Selecting the Operating Frequency
The operating frequency of the controller is determined by an external resistor R that is connected from the RC
RC
pin to VDD and a capacitor attached from the RC pin to ground. This connection and the two oscillator
comparators inside the device, are shown in Figure 24. The oscillator frequency can be calculated in Equation 1.
1
f =
SW R ´ C ´ 0.105
RC RC (1)
where
f is the clock frequency
SW
R is the timing resistor value in Ω
RC
C is the timing capacitor value in F
RC
R must be kept large enough that the current through it does not exceed 750 μA when the internal switch
RC
(shown in Figure 24) is discharging the timing capacitor. This condition may be expressed by Equation 2.
V
IN £ 750 mA
R
RC (2)

