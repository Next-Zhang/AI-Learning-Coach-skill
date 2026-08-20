---
goal: 用 Python 处理 Excel 报表并做数据分析
scope_covered: [语法基础, 数据分析（pandas）, Excel 处理, 数据可视化]
scope_excluded: [Web 框架, 网络爬虫]
status: active
created: 2026-08-21
updated: 2026-08-21
---

# 学习计划

## 每日任务

### Day 1 — 2026-08-21
- 主题：Python 基础：变量、类型与条件
- 目标清单：
  - [ ] 读懂变量与基础数据类型（数字/字符串/布尔）
  - [ ] 用 if/elif/else 写分支逻辑
  - [ ] 完成 2 个变量与条件练习
- 知识点：变量与数据类型, 条件与循环
- 来源：sources/python-basics.md；https://www.bilibili.com/video/BV1Taug6eEcp/

### Day 2 — 2026-08-22
- 主题：函数（含默认参数）
- 目标清单：
  - [ ] 用 def 定义函数、传参并 return 返回值
  - [ ] 完成 2 个函数练习（含默认参数）
  - [ ] 读一段函数代码并解释其作用
- 知识点：函数
- 来源：sources/python-basics.md；https://docs.python.org/3/tutorial/controlflow.html#defining-functions；https://www.bilibili.com/video/BV1Taug6eEcp/

### Day 3 — 2026-08-23
- 主题：pandas 入门：Series 与 DataFrame
- 目标清单：
  - [ ] 理解 Series 是一维带标签数组
  - [ ] 用列表/字典创建 Series 与 DataFrame
  - [ ] 完成 3 个 pandas 基础操作练习
- 知识点：pandas.Series, pandas.DataFrame
- 来源：sources/pandas-series.md；https://pandas.pydata.org/docs/user_guide/10min.html；https://www.bilibili.com/video/BV1nDuv6tExp/

### Day 4 — 2026-08-24
- 主题：数据读取与筛选
- 目标清单：
  - [ ] 用 read_excel 读取表格数据
  - [ ] 用布尔条件筛选行与列
  - [ ] 完成 2 个读取 + 筛选练习
- 知识点：数据读取与筛选
- 来源：https://pandas.pydata.org/docs/user_guide/io.html；https://edu.csdn.net/learn/31490/473845

### Day 5 — 2026-08-25
- 主题：Excel 读写（清洗将在 Day 6 引入，Day 5 仅做读取与列筛选）
- 目标清单：
  - [ ] 用 pandas 读写 Excel（read_excel / to_excel）
  - [ ] 指定 sheet 参数读取工作表
  - [ ] 完成「读入 → 简单处理（仅筛选）→ 写出」小程序
- 知识点：Excel 读写
- 来源：https://pandas.pydata.org/docs/reference/api/pandas.read_excel.html；https://www.bilibili.com/video/av540310024/

### Day 6 — 2026-08-26
- 主题：数据清洗
- 目标清单：
  - [ ] 识别缺失值与重复行（isna / drop_duplicates）
  - [ ] 用 dropna / fillna 处理缺失值
  - [ ] 完成 2 个清洗练习
- 知识点：数据清洗
- 来源：https://pandas.pydata.org/docs/user_guide/missing_data.html；https://www.bilibili.com/video/av540310024/

### Day 7 — 2026-08-27
- 主题：matplotlib 基础绘图
- 目标清单：
  - [ ] 用 pyplot 画折线图与柱状图（figure 与 axes，了解即可）
  - [ ] 完成 2 个绘图练习
- 知识点：matplotlib 基础绘图
- 来源：https://matplotlib.org/stable/tutorials/pyplot.html；https://learn.microsoft.com/zh-cn/shows/even-more-python-for-beginners-data-tools/demo-visualizing-data-with-matplotlib--even-more-python-for-beginners-30-of-31

### Day 8 — 2026-08-28
- 主题：图表定制与美化
- 目标清单：
  - [ ] 添加标题、轴标签、网格
  - [ ] 用颜色与图例让图表可读
  - [ ] 完成「清洗后数据 → 定制图表」练习
- 知识点：图表定制
- 来源：https://matplotlib.org/stable/users/explain/quick_start.html；https://learn.microsoft.com/zh-cn/shows/even-more-python-for-beginners-data-tools/demo-visualizing-data-with-matplotlib--even-more-python-for-beginners-30-of-31

### Day 9 — 2026-08-29
- 主题：综合实战：从 Excel 报表到分析图表
- 目标清单：
  - [ ] 读入一份 Excel 报表并清洗
  - [ ] 做分组聚合分析并输出结论
  - [ ] 产出含图表的分析小结
- 知识点：数据读取与筛选, Excel 读写, 数据清洗, matplotlib 基础绘图, 图表定制
- 来源：sources/pandas-series.md；sources/pandas-groupby.md；sources/pandas-tips.md
