# 摸底测试题目集（演练 · ticket 09）

- **日期**：2026-08-20
- **范围**（来自 plan.md 草案 `scope_covered`）：`语法基础`、`数据分析（pandas）`、`Excel 处理`、`数据可视化`
- **题量**：18 题（选择 10 + 简答 4 + 实操 4）｜难度 1–5 全覆盖（d1×2、d2×8、d3×4、d4×3、d5×1，低档多于高档）
- **知识点**：10 个，每子领域 ≥ 2 题

## Q1 选择 d1 变量与数据类型（语法基础）
下面哪个是合法的 Python 变量名？
- A. `2name`　B. `my_var`　C. `my-var`　D. `class`
- 参考答案：B
- 依据：sources/python-basics.md（标识符规则）

## Q2 选择 d2 变量与数据类型（语法基础）
`type(3.14)` 的返回值是？
- A. `int`　B. `float`　C. `str`　D. `bool`
- 参考答案：B
- 依据：sources/python-basics.md（内置类型）

## Q3 简答 d2 条件与循环（语法基础）
用 `for` 循环打印 1 到 5 的整数，每行一个。
- 评分要点：`for i in range(1, 6)`（0.5）；`print(i)` 在循环体内（0.5）
- 依据：sources/python-basics.md（range 与 for）

## Q4 实操 d2 函数（语法基础）
定义一个函数 `add(a, b)` 返回 `a` 与 `b` 的和，并调用它计算 `add(2, 3)`。贴出代码与运行结果。
- 评分要点：`def add(a, b):` 定义（0.4）；`return a + b`（0.3）；调用并打印结果（0.3）
- 依据：sources/python-basics.md（函数定义与调用）

## Q5 选择 d3 条件与循环（语法基础）
```python
i = 0
while i < 3:
    print(i)
    i += 1
```
上面代码 `print(i)` 执行几次？
- A. 2 次　B. 3 次　C. 4 次　D. 无限次
- 参考答案：B
- 依据：sources/python-basics.md（while 与自增）

## Q6 选择 d2 pandas.Series（数据分析（pandas））
创建 Series 的正确方式是？
- A. `pd.Series([1, 2, 3])`　B. `pd.series([1, 2, 3])`　C. `Series([1, 2, 3])`　D. `pd.Series{1, 2, 3}`
- 参考答案：A
- 依据：sources/pandas-series.md（Series 创建）

## Q7 选择 d3 pandas.DataFrame（数据分析（pandas））
`df` 是 DataFrame，`df['列名']` 返回的是？
- A. DataFrame　B. Series　C. 列表　D. 字典
- 参考答案：B
- 依据：sources/pandas-series.md / pandas-groupby.md（列选取）

## Q8 简答 d3 数据读取与筛选（数据分析（pandas））
读取 CSV：`df = pd.read_csv('data.csv')`，筛出 `score` 列大于 100 的行。写代码。
- 评分要点：`read_csv` 读取（0.3）；条件筛选 `df[df['score'] > 100]`（0.5）；赋值或展示结果（0.2）
- 依据：sources/pandas-series.md（条件筛选）

## Q9 实操 d4 pandas.DataFrame（数据分析（pandas））
对 `df` 按 `部门` 列分组，求每组的 `工资` 均值并打印。贴代码与运行结果。
- 评分要点：`df.groupby('部门')`（0.4）；`['工资'].mean()`（0.4）；打印结果（0.2）
- 依据：sources/pandas-groupby.md（分组聚合）

## Q10 选择 d5 pandas.Series（数据分析（pandas））
```python
s1 = pd.Series([1, 2], index=['a', 'b'])
s2 = pd.Series([10], index=['b'])
```
`s1 + s2` 的结果是？
- A. 全部为 NaN　B. `a` 为 NaN、`b` 为 12　C. 直接报错　D. `b` 为 12
- 参考答案：B
- 依据：sources/pandas-series.md（索引对齐）

## Q11 选择 d1 Excel 读写（Excel 处理）
Python 中常用于读写 Excel 文件的库是？
- A. `openpyxl`　B. `requests`　C. `os`　D. `json`
- 参考答案：A
- 依据：sources/（Excel 处理资料，需补充）

## Q12 选择 d2 数据清洗（Excel 处理）
`df.dropna()` 的作用是？
- A. 删除重复行　B. 删除含缺失值的行　C. 填充缺失值　D. 按列排序
- 参考答案：B
- 依据：sources/（数据清洗资料，需补充）

## Q13 实操 d3 Excel 读写（Excel 处理）
用 pandas 读取 `报表.xlsx` 并打印总行数。贴代码与运行结果。
- 评分要点：`pd.read_excel('报表.xlsx')`（0.5）；统计行数 `df.shape[0]` 或 `len(df)`（0.5）
- 依据：sources/（Excel 处理资料，需补充）

## Q14 简答 d4 数据清洗（Excel 处理）
数据中存在缺失值，说明一种处理缺失值的方法并给出代码。
- 评分要点：说明方法名（`dropna` / `fillna` 等，0.5）；给出对应代码（0.5）
- 依据：sources/（数据清洗资料，需补充）

## Q15 选择 d2 matplotlib 基础绘图（数据可视化）
用 matplotlib 画完图后，显示图像的函数是？
- A. `plt.show()`　B. `plt.display()`　C. `plt.print()`　D. `plt.render()`
- 参考答案：A
- 依据：sources/（数据可视化资料，需补充）

## Q16 选择 d2 图表定制（数据可视化）
给图表添加标题的函数是？
- A. `plt.title()`　B. `plt.label()`　C. `plt.heading()`　D. `plt.caption()`
- 参考答案：A
- 依据：sources/（数据可视化资料，需补充）

## Q17 简答 d2 matplotlib 基础绘图（数据可视化）
用 pyplot 画一条最简单的折线图，需要哪几行代码？
- 评分要点：导入 `import matplotlib.pyplot as plt`（0.4）；`plt.plot(x, y)`（0.3）；`plt.show()`（0.3）
- 依据：sources/（数据可视化资料，需补充）

## Q18 实操 d4 图表定制（数据可视化）
用 matplotlib 画一个柱状图并加标题。贴代码与运行结果。
- 评分要点：`plt.bar(x, y)`（0.4）；`plt.title(...)`（0.3）；`plt.show()`（0.3）
- 依据：sources/（数据可视化资料，需补充）
