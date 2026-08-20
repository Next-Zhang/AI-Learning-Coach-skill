# 评审包裹 in-1（rehearsal-10，评审轮 1）

## 0. 评审任务说明（评审 agent 必读）

你是**独立评审 agent**（全新会话，与主教练会话完全隔离）。你只读本包裹与
D:\项目\数据库\ai_native_learning_tool\python-coach\.scratch\python-coach\rehearsal-10\sources 下的资料文件，不与其他会话交互，不修改任何文件（除了稍后写评审输出）。

请对本学习计划草案做**三份评审**，每份按以下格式输出：

    结论：通过 | 有问题
    问题清单：（无则留空）每项一行：`[编号] 级别（阻塞|建议）| 对应计划项 | 描述 | 建议修订`

- **真实性（Z）**：逐项对照「检索记录」——每个目标清单条目、知识点、主题断言须在对应 Day 的检索命中里找到依据（来源/摘要/链接）；引用了检索记录里不存在的来源、或无任何依据的断言 → 阻塞。引用可少于命中，但不可超出命中。
- **合理性（R）**：主题顺序（前置依赖是否倒置、跨天是否跳领域）、深度（对照能力矩阵分：低分子领域是否给了足够铺垫）、份量（对照每日时间预算：1 小时/天塞的知识点与练习是否过多）——教学硬伤（倒置、明显超量）→ 阻塞，其余为建议。
- **适配性（S）**：对照画像逐维核对——目标（计划是否真的通向它）、水平自评与矩阵起点、时间预算（总投入 = 天数 × 每日份量，估计约 9~20 小时，画像工作日 1h/周末 2h）、节奏（平缓）、压力（3，勿排冲刺天）、学习风格偏好（动手练习占比）。
- **边界交叉检查**：是否遗漏某个 scope_covered 子领域、是否夹带 scope_excluded 内容（发现即阻塞）。

三项评审输出后，把完整评审写入 `D:\项目\数据库\ai_native_learning_tool\python-coach\.scratch\python-coach\rehearsal-10\review\out-1.md`，然后回复一句话结论摘要即可。

## 1. 学习目标

用 Python 处理 Excel 报表并做数据分析

## 2. 范围声明

覆盖：语法基础、数据分析（pandas）、Excel 处理、数据可视化；不涉及：Web 框架、网络爬虫

## 3. 画像摘要

- Python 水平自评（1–5）：2（写过几行/只看过教程）
- 每日时间预算：工作日 1 小时，周末 2 小时
- 期望节奏：平缓，每天学一点
- 压力承受自评（1–5）：3（一般）
- 学习风格偏好：视频 + 动手练习

### 能力矩阵（知识点 × 水平分，来源：摸底测试）

| 知识点 | 水平分 | 子领域归属 |
| --- | --- | --- |
| 变量与数据类型 | 1.5 | 语法基础 |
| 条件与循环 | 1 | 语法基础 |
| 函数 | 1 | 语法基础 |
| pandas.Series | 1.5 | 数据分析（pandas） |
| pandas.DataFrame | 1 | 数据分析（pandas） |
| 数据读取与筛选 | 2.5 | 数据分析（pandas） |
| Excel 读写 | 3 | Excel 处理 |
| 数据清洗 | 1.5 | Excel 处理 |
| matplotlib 基础绘图 | 4 | 数据可视化 |
| 图表定制 | 1.5 | 数据可视化 |

## 4. 计划草案全文（评审对象）

