import csv
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def write_csv(records: list[dict], output_path: Path):
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


def print_summary(records: list[dict], mode_name: str = "dense"):
    if not records:
        print("Khong co du lieu danh gia.")
        return
    total = len(records)
    passed = 0
    total_faith = 0.0
    total_cite = 0.0
    refusal_count = 0
    total_tokens = 0
    action_items = []
    for r in records:
        if r.get("passed"):
            passed += 1
        total_faith += r.get("faithfulness", 0.0)
        total_cite += r.get("citation_hit", 0.0)
        if r.get("refusal_correct"):
            refusal_count += 1
        total_tokens += r.get("total_tokens", 0)
        if r.get("type") == "action":
            action_items.append(r)
    avg_faith = total_faith / total
    avg_cite = total_cite / total
    refusal_ok = refusal_count / total
    action_ok = 1.0
    if action_items:
        act_pass = 0
        for r in action_items:
            if r.get("action_success"):
                act_pass += 1
        action_ok = act_pass / len(action_items)

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
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        return
    output_image_path = Path(output_image_path)
    output_image_path.parent.mkdir(parents=True, exist_ok=True)

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
        bars = axes[1].bar(["Dense", "Hybrid"], [d_tok, h_tok], color=["#2b5c8f", "#e07a5f"], width=0.4)
        axes[1].set_ylabel("So Token trung binh / cau")
        axes[1].set_title("Chi phi Token: Dense vs Hybrid")
        axes[1].grid(axis="y", linestyle="--", alpha=0.5)
        for bar in bars:
            yval = bar.get_height()
            axes[1].text(bar.get_x() + bar.get_width() / 2, yval + 10, f"{int(yval)}", ha="center", va="bottom")
    else:
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
