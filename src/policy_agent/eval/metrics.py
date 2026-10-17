import json
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

REFUSAL_KEYWORDS = [
    "không tìm thấy",
    "không có thông tin",
    "không có quy định",
    "không được đề cập",
    "từ chối",
    "không thể",
    "thiếu thông tin",
    "chưa đủ thông tin",
    "cần cung cấp thêm",
    "khong tim thay",
    "khong co thong tin",
    "khong co quy dinh",
    "khong duoc de cap",
    "tu choi",
    "khong the",
    "thieu thong tin",
    "chua du thong tin",
    "can cung cap them",
    "no relevant",
    "cannot find",
    "not found",
    "out of scope",
    "fake: no relevant passages",
]


def _load_prompt(filename: str) -> str:
    base_dir = Path(__file__).resolve().parents[2]
    p1 = base_dir / "prompts" / filename
    if p1.exists():
        return p1.read_text(encoding="utf-8").strip()
    p2 = base_dir.parent.parent / "prompts" / filename
    if p2.exists():
        return p2.read_text(encoding="utf-8").strip()
    return ""


def decompose_claims(answer: str, client=None) -> list[str]:
    if not answer or not answer.strip():
        return []
    prompt_template = _load_prompt("judge_decompose.txt")
    if client is not None and prompt_template:
        try:
            text = client.ask(prompt_template.format(answer=answer), temperature=0.0)
            claims = []
            for line in text.splitlines():
                cleaned = line.strip("-•* \t")
                if cleaned and not cleaned.lower().startswith("here are"):
                    claims.append(cleaned)
            if claims:
                return claims
        except Exception as e:
            logger.warning("decompose_claims fallback: %s", e)
    raw_parts = re.split(r"[.\n;]+", answer)
    claims = []
    for part in raw_parts:
        cleaned = part.strip("-* \t")
        if len(cleaned) > 10:
            claims.append(cleaned)
    return claims or [answer.strip()]


def judge_claim(claim: str, context: str, client=None) -> bool:
    if not claim or not context:
        return False
    prompt_template = _load_prompt("judge_claim.txt")
    if client is not None and prompt_template:
        try:
            verdict = client.ask(prompt_template.format(context=context, claim=claim), temperature=0.0)
            return verdict.strip().upper().startswith("YES")
        except Exception as e:
            logger.warning("judge_claim fallback: %s", e)
    stopwords = {"nhan", "vien", "duoc", "theo", "quy", "dinh", "la", "co", "trong", "va", "cua", "cac", "mot"}
    words = []
    for w in re.findall(r"\w+", claim):
        if len(w) > 2 and w.lower() not in stopwords:
            words.append(w.lower())
    if not words:
        return True
    match_count = 0
    ctx_lower = context.lower()
    for w in words:
        if w in ctx_lower:
            match_count += 1
    return (match_count / len(words)) >= 0.6


def check_faithfulness(answer: str, context: str | list, client=None) -> tuple[float, list[dict]]:
    if isinstance(context, list):
        parts = []
        for c in context:
            parts.append(str(c))
        context_text = "\n\n".join(parts)
    else:
        context_text = str(context)
    claims = decompose_claims(answer, client=client)
    if not claims:
        return 0.0, []
    results = []
    supported_count = 0
    for claim in claims:
        ok = judge_claim(claim, context_text, client=client)
        if ok:
            supported_count += 1
        results.append({"claim": claim, "supported": ok})
    score = supported_count / len(claims)
    return round(score, 4), results


def check_refusal(answer: str, expect_refusal: bool) -> tuple[bool, str]:
    lower_ans = answer.lower()
    refused = False
    for kw in REFUSAL_KEYWORDS:
        if kw in lower_ans:
            refused = True
            break
    if expect_refusal:
        if refused:
            return True, "Tu choi dung"
        return False, "Ky vong tu choi nhung he thong van tra loi"
    else:
        if refused:
            return False, "Cau hoi hop le nhung bi tu choi"
        return True, "Tra loi hop le"


def check_citation_hit(answer: str, expected_doc_ids: list[str]) -> float:
    if not expected_doc_ids:
        return 1.0
    hit_count = 0
    for doc_id in expected_doc_ids:
        pattern = r"\b" + re.escape(doc_id) + r"\b"
        if re.search(pattern, answer, re.IGNORECASE):
            hit_count += 1
    return round(hit_count / len(expected_doc_ids), 4)


def check_action_success(trace_steps: list[dict], requests_path: Path | None = None) -> bool:
    created_id = None
    verified_id = None
    for step in trace_steps:
        action = step.get("action", "")
        args = step.get("args", {})
        obs = step.get("observation", "")
        if action == "create_request":
            match = re.search(r"REQ-[a-f0-9]+", obs)
            if match:
                created_id = match.group(0)
        elif action == "get_request":
            req_id_arg = args.get("request_id", "")
            if created_id and req_id_arg == created_id:
                verified_id = req_id_arg
    if not created_id or not verified_id:
        return False
    if requests_path is not None and Path(requests_path).exists():
        try:
            data = json.loads(Path(requests_path).read_text(encoding="utf-8"))
            for row in data:
                if row.get("request_id") == created_id:
                    return True
            return False
        except Exception:
            return False
    return True


def evaluate_single_record(
    item: dict,
    final_answer: str,
    trace: dict,
    context_chunks: list[str] | None = None,
    client=None,
    requests_path: Path | None = None,
) -> dict:
    expect_refusal = item.get("expect_refusal", False)
    expect_write = item.get("expect_write", False)
    expected_doc_ids = item.get("expected_doc_ids", [])
    refusal_correct, refusal_reason = check_refusal(final_answer, expect_refusal)
    citation_score = check_citation_hit(final_answer, expected_doc_ids)
    steps = trace.get("steps", [])
    action_ok = True
    if expect_write:
        action_ok = check_action_success(steps, requests_path=requests_path)
    faithfulness = 1.0
    if not expect_refusal:
        ctx = context_chunks or []
        if not ctx:
            for s in steps:
                if s.get("action") == "search_policy":
                    ctx.append(s.get("observation", ""))
        faithfulness, _ = check_faithfulness(final_answer, ctx, client=client)
    usage = trace.get("usage", {})
    prompt_tokens = usage.get("prompt_tokens", 0)
    completion_tokens = usage.get("completion_tokens", 0)
    total_tokens = prompt_tokens + completion_tokens
    llm_calls = usage.get("calls", 0)
    passed = refusal_correct and (citation_score >= 0.5 or not expected_doc_ids) and action_ok
    if not expect_refusal:
        passed = passed and (faithfulness >= 0.6)
    return {
        "id": item.get("id", ""),
        "type": item.get("type", ""),
        "question": item.get("question", ""),
        "passed": passed,
        "faithfulness": faithfulness,
        "citation_hit": citation_score,
        "refusal_correct": refusal_correct,
        "refusal_reason": refusal_reason,
        "action_success": action_ok,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "llm_calls": llm_calls,
        "final_answer": final_answer,
    }
