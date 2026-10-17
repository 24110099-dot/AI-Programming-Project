import argparse
import asyncio
import json
import logging
import os
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from policy_agent.agent.loop import run_agent
from policy_agent.config import load_settings
from policy_agent.eval.metrics import evaluate_single_record
from policy_agent.eval.report import plot_comparison_chart, print_summary, write_csv
from policy_agent.llm.client import call_llm
from policy_agent.models import Usage

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


class LLMJudgeHelper:
    def __init__(self, settings=None):
        self.settings = settings or load_settings()
        self.usage = Usage()

    def ask(self, prompt: str, temperature: float = 0.0) -> str:
        messages = [{"role": "user", "content": prompt}]
        return call_llm(messages, self.settings, self.usage)


def load_testset(path: Path) -> list[dict]:
    if not path.exists():
        return []
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                records.append(json.loads(line))
    return records


async def run_benchmark_for_mode(
    items: list[dict],
    mode: str,
    llm_client: LLMJudgeHelper | None = None,
    requests_path: Path | None = None,
    log_file: Path | None = None,
) -> list[dict]:
    os.environ["RETRIEVAL_MODE"] = mode
    results = []
    log_fp = None
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        log_fp = open(log_file, "w", encoding="utf-8")
    try:
        for idx, item in enumerate(items, 1):
            q_id = item.get("id", f"Q{idx:02d}")
            question = item.get("question", "")
            logger.info("[%d/%d] %s: %s", idx, len(items), q_id, question[:50])
            start_t = datetime.now(timezone.utc)
            trace_obj = await run_agent(question)
            latency = (datetime.now(timezone.utc) - start_t).total_seconds()
            final_answer = trace_obj.final_answer
            trace = asdict(trace_obj)
            eval_res = evaluate_single_record(
                item=item,
                final_answer=final_answer,
                trace=trace,
                client=llm_client,
                requests_path=requests_path,
            )
            eval_res["mode"] = mode
            eval_res["latency_sec"] = round(latency, 2)
            results.append(eval_res)
            if log_fp:
                trace_entry = {
                    "id": q_id,
                    "mode": mode,
                    "question": question,
                    "final_answer": final_answer,
                    "trace": trace,
                    "metrics": eval_res,
                }
                log_fp.write(json.dumps(trace_entry, ensure_ascii=False) + "\n")
                log_fp.flush()
    finally:
        if log_fp:
            log_fp.close()
    return results


async def async_main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["dense", "hybrid", "both"], default=os.getenv("RETRIEVAL_MODE", "dense"))
    parser.add_argument("--testset", type=Path, default=Path("tests/testset.jsonl"))
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    settings = load_settings()
    testset_path = args.testset
    if not testset_path.exists():
        testset_path = settings.project_root / "tests" / "testset.jsonl"
    items = load_testset(testset_path)
    if not items:
        sys.exit(1)
    if args.limit and args.limit > 0:
        items = items[:args.limit]

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = settings.project_root / "results"
    logs_dir = settings.project_root / "logs"
    results_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    llm_client = LLMJudgeHelper(settings)
    dense_results = None
    hybrid_results = None

    if args.mode in ("dense", "both"):
        dense_results = await run_benchmark_for_mode(
            items=items,
            mode="dense",
            llm_client=llm_client,
            requests_path=settings.requests_path,
            log_file=logs_dir / f"run_dense_{ts}.jsonl",
        )
        print_summary(dense_results, mode_name="dense")
        write_csv(dense_results, results_dir / f"eval_dense_{ts}.csv")

    if args.mode in ("hybrid", "both"):
        hybrid_results = await run_benchmark_for_mode(
            items=items,
            mode="hybrid",
            llm_client=llm_client,
            requests_path=settings.requests_path,
            log_file=logs_dir / f"run_hybrid_{ts}.jsonl",
        )
        print_summary(hybrid_results, mode_name="hybrid")
        write_csv(hybrid_results, results_dir / f"eval_hybrid_{ts}.csv")

    chart_path = results_dir / "benchmark_dense_vs_hybrid.png"
    if args.mode == "both":
        plot_comparison_chart(dense_results, hybrid_results, chart_path)
        write_csv(dense_results + hybrid_results, results_dir / f"eval_{ts}.csv")
        write_csv(dense_results + hybrid_results, results_dir / "eval_latest.csv")
    else:
        primary_results = dense_results or hybrid_results
        plot_comparison_chart(primary_results, None, chart_path)
        write_csv(primary_results, results_dir / f"eval_{ts}.csv")
        write_csv(primary_results, results_dir / "eval_latest.csv")


def main():
    asyncio.run(async_main())


if __name__ == "__main__":
    main()
