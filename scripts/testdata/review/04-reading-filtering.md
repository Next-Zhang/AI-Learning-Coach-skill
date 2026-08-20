---
course: 04
date: 2026-08-24
topics: [数据读取与筛选]
---

# 04 — 数据读取与筛选

- **读取 Excel**：`df = pd.read_excel('报表.xlsx', sheet_name='Sheet1')` 读取工作表。常见坑：未装 `openpyxl` 报 ImportError；`sheet_name` 拼错报 ValueError。来源：https://pandas.pydata.org/docs/user_guide/io.html。
- **布尔筛选**：`df[df['列'] > 100]` 按布尔掩码取行。常见坑：链式索引赋值 `df[df['列']>0]['列'] = 0` 不生效且有 SettingWithCopyWarning，应改用 `df.loc[df['列']>0, '列'] = 0`。来源：https://pandas.pydata.org/docs/user_guide/indexing.html。
