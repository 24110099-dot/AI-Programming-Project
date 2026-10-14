"""Write structured run events as UTF-8 JSONL."""
import json
from dataclasses import asdict
from pathlib import Path


def save_trace(run, path):
    """Return the created trace path; serialization errors are not hidden."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [{"event": "START", "timestamp": run.timestamp, "question": run.question}]
    rows.extend({"event": "STEP", "step": number, **asdict(step)} for number, step in enumerate(run.steps, 1))
    rows.append({"event": "FINAL", "final_answer": run.final_answer, "cited_doc_ids": run.cited_doc_ids})
    rows.append({"event": "USAGE", **asdict(run.usage)})
    with path.open("x", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")
    return path
