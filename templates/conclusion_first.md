# `/conclusion-first` 5-段报告模板

> Agent 任何 user-facing 报告都用这个。

```markdown
**Conclusion**: <一句话——成 / 败 / 待 user 决策 + 核心结果>

**What I changed**:
- <file:line> — <change>
- ...

**What I checked**:
- <test/audit/log> — <result>
- ...

**Risks**:
- <known unresolved> | "No known risks"
- ...

**Next step**:
- <agent will do X> 或 <AskUserQuestion: ?>
```

## 常见错误

❌ 省略 Risks 段
❌ 把 What I checked 写成「应该 / 觉得 / 大概」（必须是实证）
❌ Conclusion 写两句以上（一句话——必要时拆 sub-bullet）
❌ Next step 模糊（"看情况" 不算）

## 短回复豁免

简单 Q&A（如 "1+1 等于多少"）可只写 Conclusion 一段，但**不允许**长任务收尾省段。
