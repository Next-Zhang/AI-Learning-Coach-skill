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

- query：`pandas Series DataFrame`；limit：10；web 补充：是（显式判断依据：本地命中 3 条均为 pandas 通用资料（Series 基础/groupby 聚合/小技巧），当日核心知识点「DataFrame 创建操作」无对应本地资料，相关命中不足 3 条）

返回命中：
- （local）pandas Series 基础 — pandas 官方 Series 参考，覆盖一维数组的创建与基础操作。；来源：https://pandas.pydata.org/docs/reference/api/pandas.Series.html；链接：`D:\项目\数据库\ai_native_learning_tool\python-coach\.scratch\python-coach\rehearsal-10\sources\pandas-series.md`
- （local）pandas groupby 分组聚合 — pandas groupby 官方指南，按列分组后聚合（sum/mean），分组列默认变索引。；来源：https://pandas.pydata.org/docs/user_guide/groupby.html；链接：`D:\项目\数据库\ai_native_learning_tool\python-coach\.scratch\python-coach\rehearsal-10\sources\pandas-groupby.md`
- （local）数据分析小技巧 — 常用的小技巧合集。；来源：https://example.com/data-tips；链接：`D:\项目\数据库\ai_native_learning_tool\python-coach\.scratch\python-coach\rehearsal-10\sources\pandas-tips.md`
- （web）pandas 十分钟入门（DataFrame） — pandas 官方 10 分钟速览，覆盖 Series/DataFrame 创建与基础操作。；来源：https://pandas.pydata.org/docs/user_guide/10min.html；链接：`https://pandas.pydata.org/docs/user_guide/10min.html`
- （web）2 小时速通 Pandas（视频，B 站） — Pandas 由浅入深讲解，覆盖 Series/DataFrame 与常用操作。；来源：https://www.bilibili.com/video/BV1nDuv6tExp/；链接：`https://www.bilibili.com/video/BV1nDuv6tExp/`

## Day 4 — 数据读取与筛选

- query：`pandas 读取筛选`；limit：10；web 补充：是（显式判断依据：本地命中 3 条均与「读取/筛选」无关——Series 创建、groupby 聚合、小技巧；相关命中 0 条）

返回命中：
- （local）pandas Series 基础 — pandas 官方 Series 参考，覆盖一维数组的创建与基础操作。；来源：https://pandas.pydata.org/docs/reference/api/pandas.Series.html；链接：`D:\项目\数据库\ai_native_learning_tool\python-coach\.scratch\python-coach\rehearsal-10\sources\pandas-series.md`
- （local）pandas groupby 分组聚合 — pandas groupby 官方指南，按列分组后聚合（sum/mean），分组列默认变索引。；来源：https://pandas.pydata.org/docs/user_guide/groupby.html；链接：`D:\项目\数据库\ai_native_learning_tool\python-coach\.scratch\python-coach\rehearsal-10\sources\pandas-groupby.md`
- （local）数据分析小技巧 — 常用的小技巧合集。；来源：https://example.com/data-tips；链接：`D:\项目\数据库\ai_native_learning_tool\python-coach\.scratch\python-coach\rehearsal-10\sources\pandas-tips.md`
- （web）pandas 读写表格数据 — pandas 读取/写出表格数据（read_csv/read_excel），行筛选与列选择。；来源：https://pandas.pydata.org/docs/user_guide/io.html；链接：`https://pandas.pydata.org/docs/user_guide/io.html`
- （web）pandas 读取 Excel 文件及常用参数（视频，CSDN） — pandas 读取 excel 文件及常用参数，数据读取与清洗视频。；来源：https://edu.csdn.net/learn/31490/473845；链接：`https://edu.csdn.net/learn/31490/473845`

## Day 5 — Excel 读写

- query：`pandas Excel 读写`；limit：10；web 补充：是（显式判断依据：本地命中 3 条均与「Excel 读写」无关（无 read_excel/to_excel 资料）；相关命中 0 条）

返回命中：
- （local）pandas Series 基础 — pandas 官方 Series 参考，覆盖一维数组的创建与基础操作。；来源：https://pandas.pydata.org/docs/reference/api/pandas.Series.html；链接：`D:\项目\数据库\ai_native_learning_tool\python-coach\.scratch\python-coach\rehearsal-10\sources\pandas-series.md`
- （local）pandas groupby 分组聚合 — pandas groupby 官方指南，按列分组后聚合（sum/mean），分组列默认变索引。；来源：https://pandas.pydata.org/docs/user_guide/groupby.html；链接：`D:\项目\数据库\ai_native_learning_tool\python-coach\.scratch\python-coach\rehearsal-10\sources\pandas-groupby.md`
- （local）数据分析小技巧 — 常用的小技巧合集。；来源：https://example.com/data-tips；链接：`D:\项目\数据库\ai_native_learning_tool\python-coach\.scratch\python-coach\rehearsal-10\sources\pandas-tips.md`
- （web）pandas 读写 Excel — pandas.read_excel / DataFrame.to_excel 读写 Excel 文件，sheet 选择参数。；来源：https://pandas.pydata.org/docs/reference/api/pandas.read_excel.html；链接：`https://pandas.pydata.org/docs/reference/api/pandas.read_excel.html`
- （web）Pandas 数据分析 & Excel 办公自动化（视频，B 站） — Pandas + Excel 办公自动化动画讲解，覆盖读取/处理/写出 Excel。；来源：https://www.bilibili.com/video/av540310024/；链接：`https://www.bilibili.com/video/av540310024/`

## Day 6 — 数据清洗

- query：`pandas 数据清洗`；limit：10；web 补充：是（显式判断依据：本地命中 3 条均与「数据清洗」无关（无缺失值处理资料）；相关命中 0 条）

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
