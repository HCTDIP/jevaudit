# jevaudit — 通用校准审计器

> Audit ANY decision model, not just Jev.
> decide → 三指纹账本 → Brier + 基线 + 校准曲线报告。

## Why

任何"模型给概率、事后有真值"的决策系统都需要审计：置信度 p 和真实结果 o
到底差多少？是不是瞎猜？基线是多少？jevaudit 把审计变成三件套：
**账本（可回溯）+ Brier（可比较）+ 校准曲线（可诊断）**。

- **三指纹账本**：input_hash / output_hash / code_hash——输入给偏了、模型漂移了、
  判定脚本改了，首查指纹
- **基线内置**：全猜 0.5 的 Brier = **0.25 常数**（与结果分布无关），模型低于
  0.25 才是有用——报告自动对比，难听话自动打（>0.4 直接写"接近随机"）
- **前视防护**：审计时只看决策时点可得的信息，结算后的信息严禁进输入

## Install

```bash
pip install jevaudit   # (after publish — for now: copy the jevaudit/ directory)
```

## Quickstart

```python
from jevaudit import add_record, load_ledger, input_hash, output_hash, code_hash
from jevaudit import gate2, brier_score, calibration_curve, report

# 1) 每次决策记一条（三指纹 + check_spec 必填）
add_record("ledger.jsonl", {
    "id": "dec-001",
    "input_hash": input_hash(state, questions),   # sha256(规范输入)[:32]
    "output_hash": output_hash(response),         # sha256(响应)[:32]
    "code_hash": code_hash(),                     # sha256(判定脚本)[:16]
    "p": 0.95,                                    # 模型给的置信度
    "outcome": 1,                                 # 真实回填结果 (1/0)
    "check_spec": {"baseline": "implied_price", "tick": 0.01},  # 用的什么基准
})

# 2) 审计：Brier + 基线 + 校准曲线
rows = load_ledger("ledger.jsonl")
b = brier_score([r["p"] for r in rows], [r["outcome"] for r in rows])
curve = calibration_curve([r["p"] for r in rows], [r["outcome"] for r in rows])
report(rows, "calibration_report.md")   # 产出 Markdown（含 0.25 基线对比行）

# 3) 门控：KEEP / CONFIRM / DROP
action = gate2(0.75)   # KEEP (>=0.7) / CONFIRM (0.3-0.7) / DROP (<0.3)
```

## Gotchas（三轮实战沉淀，踩不到的坑）

1. **Brier 难看时，第一步永远是证伪校验基准**（真值语义/价格语义/结算语义），
   第二步才怀疑模型——两次实战：真值生成器语义反了 → Brier 必然反向
2. **price 列严禁精确校验**：展示价是截断/舍入价（残差恒 < 0.0125），
   真执行价 = `implied_price(usdcSize/size)`；校验用 tick 级容差（0.01/0.001）
3. **check_spec 必填**：记录用的什么基准/容差，让"度量分歧"可回溯，
   不然下个人又把基准当真值查一遍
4. **["0","0"] 是退化态**：已结算二元市场必须恰好一边=1，两边全 0 = 未真结算，拒
5. **outcomePrices 可能是字符串**（JSON 编码数组），先 json.loads 再算
6. **残差 <0 的反例（~1.4%）疑似 SELL 侧语义**：标注 `reverse`，不判死不混入
7. **样本 <3 不下结论**；漂移率 |mean_p − mean_o| > 0.01 如实打 ❌，不圆场

## 配套

- **jevkit**（PyPI）：OpenRouter Decisions API (Jev) 的第一个开源第三方客户端
  —— client + CLI + gate 模式
- 实战战绩：n=100 黑箱审计（Polymarket 真实交易 vs Jev，前视防护 100/100）

## License

MIT
