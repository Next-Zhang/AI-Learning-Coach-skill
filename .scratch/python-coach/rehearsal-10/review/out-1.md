# 评审输出 out-1（rehearsal-10，评审轮 1）

评审依据：评审包裹 in-1.md（第 0 节任务说明、学习目标、范围声明、画像摘要、能力矩阵、计划草案全文、检索记录），并核对 sources/ 下 4 个本地资料文件的实测内容（python-basics.md / pandas-series.md / pandas-groupby.md / pandas-tips.md）。

---

## 一、真实性（Z）

结论：通过

问题清单：（无）

逐日核对说明（引用 ≤ 命中，无凭空来源、无无依据断言）：

- Day 1：引用 `sources/python-basics.md`，在 Day 1 命中（local）✓；assertion「变量与基础数据类型、if/elif/else 分支」与命中摘要「覆盖变量、条件、循环与函数」一致，本地文件实测含 if/else 条目 ✓。
- Day 2：引用 `sources/python-basics.md`（命中 ✓）+ `https://docs.python.org/3/tutorial/controlflow.html#defining-functions`（web 命中 ✓，摘要覆盖 def/参数/return；默认参数属该官方教程范畴）✓。
- Day 3：引用 `sources/pandas-series.md`（命中 ✓，摘要「Series 创建与基础操作」，本地文件实测含列表/字典创建、`DataFrame 由 Series 组成`）+ `https://pandas.pydata.org/docs/user_guide/10min.html`（web 命中 ✓，摘要覆盖 Series/DataFrame 创建与基础操作）✓。当日命中另有 pandas-groupby.md、pandas-tips.md 未引用，属「引用少于命中」，合法。
- Day 4：引用 `https://pandas.pydata.org/docs/user_guide/io.html`（web 命中 ✓，摘要含 read_csv/read_excel、行筛选与列选择，与「read_excel + 布尔筛选行与列」目标一致）✓。
- Day 5：引用 `https://pandas.pydata.org/docs/reference/api/pandas.read_excel.html`（web 命中 ✓，摘要含 read_excel/to_excel、sheet 选择参数，与「指定 sheet 参数读取」目标一致）✓。
- Day 6：引用 `https://pandas.pydata.org/docs/user_guide/missing_data.html`（web 命中 ✓，摘要含 isna/dropna/fillna、drop_duplicates，与目标一致）✓。
- Day 7：引用 `https://matplotlib.org/stable/tutorials/pyplot.html`（web 命中 ✓，摘要含 plot/scatter/bar、figure 与 axes）✓。
- Day 8：引用 `https://matplotlib.org/stable/users/explain/quick_start.html`（web 命中 ✓，摘要含标题、轴标签、网格、颜色、图例）✓。
- Day 9：引用 `sources/pandas-series.md` / `sources/pandas-groupby.md` / `sources/pandas-tips.md`，均曾在 Day 3–6 命中（series：D3/D4/D5/D6；groupby：D3/D4/D5/D6；tips：D3/D4/D5/D6）✓；该日不引入新断言，「分组聚合」（groupby 摘要覆盖 sum/mean）、「清洗后再绘图」（复用已检来源）均有依据 ✓。

结论：所有来源均在对应 Day 的检索命中内，无超出命中的引用，无无依据断言。通过。

---

## 二、合理性（R）

结论：通过

问题清单：

- [R-1] 建议 | Day 7 主题「matplotlib 基础绘图」| 当日为工作日（周四，预算 1h），同时安排折线图+柱状图两种图形、figure 与 axes 关系（matplotlib 最抽象概念之一）再加 2 个练习，单日份量偏紧 | 将 figure/axes 关系降级为「了解即可」或顺延至 Day 8；1h 内聚焦 plot/bar 两种基本图的练习
- [R-2] 建议 | Day 5–6 顺序 | 数据清洗在实际处理管线中通常早于最终 write-out，计划先做「读入→简单处理→写出」（Day 5）再学清洗（Day 6），顺序略反直觉（非前置依赖倒置，不阻塞） | 无需调整天数；在 Day 5 目标中注明「清洗将在 Day 6 引入」，或明确 Day 5 的「简单处理」仅为筛选（复用 Day 4）；Day 9 已正确整合「先清洗后成图」

其余核对（无硬伤）：

