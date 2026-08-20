---
course: 03
date: 2026-08-23
topics: [pandas.Series, pandas.DataFrame]
---

# 03 — pandas Series 与 DataFrame

- **Series**：一维带标签数组。示例：`s = pd.Series([1, 2, 3])`。常见坑：索引不连续时 `s[0]` 按位置取，标签恰为 0 时按标签取，易混；优先用 `s.iloc[0]` / `s.loc[0]`。来源：sources/pandas-series.md。
- **DataFrame**：二维表，由 Series 组成。示例：`pd.DataFrame({'a': [1, 2], 'b': [3, 4]})`。常见坑：列名大小写敏感；`df['缺列']` 报 KeyError。来源：sources/pandas-series.md。
