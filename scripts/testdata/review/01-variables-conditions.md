---
course: 01
date: 2026-08-21
topics: [变量与数据类型, 条件与循环]
---

# 01 — 变量、类型与条件

- **变量与数据类型**：数字/字符串/布尔等类型，`type(x)` 查看类型，变量可重新赋值。示例：`x = 3`；`x = "hi"`。常见坑：命名不合法报 SyntaxError（不能以数字开头、不能用关键字）；`int` 与 `str` 直接拼接报 TypeError，需 `str()` 转换。来源：sources/python-basics.md。
- **条件与循环**：`if/elif/else` 分支、`for` 遍历。示例：`if x > 0: print("正")`。常见坑：忘写冒号、缩进不一致报 IndentationError。来源：sources/python-basics.md。