```text
---
goal: 用 Python 处理 Excel 报表并做数据分析
scope_covered: [语法基础, 数据分析（pandas）, Excel 处理, 数据可视化]
scope_excluded: [Web 框架, 网络爬虫]
status: draft
created: 2026-08-21
updated: 2026-08-21
---

# 学习计划

## 每日任务

天数列推导：语法基础（矩阵均分 1.17 → 2 天）、数据分析 pandas（1.67 → 2 天）、Excel 处理（2.25 → 2 天）、数据可视化（2.75 → 2 天）= 8 天内容 + 产出型目标加 1 天综合实战 = 9 天；时间预算工作日 1h/周末 2h、节奏平缓、压力 3，均不触发天数调整。

### Day 1 — 2026-08-21
- 主题：Python 基础：变量、类型与条件
- 目标清单：
  - [ ] 读懂变量与基础数据类型（数字/字符串/布尔）
  - [ ] 用 if/elif/else 写分支逻辑
  - [ ] 完成 2 个变量与条件练习
- 知识点：变量与数据类型, 条件与循环
- 来源：sources/python-basics.md

### Day 2 — 2026-08-22
- 主题：函数
- 目标清单：
  - [ ] 用 def 定义函数、传参并 return 返回值
  - [ ] 完成 2 个函数练习（含默认参数）
  - [ ] 读一段函数代码并解释其作用
- 知识点：函数
- 来源：sources/python-basics.md；https://docs.python.org/3/tutorial/controlflow.html#defining-functions

### Day 3 — 2026-08-23
- 主题：pandas 入门：Series 与 DataFrame
- 目标清单：
  - [ ] 理解 Series 是一维带标签数组
  - [ ] 用列表/字典创建 Series 与 DataFrame
  - [ ] 完成 3 个 pandas 基础操作练习
- 知识点：pandas.Series, pandas.DataFrame
- 来源：sources/pandas-series.md；https://pandas.pydata.org/docs/user_guide/10min.html

### Day 4 — 2026-08-24
- 主题：数据读取与筛选
- 目标清单：
  - [ ] 用 read_excel 读取表格数据
  - [ ] 用布尔条件筛选行与列
  - [ ] 完成 2 个读取 + 筛选练习
- 知识点：数据读取与筛选
- 来源：https://pandas.pydata.org/docs/user_guide/io.html

### Day 5 — 2026-08-25
- 主题：Excel 读写
- 目标清单：
  - [ ] 用 pandas 读写 Excel（read_excel / to_excel）
  - [ ] 指定 sheet 参数读取工作表
  - [ ] 完成「读入 → 简单处理 → 写出」小程序
- 知识点：Excel 读写
- 来源：https://pandas.pydata.org/docs/reference/api/pandas.read_excel.html

### Day 6 — 2026-08-26
- 主题：数据清洗
- 目标清单：
  - [ ] 识别缺失值与重复行（isna / drop_duplicates）
  - [ ] 用 dropna / fillna 处理缺失值
  - [ ] 完成 2 个清洗练习
- 知识点：数据清洗
- 来源：https://pandas.pydata.org/docs/user_guide/missing_data.html

### Day 7 — 2026-08-27
- 主题：matplotlib 基础绘图
- 目标清单：
  - [ ] 用 pyplot 画折线图与柱状图
  - [ ] 理解 figure 与 axes 的关系
  - [ ] 完成 2 个绘图练习
- 知识点：matplotlib 基础绘图
- 来源：https://matplotlib.org/stable/tutorials/pyplot.html

### Day 8 — 2026-08-28
- 主题：图表定制与美化
- 目标清单：
  - [ ] 添加标题、轴标签、网格
  - [ ] 用颜色与图例让图表可读
  - [ ] 完成「清洗后数据 → 定制图表」练习
- 知识点：图表定制
- 来源：https://matplotlib.org/stable/users/explain/quick_start.html

### Day 9 — 2026-08-29
- 主题：综合实战：从 Excel 报表到分析图表
- 目标清单：
  - [ ] 读入一份 Excel 报表并清洗
  - [ ] 做分组聚合分析并输出结论
  - [ ] 产出含图表的分析小结
- 知识点：数据读取与筛选, Excel 读写, 数据清洗, matplotlib 基础绘图, 图表定制
- 来源：sources/pandas-series.md；sources/pandas-groupby.md；sources/pandas-tips.md
```

## 5. 检索记录（真实性核对手册）

# 检索记录（rehearsal-10）

计划草案各 Day 主题/知识点的检索层执行记录（`scripts/retrieve.py`，sources 目录：`rehearsal-10/sources/`）。本地相关命中不足 3 条时做一次 web 补充（相关性由主 agent 显式判断并记录）。本记录是三验证「真实性」的核对手册。

## Day 1 — 变量与数据类型、条件与循环

- query：`变量 数据类型 条件循环`；limit：10；web 补充：是（显式判断：本地相关命中不足 3 条）

返回命中：
- （local）Python 基础语法速览 — Python 官方教程速览，覆盖变量、条件、循环与函数。；来源：https://docs.python.org/3/tutorial/；链接：`D:\项目\数据库\ai_native_learning_tool\python-coach\.scratch\python-coach\rehearsal-10\sources\python-basics.md`
- （web）Python 零基础入门（视频，B 站） — Python 零基础全套视频教程，覆盖变量、条件、循环与函数。；来源：https://www.bilibili.com/video/BV1Taug6eEcp/；链接：`https://www.bilibili.com/video/BV1Taug6eEcp/`

## Day 2 — 函数

- query：`函数 def 参数`；limit：10；web 补充：是（显式判断：本地相关命中不足 3 条）

返回命中：
- （local）Python 基础语法速览 — Python 官方教程速览，覆盖变量、条件、循环与函数。；来源：https://docs.python.org/3/tutorial/；链接：`D:\项目\数据库\ai_native_learning_tool\python-coach\.scratch\python-coach\rehearsal-10\sources\python-basics.md`
- （web）Python 官方函数教程 — 函数定义 def、参数与 return 的官方教程。；来源：https://docs.python.org/3/tutorial/controlflow.html#defining-functions；链接：`https://docs.python.org/3/tutorial/controlflow.html#defining-functions`
- （web）Python 零基础入门（视频，B 站） — Python 零基础全套视频教程，覆盖变量、条件、循环与函数。；来源：https://www.bilibili.com/video/BV1Taug6eEcp/；链接：`https://www.bilibili.com/video/BV1Taug6eEcp/`

