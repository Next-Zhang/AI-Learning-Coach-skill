# Ticket 12 演练记录 — 验收、当日总结与网页清除（Day 5 晚间，2026-08-25）

本演练按 `resources/acceptance-contract.md` 走通 Day 5 晚间收尾流程：**证据提交 → 逐目标核查 → 结论 → 完成度合成（7:3）→ 学习者确认（含质疑复核）→ 难度采集 → 验收写回画像 → 当日总结写入 progress.md → 网页删除**。脚本调用均为真实运行（退出码 0），产物见本目录。

## 0. 场景与前置数据

延续 rehearsal-11 的 Day 5 早晨产物，补 Day 1–4 进度，作为「Day 5 晚间」收尾状态：

- `plan.md`（ticket 10 终稿，`status: active`，9 天）；当日 Day 5 = 2026-08-25「Excel 读写（读取与列筛选）」。
- `page-out/day-5-2026-08-25.html`：本会话早晨由 `page.py` 生成的当日执行网页（6081 字节，从 rehearsal-11 拷贝的渲染实例副本）。
- `data/profile.md`（before 见 `data-before/profile.md`）：能力矩阵 10 行，Excel 读写 3.0（摸底 2026-08-20），Day 1–4 验收/复习增量在日志。
- `data/progress.md`（before 见 `data-before/progress.md`）：已含 Day 1–4 总结块（各自完成度 4/5、难度 刚好），frontmatter `updated: 2026-08-24`。
- `data/review/` 与 `data/sources/`：快查卡与资料（收尾本轮不写，仅作为当日其实完成的可读上下文）。

## 1. 证据提交（转写摘录）

学习者贴出当天成果：

```
我完成了 Day 5 的小程序：
df = pd.read_excel('报表.xlsx', sheet_name='明细')
df['金额'] = df.loc[df['金额'] > 100, '金额'] * 1.1  # 筛选后再加价，用 loc
df.to_excel('结果.xlsx', index=False)
```

学习者："早上练习里 `df[df['金额'] > 100]['金额'] = 0` 链式赋值没生效，按你提示改成 `df.loc[df['金额'] > 100, '金额'] = 0` 了，小程序里筛选那步用的就是 loc。中间还卡过 openpyxl 没装，你提示我 `pip install openpyxl` 后就好了。结果文件 `结果.xlsx` 我打开看过了，数据对。"（另附运行输出：`df.head()` 显示前 5 行、to_excel 后目录里有文件。）

## 2. 逐项目标核查（对照 plan.md Day 5 目标清单）

| 目标 | 判定 | 依据 |
| --- | --- | --- |
| 用 pandas 读写 Excel（read_excel / to_excel） | 达成 | 证据里 read_excel/to_excel 均成功运行，`结果.xlsx` 存在确认 |
| 指定 sheet 参数读取工作表 | 达成 | `sheet_name='明细'` 正确指定并读出 |
| 完成「读入 → 简单处理（仅筛选）→ 写出」小程序 | 达成 | 程序跑通；loc 筛选为教练早间纠错后修正（过程依赖纠错计入评分） |

**结论：完成**（3/3 达成）。理由：三项目标都有代码 + 运行结果证据；唯一修正点（链式索引赋值 → loc）在教练引导下已改对并理解原因。

## 3. 完成度合成（真实脚本运行）

教练自评 agent 评分 4，请学习者自评——学习者："全写出来了，我给 5。" → `scripts/completion.py`（input/ → output/；难度按契约属脚本可选字段、只回显不参与合成，本演练在脚本输入中一并带上，对话内采集时序按 §4 在确认完成度后进行）：

```json
{ "agent_score": 4.0, "self_score": 5.0, "raw": 4.3, "score": 4.5,
  "score_display": "4.5/5", "synthesis": "0.7 × 4 + 0.3 × 5 ≈ 4.5",
  "difficulty": "太难" }
```

展示："合成完成度 **4.5/5**（0.7 × 4 + 0.3 × 5 ≈ 4.5）。请确认，或告诉我哪里不对。"

## 4. 学习者确认环节（含质疑与复核）

**学习者质疑**："目标 3 条全达成，凭什么不是 5？再说既然这么难，完成度不该低一点吗？"

