"""Module xuat bao cao ket qua danh gia (CSV + bieu do).

Dung de sinh file ket qua results/eval_<timestamp>.csv va bieu do results/benchmark_dense_vs_hybrid.png.
Nguoi phu trach: SV C (Khang).
"""

import csv
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def write_csv(records: list[dict], output_path: Path):
    """Ghi danh sach ket qua danh gia ra file CSV."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fields = [
        "id",
        "type",
        "question",
        "passed",
        "faithfulness",
        "citation_hit",
        "refusal_correct",
        "action_success",
        "prompt_tokens",
        "completion_tokens",
        "total_tokens",
        "llm_calls",
        "refusal_reason",
        "final_answer",
    ]

    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for r in records:
            writer.writerow(r)

    logger.info("Da xuat bao cao CSV: %s", output_path)


def print_summary(records: list[dict], mode_name: str = "dense"):
    """In bang tong hop ket qua ra console."""
    if not records:
        print("Khong co du lieu danh gia de in bao cao.")
        return

    total = len(records)
    passed = sum(1 for r in records if r.get("passed"))
    avg_faith = sum(r.get("faithfulness", 0.0) for r in records) / total
    avg_cite = sum(r.get("citation_hit", 0.0) for r in records) / total
    refusal_ok = sum(1 for r in records if r.get("refusal_correct")) / total
    action_items = [r for r in records if r.get("type") == "action"]
    action_ok = (sum(1 for r in action_items if r.get("action_success")) / len(action_items)) if action_items else 1.0
    total_tokens = sum(r.get("total_tokens", 0) for r in records)

    print("\n" + "=" * 65)
    print(f"       KET QUA DANH GIA HE THONG (Che do: {mode_name.upper()})")
    print("=" * 65)
    print(f"Tong so cau hoi danh gia : {total}")
    print(f"So cau vuot qua (Passed) : {passed}/{total} ({passed/total*100:.1f}%)")
    print(f"Faithfulness trung binh  : {avg_faith:.4f}")
    print(f"Citation Hit trung binh  : {avg_cite:.4f}")
    print(f"Ti le tu choi dung       : {refusal_ok*100:.1f}%")
    print(f"Ti le hanh dong hop le   : {action_ok*100:.1f}%")
    print(f"Tong luong Token su dung : {total_tokens:,} tokens")
    print("-" * 65)
    print(f"{'ID':<6} | {'Loai':<16} | {'Passed':<6} | {'Faith':<6} | {'Cite':<6} | {'Tokens':<6}")
    print("-" * 65)
    for r in records:
        p_str = "PASS" if r.get("passed") else "FAIL"
        print(f"{r.get('id'):<6} | {r.get('type')[:16]:<16} | {p_str:<6} | {r.get('faithfulness', 0):.2f}   | {r.get('citation_hit', 0):.2f}   | {r.get('total_tokens', 0):<6}")
    print("=" * 65 + "\n")


def plot_comparison_chart(
    dense_records: list[dict],
    hybrid_records: list[dict] | None,
    output_image_path: Path,
):
    """Ve bieu do so sanh (Dense vs Hybrid) bang Matplotlib de them vao bao cao (+1 diem cong)."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        logger.warning("matplotlib chua duoc cai dat, bo qua ve bieu do.")
        return

    output_image_path = Path(output_image_path)
    output_image_path.parent.mkdir(parents=True, exist_ok=True)

    # Tinh toan cac chi so tong hop
    def calc_stats(records):
        if not records:
            return 0, 0, 0, 0, 0
        n = len(records)
        pass_rate = (sum(1 for r in records if r.get("passed")) / n) * 100
        avg_faith = (sum(r.get("faithfulness", 0.0) for r in records) / n) * 100
        avg_cite = (sum(r.get("citation_hit", 0.0) for r in records) / n) * 100
        avg_refusal = (sum(1 for r in records if r.get("refusal_correct")) / n) * 100
        avg_tokens = sum(r.get("total_tokens", 0) for r in records) / n
        return pass_rate, avg_faith, avg_cite, avg_refusal, avg_tokens

    d_pass, d_faith, d_cite, d_refusal, d_tok = calc_stats(dense_records)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    metrics_names = ["Pass Rate (%)", "Faithfulness (%)", "Citation Hit (%)", "Refusal Acc (%)"]
    dense_scores = [d_pass, d_faith, d_cite, d_refusal]

    if hybrid_records:
        h_pass, h_faith, h_cite, h_refusal, h_tok = calc_stats(hybrid_records)
        hybrid_scores = [h_pass, h_faith, h_cite, h_refusal]

        # Bieu do cot so sanh 4 chi so
        import numpy as np
        x = np.arange(len(metrics_names))
        width = 0.35

        axes[0].bar(x - width / 2, dense_scores, width, label="Dense (Cosine)", color="#2b5c8f")
        axes[0].bar(x + width / 2, hybrid_scores, width, label="Hybrid (BM25+Dense)", color="#e07a5f")
        axes[0].set_ylabel("Ty le (%)")
        axes[0].set_title("So sanh Chat luong: Dense vs Hybrid")
        axes[0].set_xticks(x)
        axes[0].set_xticklabels(metrics_names, rotation=15)
        axes[0].set_ylim(0, 110)
        axes[0].legend()
        axes[0].grid(axis="y", linestyle="--", alpha=0.5)

        # Bieu do cot so sanh Token trung binh
        token_modes = ["Dense", "Hybrid"]
        token_vals = [d_tok, h_tok]
        bars = axes[1].bar(token_modes, token_vals, color=["#2b5c8f", "#e07a5f"], width=0.4)
        axes[1].set_ylabel("So Token trung binh / cau")
        axes[1].set_title("Chi phi Token: Dense vs Hybrid")
        axes[1].grid(axis="y", linestyle="--", alpha=0.5)
        for bar in bars:
            yval = bar.get_height()
            axes[1].text(bar.get_x() + bar.get_width() / 2, yval + 10, f"{int(yval)}", ha="center", va="bottom")
    else:
        # Bieu do don neu chi co 1 che do
        axes[0].bar(metrics_names, dense_scores, color="#2b5c8f", width=0.4)
        axes[0].set_ylabel("Ty le (%)")
        axes[0].set_title("Ket qua Danh gia He thong (Dense)")
        axes[0].set_ylim(0, 110)
        axes[0].grid(axis="y", linestyle="--", alpha=0.5)

        axes[1].bar(["Dense"], [d_tok], color="#2b5c8f", width=0.3)
        axes[1].set_ylabel("Token trung binh / cau")
        axes[1].set_title("Chi phi Token trung binh")
        axes[1].grid(axis="y", linestyle="--", alpha=0.5)

    plt.tight_layout()
    plt.savefig(output_image_path, dpi=200)
    plt.close()
    logger.info("Da luu bieu do danh gia: %s", output_image_path)
