# 多芯片手册证据助手 v0.4

在本机查询 TI **TPS40200、LM2596-ADJ、LM358、NE555** 的参数、测试条件和原文，进行有限检查与公式估算。中文界面、确定性检索与规则，资料和依赖准备好后可离线使用，无需模型、账户或 API 密钥。

## 打开使用

双击 **启动证据助手.command**，或打开已经运行的 **http://127.0.0.1:8502/**。顶部选择芯片；型号与手册版本持续显示。关闭网页不会停止服务，在启动窗口按 Control+C 可停止。

首次准备环境需安装 Python 3.12 与 uv，然后在项目目录运行：

```sh
uv sync --frozen --extra dev
uv run --frozen tps-workbench --open
```

环境准备完成后：

```sh
uv run --offline --frozen tps-workbench --open
```

也可直接运行 `.venv/bin/python -m tps_evidence.server --open`。仅监听 127.0.0.1，不使用运行时模型、外部字体或 CDN。端口冲突时加 `--port 8503`。原有项目目录、启动命令和记录位置继续兼容。

旧 Streamlit 页面 `app.py` 保留为 TPS40200 兼容界面；新增的多芯片交互使用默认工作台。

## 支持范围

| TI 型号 | 固定手册 | 参数行 | 有限检查与计算 |
|---|---|---:|---|
| TPS40200 | SLUS659G / Rev. G / 2014-11 | 43 | VDD、TJ、频率、RC 标称频率与电流、元件容差 |
| LM2596-ADJ | SNVS124G / Rev. G / 2023-03 | 35 | 4.5–40 V 输入、反馈分压标称输出、下侧电阻应用建议 |
| LM358 | SLOS068AB / Rev. AB / 2024-10 | 40 | 正负电源总压差、环境温度、推荐与条件化电气共模范围 |
| NE555 | SLFS022K / Rev. K / 2026-03 | 40 | 供电与环境温度、单稳态脉宽、无稳态频率和输出高电平占空比、元件容差 |

LM2596 只支持可调版本，LM358 不转用 A/B/BA 参数，NE555 不转用其他 555 型号。原文可能是系列合订手册；结构化答案只保留当前型号适用行。未知型号明确报错，问题提到不同型号时提示切换。

每款完整保留适用的绝对最大额定值、推荐／工作条件和电气特性表格行；NE555 另整理开关特性。ESD、热阻和封装附页保存在完整 PDF 中，本轮未转录成参数库。MIN/TYP/MAX 的空白不填零，典型值不作为保证范围。

## 四个工作区

- **证据台**：输入参数符号或中文问题，查看数值、条件、脚注和引用。点击参数行定位 PDF；支持翻页、缩放、拖动及引脚功能查看。
- **条件检查**：只显示当前芯片的字段。每项结果分别显示满足、不满足、信息不足、无效输入或标称估算，不给整个电路通过的结论。
- **验证记录**：查看当前芯片的开发／留出案例、原文 BM25 基线、证据命中、参数事实正确率与回答覆盖率，可重跑和导出。
- **方案记录**：保存最后一次已完成的结果、载入、筛选、对比和备份。同型号比较输入、数值和条件匹配；跨型号仅并列展示原始快照，不生成替代或兼容结论。

顶部“导出”提供 Markdown／JSON，保留原始输入、状态、条件、英文原文、手册版本、SHA-256 与页码／坐标。未提交的表单草稿不会保存或导出。

### 条件筛选

参数查询后打开“条件”，填写已知条件，再点击“匹配条件”。多个符合行分别保留，条件不符的原始行可展开查看。缺少温度、供电或测试设置不会默认符合。

TPS40200 的 TA=TJ 是手册测试设置；LM358、NE555 的 TA 是环境温度，LM2596 的 VFB 行采用 TJ。环境温度不自动换成结温。未建模的复杂测试设置明确提示对照原文，不推断整行适用。

### 各芯片的公式边界

- **TPS40200**：频率与电流按原有规则计算；容差区间仅含输入的 R/C 容差，电流使用填写的固定 VDD。
- **LM2596-ADJ**：R1 为 FB→GND 的下侧电阻，R2 为 VOUT→FB 的上侧电阻。`VOUT≈1.23×(1+R2/R1)` 是标称估算；R1 的 240 Ω–1.5 kΩ 是应用建议。没有据此核验压差、热、磁性元件或布局。
- **LM358**：VS=V+−V−。推荐共模范围与电气特性测试行分别判断；25°C 的电气行与全温行不合并。输入共模满足不意味着输出摆幅、带宽或负载能力满足。
- **NE555**：单稳态约 `tw=1.1 RA C`；无稳态约 `tH=0.693(RA+RB)C`、`tL=0.693 RB C`，频率统一为 `1/(tH+tL)`，占空比为 `tH/(tH+tL)`。100 kHz 是减小失真的应用建议；触发时序、芯片本身误差、温漂和供电漂移不包含在元件容差区间内。单稳态不使用 RB。

容差需明确填写百分比，允许 0% 至小于 100%；空白不当作 0%。非法单位、零／负电阻电容和不支持的字段得到明确提示。

### 保存与兼容

记录默认保存在 `~/Library/Application Support/TPS40200 Evidence/records/`；`TPS_RECORDS_HOME` 可覆盖。每条记录独立原子写入，最多 200 条，重启后仍保留。

