"""jevaudit — 通用校准审计器（audit ANY decision model, not just Jev）。

decide → 三指纹账本 → Brier + 基线 + 校准曲线报告。
三轮实战沉淀的 gotchas 内建：真值语义先证伪 / price 语义修正 / 基线 0.25 常数。
"""
from jevaudit.ledger import canonical, input_hash, output_hash, code_hash, add_record, load_ledger
from jevaudit.gating import gate2, GateResult
from jevaudit.accuracy_report import brier_score, calibration_curve, report
from jevaudit.price_sem import implied_price, residual_check, match_tick
from jevaudit.physical_gate import require_task_env, log_action

__all__ = [
    "canonical", "input_hash", "output_hash", "code_hash", "add_record", "load_ledger",
    "gate2", "GateResult",
    "brier_score", "calibration_curve", "report",
    "implied_price", "residual_check", "match_tick",
    "require_task_env", "log_action",
]
__version__ = "0.1.1"