## Day 3 — pandas Series 与 DataFrame

- query：`pandas Series DataFrame`；limit：10；web 补充：是（显式判断：本地相关命中不足 3 条）

返回命中：
- （local）pandas Series 基础 — pandas 官方 Series 参考，覆盖一维数组的创建与基础操作。；来源：https://pandas.pydata.org/docs/reference/api/pandas.Series.html；链接：`D:\项目\数据库\ai_native_learning_tool\python-coach\.scratch\python-coach\rehearsal-10\sources\pandas-series.md`
- （local）pandas groupby 分组聚合 — pandas groupby 官方指南，按列分组后聚合（sum/mean），分组列默认变索引。；来源：https://pandas.pydata.org/docs/user_guide/groupby.html；链接：`D:\项目\数据库\ai_native_learning_tool\python-coach\.scratch\python-coach\rehearsal-10\sources\pandas-groupby.md`
- （local）数据分析小技巧 — 常用的小技巧合集。；来源：https://example.com/data-tips；链接：`D:\项目\数据库\ai_native_learning_tool\python-coach\.scratch\python-coach\rehearsal-10\sources\pandas-tips.md`
- （web）pandas 十分钟入门（DataFrame） — pandas 官方 10 分钟速览，覆盖 Series/DataFrame 创建与基础操作。；来源：https://pandas.pydata.org/docs/user_guide/10min.html；链接：`https://pandas.pydata.org/docs/user_guide/10min.html`
- （web）2 小时速通 Pandas（视频，B 站） — Pandas 由浅入深讲解，覆盖 Series/DataFrame 与常用操作。；来源：https://www.bilibili.com/video/BV1nDuv6tExp/；链接：`https://www.bilibili.com/video/BV1nDuv6tExp/`

## Day 4 — 数据读取与筛选

- query：`pandas 读取筛选`；limit：10；web 补充：是（显式判断：本地相关命中不足 3 条）

返回命中：
- （local）pandas Series 基础 — pandas 官方 Series 参考，覆盖一维数组的创建与基础操作。；来源：https://pandas.pydata.org/docs/reference/api/pandas.Series.html；链接：`D:\项目\数据库\ai_native_learning_tool\python-coach\.scratch\python-coach\rehearsal-10\sources\pandas-series.md`
- （local）pandas groupby 分组聚合 — pandas groupby 官方指南，按列分组后聚合（sum/mean），分组列默认变索引。；来源：https://pandas.pydata.org/docs/user_guide/groupby.html；链接：`D:\项目\数据库\ai_native_learning_tool\python-coach\.scratch\python-coach\rehearsal-10\sources\pandas-groupby.md`
- （local）数据分析小技巧 — 常用的小技巧合集。；来源：https://example.com/data-tips；链接：`D:\项目\数据库\ai_native_learning_tool\python-coach\.scratch\python-coach\rehearsal-10\sources\pandas-tips.md`
- （web）pandas 读写表格数据 — pandas 读取/写出表格数据（read_csv/read_excel），行筛选与列选择。；来源：https://pandas.pydata.org/docs/user_guide/io.html；链接：`https://pandas.pydata.org/docs/user_guide/io.html`
- （web）pandas 读取 Excel 文件及常用参数（视频，CSDN） — pandas 读取 excel 文件及常用参数，数据读取与清洗视频。；来源：https://edu.csdn.net/learn/31490/473845；链接：`https://edu.csdn.net/learn/31490/473845`

## Day 5 — Excel 读写

- query：`pandas Excel 读写`；limit：10；web 补充：是（显式判断：本地相关命中不足 3 条）

返回命中：
- （local）pandas Series 基础 — pandas 官方 Series 参考，覆盖一维数组的创建与基础操作。；来源：https://pandas.pydata.org/docs/reference/api/pandas.Series.html；链接：`D:\项目\数据库\ai_native_learning_tool\python-coach\.scratch\python-coach\rehearsal-10\sources\pandas-series.md`
- （local）pandas groupby 分组聚合 — pandas groupby 官方指南，按列分组后聚合（sum/mean），分组列默认变索引。；来源：https://pandas.pydata.org/docs/user_guide/groupby.html；链接：`D:\项目\数据库\ai_native_learning_tool\python-coach\.scratch\python-coach\rehearsal-10\sources\pandas-groupby.md`
- （local）数据分析小技巧 — 常用的小技巧合集。；来源：https://example.com/data-tips；链接：`D:\项目\数据库\ai_native_learning_tool\python-coach\.scratch\python-coach\rehearsal-10\sources\pandas-tips.md`
- （web）pandas 读写 Excel — pandas.read_excel / DataFrame.to_excel 读写 Excel 文件，sheet 选择参数。；来源：https://pandas.pydata.org/docs/reference/api/pandas.read_excel.html；链接：`https://pandas.pydata.org/docs/reference/api/pandas.read_excel.html`
- （web）Pandas 数据分析 & Excel 办公自动化（视频，B 站） — Pandas + Excel 办公自动化动画讲解，覆盖读取/处理/写出 Excel。；来源：https://www.bilibili.com/video/av540310024/；链接：`https://www.bilibili.com/video/av540310024/`

