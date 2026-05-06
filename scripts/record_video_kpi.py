"""BA CF 16.5 — Manuelle KPI aus JSON erfassen und Feedback-Loop ausgeben."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.cash_optimization.schema import CashOptimizationLayerResult
from app.cash_feedback.loop import run_real_kpi_feedback_loop


def main() -> int:
    parser = argparse.ArgumentParser(description="Real KPI JSON → Feedback-Loop (CF 16.5–16.9).")
    parser.add_argument("metrics_json", help="Pfad zu metrics.json")
    parser.add_argument(
        "--cash-layer-json",
        dest="cash_layer_json",
        help="Optional: gespeichertes cash_optimization_layer_result (PromptPlan-JSON-Ausschnitt)",
    )
    args = parser.parse_args()

    metrics = json.loads(Path(args.metrics_json).read_text(encoding="utf-8"))
    cash_layer = None
    if args.cash_layer_json:
        raw = json.loads(Path(args.cash_layer_json).read_text(encoding="utf-8"))
        cash_layer = CashOptimizationLayerResult.model_validate(raw)

    result = run_real_kpi_feedback_loop(metrics, cash_layer=cash_layer)
    print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