**agent 复核（无据维持）**："目标全达成 → 结论是『完成』没错；但完成度分数还含**过程质量**：loc 是你早间在教练纠错后改对的，独立完成度打一点点折，所以 agent 给 4 不是 5。至于难度——**难度单独记录、不参与完成度**（契约 §5）：今天难不代表你做得不好，反之也不代表做得好。openpyxl 是环境坑，安装就好，不是知识难度。你的自评 5 保留，合成就是 4.5/5。"

学习者："懂了，确认 4.5/5。"

**难度采集（契约 §4.4：确认完成度后单独问）**——教练："好。再单独问你一句今日难度（太难 / 刚好 / 太简单，独立记录、不参与完成度）：" 学习者："太难吧，卡 openpyxl 卡到抓狂，还有那个 loc 坑。" 教练："收到，记录『太难』。最终验收单：结论『完成』（3/3）+ 完成度 4.5/5 + 难度『太难』——确认后我就写回画像、写总结。" 学习者："确认。"

## 5. 验收结果写回（真实脚本运行）

写回清单：当日知识点 `Excel 读写`（当前 3.0，完成度 4.5 ≥ 4 → +0.5，上限 5）→ 学习者确认后 `scripts/profile.py`（`op=acceptance`，input/ → output/）：

```json
{ "op": "acceptance", "date": "2026-08-25", "topic": "Excel 读写",
  "source": "验收 Day 5", "old_score": 3.0, "new_score": 3.5, "delta": 0.5,
  "updated": true, "score": 4.5, "difficulty": "太难",
  "log_entry": "- 2026-08-25：验收 Day 5（完成度 4.5，难度 太难）→ Excel 读写 +0.5（3→3.5）" }
```

`data/profile.md`：能力矩阵 `Excel 读写` 行 3.0 → 3.5（更新时间/来源更新），增量记录追加一行；frontmatter `updated` 在本次写回前后均为 `2026-08-25`（晨间复习写回已设置同日，profile.py 语义为 updated=date，故本次快照间该字段无变化）；与 `data-before/profile.md` diff 一致。难度「太难」已独立入日志，不改变矩阵数值。

## 6. 当日总结写入 progress.md

教练起草 Day 5 总结块（格式遵循 `data-formats.md` §2）→ 展示 → 学习者确认后**追加**到 `data/progress.md` 末尾并更新 frontmatter `updated: 2026-08-25`（与 `data-before/progress.md` diff：仅尾部追加 Day 5 块 + updated 字段，既往日期内容未动）：

```markdown
## 2026-08-25 — Day 5
- 当日任务：Excel 读写（读取与列筛选；清洗 Day 6 引入）
- 完成度：4.5/5（0.7 × 4 + 0.3 × 5 ≈ 4.5）
- 难度反馈：太难
- 当日总结：学会 read_excel / to_excel 与 sheet_name 指定工作表，完成「读入 → 筛选 → 写出」小程序。卡点：openpyxl 缺失（环境坑，安装后解决）与链式索引赋值（过滤后赋值不生效，已改 loc 修正）。总评：3/3 目标达成，独立完成度还有提升空间（loc 由教练纠错）。后续 Day 6 清洗会用到这里学到的读写。
- 证据摘要：openpyxl 报错 → 修复后 read_excel('报表.xlsx', sheet_name='明细') 读出；df.loc[df['金额'] > 100, '金额'] = 0 筛选修正；to_excel('结果.xlsx') 写出文件确认存在；小程序完整代码见学习者本地脚本。
```

## 7. 网页清除（确认后）

教练提出："今天的执行网页 `day-5-2026-08-25.html` 是临时文件，验收与总结都完成了，我建议删除，页面不累积；模板留在技能里，明天重新生成。" 学习者确认 → 删除 `page-out/day-5-2026-08-25.html`（删除后不存在）。收尾汇报："Day 5 验收完成：完成度 4.5/5，总结已写入进度，当日网页已删除。明天见。"

## 8. 产物清单

- `data/`：验收后的工作数据（`plan.md` / `profile.md` / `progress.md` / `review/` / `sources/`，含 Day 5 验收结果）
- `data-before/`：验收前 `profile.md` / `progress.md` 快照
- `input/` → `output/`：completion、acceptance 输入输出 JSON
- `page-out/`：当日网页已删除（删除前为一渲染实例副本）
- 本文件：演练记录
