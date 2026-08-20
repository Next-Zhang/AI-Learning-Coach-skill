---
title: pandas groupby 分组聚合
source: https://pandas.pydata.org/docs/user_guide/groupby.html
topics: [pandas, groupby, 聚合]
date: 2026-08-19
summary: pandas groupby 官方指南，按列分组后聚合（sum/mean），分组列默认变索引。
---

# groupby 分组聚合

按列分组后聚合：`df.groupby('key').sum()`；常见坑：分组列默认变索引，用 `reset_index()` 恢复。

`agg` 支持多聚合：`df.groupby('key').agg(['sum', 'mean'])`。