新记录使用 schema 2，保存芯片身份和应用版本；schema 1 的旧记录在读取时按 TPS40200 兼容，原文件不重写。载入记录自动切换芯片并按当前规则重算，原快照不变；手册哈希不同则保留旧快照，阻止直接重算。备份可导出全部记录，当前没有备份导入或删除界面。

切换页面和芯片会保留本次打开网页期间的独立草稿；刷新、关闭网页不自动保存草稿。需要保留结果时使用“保存方案”。

## 资料、整理与出处

TPS40200 资料沿用 `data/`；新增芯片分别存于 `data/chips/<chip_id>/`。每款分为：

- `source/`：官方 PDF、下载元数据和 manifest，记录网址、修订号、时间及 SHA-256。
- `raw/`：未经修正的 PDF 文本、行坐标和相关页的表格提取结果。
- `curated/`：对照原图转录的参数、测试条件、行坐标、证据规范与整理日志。
- `processed/`：可检索的带坐标证据。新增芯片仅索引已明确适用的整理区块；完整 PDF 均可浏览。

坐标为 PDF point，左上原点 `(x0, top, x1, bottom)`，页码从 1 开始。跨页脚注有独立证据 ID 和坐标，可单独点击定位。

固定 PDF 在查询与页面读取时校验哈希，缓存按芯片和手册哈希隔离。更换手册需要重新复核参数、坐标、条件和验证集。

整理由 Codex 对照固定原图完成，尚无独立第三方复核。LM2596 第5页 SD/SS、Delay、Flag 与其引脚表不一致，未转录为答案或规则；稳态开关输出电压的反常 MAX 列照原列保存并注明待核对。原表合并限制栏如 Internally limited、Unlimited 保存为条件文本，不伪填成 TYP 值。具体决定在各款 review_log.json 中。

官方来源为 TI 的 TPS40200、LM2596、LM358、NE555 数据手册；文件版权归 Texas Instruments，保留完整文件用于本地出处核对。

## 验证与示例

**134 项自动化测试通过，4 款共 240/240 个固定案例通过**；每款开发／留出各 30 个，同一问题的改写归入同组。各芯片留出集的证据前三条命中、已预标注参数事实正确率及回答覆盖率均为 100%。这仅描述本组自建案例，不能推广为任意问题准确率。

验证涵盖单位与边界、TA/TJ 区分、布尔测试设置、型号后缀、共享手册中的参数归属、容差端点、并行查询、文件替换、旧记录不改写和接口导出。期望来自固定 PDF 转录或独立有理数计算，未从被测实现生成；题目与实现来自同一开发过程，尚非独立盲测。

各款报告位于 `reports/chips/<chip_id>/`，TPS40200 原报告沿用 `reports/`。总览见 `reports/multichip-evaluation.md`，交互验收见 `reports/features-v04.md`。旧版本的首次留出结果和修正记录保留。

28 组实际 CSS 文字／控件颜色对比度检查通过；文字至少 4.88:1，控件至少 3.63:1。已检查 1280px 桌面及 320px 手机布局，页面无横向溢出；原文画布与对比表允许内部滚动。这不是完整 WCAG 认证。

原有三个 TPS40200 案例保留；每款新芯片的三个界面示例及 Markdown／JSON 导出在 `examples/chips/<chip_id>/`。这些是手册与公式验证，不是实测硬件结果。

## 开发接口与复现

```python
from tps_evidence.engine import query
from tps_evidence.rules import check

query("VFB")  # 兼容旧调用，默认 TPS40200
query("TRIG", {"vcc": "5 V", "ambient_temperature": "25 °C"}, chip_id="ne555")
check({"vin": "12 V", "r_lower": "1 kΩ", "r_upper": "3 kΩ"}, chip_id="lm2596-adj")
```

HTTP 查询、检查、导出和保存请求使用 `chip_id`，默认 `tps40200`。`GET /api/chips` 列出型号与能力；`GET /api/bootstrap?chip_id=ne555` 返回该芯片资料、字段与示例。`GET /api/pages/12.png?chip_id=ne555`、`GET /api/source.pdf?chip_id=ne555` 和评测接口同样指定芯片。`POST /api/records` 接收名称和最后一次完成的 request；`GET /api/records` 可按 chip_id 筛选。

```sh
uv run --offline --frozen pytest -q
uv run --offline --frozen python scripts/check_contrast.py
uv run --offline --frozen tps-evidence evaluate --chip all --split all
uv run --offline --frozen tps-evidence query 'VOS' --chip lm358 --format md
uv run --offline --frozen tps-evidence check --chip ne555 --mode astable --ra '10 kΩ' --rb '10 kΩ' --capacitance '10 nF' --format md
uv run --offline --frozen python -m scripts.export_multichip_examples
```

新增芯片的资料重建使用 `python -m scripts.prepare_multichip` 与 `python -m scripts.prepare_multichip_benchmark`；也可 `tps-evidence ingest --chip lm358` 重建单款。只允许对固定、已复核的手册运行，脚本会核对版本与下载时哈希。原 TPS40200 的准备脚本与入口继续保留。

项目按完整目录使用；`uv.lock` 固定依赖，`TPS_EVIDENCE_HOME` 可指定包含 data 的项目根目录。当前不提供任意 PDF 上传、自由生成回答、曲线自动读数、完整电路设计或跨芯片选型推荐。
