---
course: 02
date: 2026-08-22
topics: [函数]
---

# 02 — 函数

- **函数定义与调用**：`def 名(参数):` 定义、`return` 返回值、默认参数。示例：`def add(a, b=1): return a + b`。常见坑：默认参数在定义时求值（不要用可变对象作默认值，如 `def f(x, lst=[])`）；忘写 `return` 返回 None。来源：sources/python-basics.md。