- 主题顺序无倒置：语法基础（Day 1–2）→ pandas（Day 3–4）→ Excel 处理（Day 5–6）→ 数据可视化（Day 7–8）→ 综合实战（Day 9），与 scope_covered 子领域顺序一致，无跨领域跳变。
- 深度铺垫充分：「低分子领域优先铺垫」——条件与循环 1.0、函数 1.0 各获完整或近完整独立天；pandas.DataFrame 1.0 与 Series 1.5 共享 Day 3；数据清洗 1.5、图表定制 1.5 各占完整一天；高分项（Excel 读写 3.0、数据读取与筛选 2.5、matplotlib 基础绘图 4.0）各占一天，份量分配比例合理。
- 份量逐日可行：每日目标 2–3 项 + 练习 2–3 个，工作日 1h 内基本可控（Day 1 变量+条件合一稍紧但可接受；Day 3 为周末 2h，3 个练习合理），无「明显超量」硬伤。

结论：无教学硬伤（无依赖倒置、无跨领域跳变、无超量阻塞问题）。通过。

---

## 三、适配性（S）

结论：有问题

问题清单：

- [S-1] 建议 | 全局（所有 Day）| 画像学习风格为「视频 + 动手练习」：动手练习确实每天都有、占比高（✓），但全计划 9 天 0 个视频来源，所有来源均为文字文档，视频偏好完全未体现（唯一未满足的画像维度） | 为每个 Day 补充 1 个匹配的官方/权威视频链接（如 Python 官方语法视频、pandas 10 分钟入门配套视频、matplotlib 官方 tutorial 视频）作为可选的替代来源，标注「或观看视频」，满足该偏好且不增加文字阅读负担

其余核对（均通过）：

- 目标：计划确实通向「用 Python 处理 Excel 报表并做数据分析」（读入→清洗→聚合→成图，Day 9 综合整合）✓。
- 起点匹配：自评 2，矩阵语法项 1~1.5，计划 Day 1–2 从变量/条件/函数打底 ✓。
- 时间预算：9 天 = 工作日 6 天×1h + 周末 3 天×2h ≈ 12h，位于估算区间 9~20h 内 ✓；综合实战日（Day 9 = 2026-08-29 周六）恰落在周末 2h 档位，项目日安排在宽裕档 ✓。
- 节奏：每天单一主题、无冲刺日，平缓 ✓。
- 压力 3：无密度冲刺天；周末 2h 用于项目属合理调配而非冲刺 ✓。
- 动手练习占比：每天均有 2–3 个练习，占比高，符合「动手练习」偏好 ✓。

结论：唯一未满足维度是「视频」偏好（建议级），其余维度全部匹配。有问题（1 项建议）。

---

## 四、边界交叉检查

结论：通过

问题清单：（无）

核对说明：

- scope_covered 四子领域全部覆盖，无遗漏：语法基础（Day 1–2）✓、数据分析/pandas（Day 3–4，Day 9 groupby/聚合）✓、Excel 处理（Day 5–6）✓、数据可视化（Day 7–8）✓。
- scope_excluded 零夹带：全计划 9 天均为 Python 语法 / pandas / Excel / matplotlib，无任何 Web 框架或网络爬虫内容。
- Day 9 的「分组聚合（groupby）」「产出含图表的分析小结」均属数据分析/可视化范畴，不在排除清单内。
- 能力矩阵 10 个知识点全部出现且无越界新知识点：变量与数据类型、条件与循环→Day 1；函数→Day 2；pandas.Series/DataFrame→Day 3；数据读取与筛选→Day 4/9；Excel 读写→Day 5/9；数据清洗→Day 6/9；matplotlib 基础绘图→Day 7/9；图表定制→Day 8/9。

结论：无遗漏子领域、无夹带排除内容。通过。

---

## 附：核对依据

- 检索记录：rehearsal-10 in-1.md 第 5 节（Day 1–9 命中清单）；计划所有来源均能在对应 Day 命中的找到。
- 本地 source 实测：python-basics.md（变量、if/else、for、函数定义）；pandas-series.md（一维带标签数组、列表/字典创建、DataFrame 由 Series 组成）；pandas-groupby.md（groupby().sum()、reset_index、agg 多聚合）；pandas-tips.md（技巧合集）。
