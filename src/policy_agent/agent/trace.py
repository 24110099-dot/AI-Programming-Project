import json
from dataclasses import asdict
from pathlib import Path


def save_trace(run, path):
    # Lưu nhật ký từng bước thực thi của Agent ra file JSONL
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    rows = [
        {"event": "START", "timestamp": run.timestamp, "question": run.question}
    ]
    for number, step in enumerate(run.steps, start=1):
        rows.append({"event": "STEP", "step": number, **asdict(step)})

    rows.append({
        "event": "FINAL",
        "final_answer": run.final_answer,
        "cited_doc_ids": run.cited_doc_ids,
    })
    rows.append({"event": "USAGE", **asdict(run.usage)})

    with path.open("x", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")

    return path