## Day 6 — 数据清洗

- query：`pandas 数据清洗`；limit：10；web 补充：是（显式判断：本地相关命中不足 3 条）

返回命中：
- （local）pandas Series 基础 — pandas 官方 Series 参考，覆盖一维数组的创建与基础操作。；来源：https://pandas.pydata.org/docs/reference/api/pandas.Series.html；链接：`D:\项目\数据库\ai_native_learning_tool\python-coach\.scratch\python-coach\rehearsal-10\sources\pandas-series.md`
- （local）pandas groupby 分组聚合 — pandas groupby 官方指南，按列分组后聚合（sum/mean），分组列默认变索引。；来源：https://pandas.pydata.org/docs/user_guide/groupby.html；链接：`D:\项目\数据库\ai_native_learning_tool\python-coach\.scratch\python-coach\rehearsal-10\sources\pandas-groupby.md`
- （local）数据分析小技巧 — 常用的小技巧合集。；来源：https://example.com/data-tips；链接：`D:\项目\数据库\ai_native_learning_tool\python-coach\.scratch\python-coach\rehearsal-10\sources\pandas-tips.md`
- （web）pandas 处理缺失数据 — 缺失值处理：isna/dropna/fillna，去重 drop_duplicates，类型转换。；来源：https://pandas.pydata.org/docs/user_guide/missing_data.html；链接：`https://pandas.pydata.org/docs/user_guide/missing_data.html`
- （web）Pandas 数据分析 & Excel 办公自动化（视频，B 站） — Pandas + Excel 办公自动化动画讲解，覆盖读取/处理/写出 Excel。；来源：https://www.bilibili.com/video/av540310024/；链接：`https://www.bilibili.com/video/av540310024/`

## Day 7 — matplotlib 基础绘图

- query：`matplotlib pyplot 基础绘图`；limit：10；web 补充：是（显式判断：本地相关命中不足 3 条）

返回命中：
- （web）matplotlib pyplot 快速上手 — pyplot 绘图函数库入门：plot/scatter/bar，figure 与 axes。；来源：https://matplotlib.org/stable/tutorials/pyplot.html；链接：`https://matplotlib.org/stable/tutorials/pyplot.html`
- （web）演示：使用 Matplotlib 可视化数据（视频，微软 Learn） — 微软 Learn 演示视频：用 Matplotlib 画图并定制图表。；来源：https://learn.microsoft.com/zh-cn/shows/even-more-python-for-beginners-data-tools/demo-visualizing-data-with-matplotlib--even-more-python-for-beginners-30-of-31；链接：`https://learn.microsoft.com/zh-cn/shows/even-more-python-for-beginners-data-tools/demo-visualizing-data-with-matplotlib--even-more-python-for-beginners-30-of-31`

## Day 8 — 图表定制

- query：`matplotlib 图表定制`；limit：10；web 补充：是（显式判断：本地相关命中不足 3 条）

返回命中：
- （web）matplotlib 定制图表 — 标题、轴标签、网格、颜色、图例 legend 等定制。；来源：https://matplotlib.org/stable/users/explain/quick_start.html；链接：`https://matplotlib.org/stable/users/explain/quick_start.html`
- （web）演示：使用 Matplotlib 可视化数据（视频，微软 Learn） — 微软 Learn 演示视频：用 Matplotlib 画图并定制图表。；来源：https://learn.microsoft.com/zh-cn/shows/even-more-python-for-beginners-data-tools/demo-visualizing-data-with-matplotlib--even-more-python-for-beginners-30-of-31；链接：`https://learn.microsoft.com/zh-cn/shows/even-more-python-for-beginners-data-tools/demo-visualizing-data-with-matplotlib--even-more-python-for-beginners-30-of-31`

## Day 9 — 综合实战

- query：`综合实战（复用）`；limit：10；web 补充：否

返回命中：

- 综合实战天：不引入新断言，目标全部复用已覆盖知识点（Day 3–8 已检来源）。引用的 `sources/pandas-series.md`、`sources/pandas-groupby.md`、`sources/pandas-tips.md` 均曾在 Day 3–6 检索命中。

