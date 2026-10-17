import json
import sys
import time
from dataclasses import asdict
from pathlib import Path


def stream_print(text: str, delay: float = 0.015, flush: bool = True) -> None:
    for char in text:
        sys.stdout.write(char)
        if flush:
            sys.stdout.flush()
        if delay > 0:
            time.sleep(delay)
    sys.stdout.write("\n")
    if flush:
        sys.stdout.flush()


def save_trace(run, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [{"event": "START", "timestamp": run.timestamp, "question": run.question}]
    for number, step in enumerate(run.steps, start=1):
        rows.append({"event": "STEP", "step": number, **asdict(step)})
    rows.append({
        "event": "FINAL",
        "final_answer": run.final_answer,
        "cited_doc_ids": run.cited_doc_ids,
    })
    rows.append({"event": "USAGE", **asdict(run.usage)})
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return path

