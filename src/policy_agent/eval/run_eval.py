"""Chay danh gia toan bo tap testset tren he thong (make eval / tasks.ps1 eval).

Ho tro ca 2 che do: Dense (Cosine) va Hybrid (BM25 + Cosine) de lay +1 diem cong.
Xuat file log ra logs/run_<mode>_<timestamp>.jsonl va ket qua ra results/.
Nguoi phu trach: SV C (Khang).
"""

import argparse
import json
import logging
import os
import sys
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
    """Helper goi LLM voi temperature=0 cho khau danh gia LLM-as-judge (Tuan 5)."""

    def __init__(self, settings=None):
        self.settings = settings or load_settings()
        self.usage = Usage()

    def ask(self, prompt: str, temperature: float = 0.0) -> str:
        messages = [{"role": "user", "content": prompt}]
        return call_llm(messages, self.settings, self.usage)



def load_testset(path: Path) -> list[dict]:
    """Doc file testset.jsonl."""
    if not path.exists():
        logger.error("Khong tim thay file testset: %s", path)
        return []
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                records.append(json.loads(line))
    return records


import asyncio
from dataclasses import asdict

async def run_benchmark_for_mode(
    items: list[dict],
    mode: str,
    llm_client: LLMJudgeHelper | None = None,
    requests_path: Path | None = None,
    log_file: Path | None = None,
) -> list[dict]:
    """Chay toan bo tap cau hoi voi 1 che do truy van cu the."""
    os.environ["RETRIEVAL_MODE"] = mode
    logger.info("Bat dau danh gia che do: %s voi %d cau hoi", mode.upper(), len(items))

    results = []
    log_fp = None
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        log_fp = open(log_file, "w", encoding="utf-8")

    try:
        for idx, item in enumerate(items, 1):
            q_id = item.get("id", f"Q{idx:02d}")
            question = item.get("question", "")
            logger.info("[%d/%d] Dang chay cau %s: %s", idx, len(items), q_id, question[:50])

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

            # Ghi vao file log jsonl
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
    parser = argparse.ArgumentParser(description="Chay danh gia he thong RAG & Agent")
    parser.add_argument(
        "--mode",
        choices=["dense", "hybrid", "both"],
        default=os.getenv("RETRIEVAL_MODE", "dense"),
        help="Che do truy van (dense, hybrid hoac ca 2 de so sanh)",
    )
    parser.add_argument(
        "--testset",
        type=Path,
        default=Path("tests/testset.jsonl"),
        help="Duong dan toi file testset.jsonl",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Gioi han so cau hoi can chay thu nghiem",
    )
    args = parser.parse_args()

    settings = load_settings()
    testset_path = args.testset
    if not testset_path.exists():
        # Thu tim tu thu muc goc
        testset_path = settings.project_root / "tests" / "testset.jsonl"

    items = load_testset(testset_path)
    if not items:
        print(f"Loi: Khong doc duoc cau hoi nao tu {testset_path}")
        sys.exit(1)

    if args.limit and args.limit > 0:
        items = items[: args.limit]

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = settings.project_root / "results"
    logs_dir = settings.project_root / "logs"
    results_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    llm_client = LLMJudgeHelper(settings)

    dense_results = None
    hybrid_results = None

    if args.mode in ("dense", "both"):
        dense_log = logs_dir / f"run_dense_{ts}.jsonl"
        dense_results = await run_benchmark_for_mode(
            items=items,
            mode="dense",
            llm_client=llm_client,
            requests_path=settings.requests_path,
            log_file=dense_log,
        )
        print_summary(dense_results, mode_name="dense")
        write_csv(dense_results, results_dir / f"eval_dense_{ts}.csv")

    if args.mode in ("hybrid", "both"):
        hybrid_log = logs_dir / f"run_hybrid_{ts}.jsonl"
        hybrid_results = await run_benchmark_for_mode(
            items=items,
            mode="hybrid",
            llm_client=llm_client,
            requests_path=settings.requests_path,
            log_file=hybrid_log,
        )
        print_summary(hybrid_results, mode_name="hybrid")
        write_csv(hybrid_results, results_dir / f"eval_hybrid_{ts}.csv")

    # Xuat bieu do tong hop hoac so sanh
    chart_path = results_dir / "benchmark_dense_vs_hybrid.png"
    if args.mode == "both":
        plot_comparison_chart(dense_results, hybrid_results, chart_path)
        # Ghi file csv gop chung
        write_csv(dense_results + hybrid_results, results_dir / f"eval_{ts}.csv")
        write_csv(dense_results + hybrid_results, results_dir / "eval_latest.csv")
    else:
        primary_results = dense_results or hybrid_results
        plot_comparison_chart(primary_results, None, chart_path)
        write_csv(primary_results, results_dir / f"eval_{ts}.csv")
        write_csv(primary_results, results_dir / "eval_latest.csv")

    print(f"\n=> Da luu ket qua danh gia vao thu muc: {results_dir}")
    print(f"=> Da luu file log chi tiet vao: {logs_dir}\n")


def main():
    asyncio.run(async_main())



if __name__ == "__main__":
    main()
