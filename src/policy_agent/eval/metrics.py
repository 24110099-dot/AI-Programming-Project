"""Module danh gia he thong (Metrics evaluation).

Tuan 5: LLM-as-judge cho Faithfulness (do do tin cay va can cu).
Kiem tra: Citation hit, ti le tu choi (Refusal rate), Action write-verify.
Nguoi phu trach: SV C (Khang).
"""

import json
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

# Tu khoa nhan dien model tu choi tra loi (ca co dau va khong dau)
REFUSAL_KEYWORDS = [
    # Co dau
    "không tìm thấy",
    "không có thông tin",
    "không có quy định",
    "không được đề cập",
    "từ chối",
    "không thể",
    "thiếu thông tin",
    "chưa đủ thông tin",
    "cần cung cấp thêm",
    # Khong dau
    "khong tim thay",
    "khong co thong tin",
    "khong co quy dinh",
    "khong duoc de cap",
    "tu choi",
    "khong the",
    "thieu thong tin",
    "chua du thong tin",
    "can cung cap them",
    # Tieng Anh
    "no relevant",
    "cannot find",
    "not found",
    "out of scope",
    "fake: no relevant passages",
]


def _load_prompt(filename: str) -> str:
    """Doc file prompt tu thu muc prompts hoac src/policy_agent/prompts."""
    base_dir = Path(__file__).resolve().parents[2]  # src/policy_agent
    paths_to_try = [
        base_dir / "prompts" / filename,
        base_dir.parent.parent / "prompts" / filename,
    ]
    for p in paths_to_try:
        if p.exists():
            return p.read_text(encoding="utf-8").strip()
    return ""


def decompose_claims(answer: str, client=None) -> list[str]:
    """Tach cau tra loi thanh cac menh de su that (factual claims).

    Neu co client Groq, goi prompt de tach theo dung bai giang Tuan 5.
    Neu khong co, tach theo dau cau (fallback).
    """
    if not answer or not answer.strip():
        return []

    prompt_template = _load_prompt("judge_decompose.txt")
    if client is not None and prompt_template:
        try:
            full_prompt = prompt_template.format(answer=answer)
            # Dung model gpt-oss hoac llama3 voi temperature=0.0
            resp_text = client.ask(full_prompt, temperature=0.0)
            claims = [
                line.strip("-* \t")
                for line in resp_text.splitlines()
                if line.strip() and not line.lower().startswith("here are")
            ]
            if claims:
                return claims
        except Exception as e:
            logger.warning("Loi goi LLM decompose claims: %s, dung fallback", e)

    # Fallback don gian: tach theo dau cham, xuong dong, dau cham phay
    raw_parts = re.split(r"[.\n;]+", answer)
    claims = []
    for part in raw_parts:
        cleaned = part.strip("-* \t")
        if len(cleaned) > 10:  # Bo qua cac cum tu qua ngan
            claims.append(cleaned)
    return claims or [answer.strip()]


def judge_claim(claim: str, context: str, client=None) -> bool:
    """Kiem tra xem mot menh de co duoc ngu canh ho tro hay khong.

    Dung LLM voi temperature 0.0 (nhu mot cay nhiet ke do chinh xac).
    """
    if not claim or not context:
        return False

    prompt_template = _load_prompt("judge_claim.txt")
    if client is not None and prompt_template:
        try:
            full_prompt = prompt_template.format(context=context, claim=claim)
            verdict = client.ask(full_prompt, temperature=0.0).strip().upper()
            return verdict.startswith("YES")
        except Exception as e:
            logger.warning("Loi goi LLM judge claim: %s, dung fallback", e)

    # Heuristic fallback: dem ti le tu khoa trong claim xuat hien o context (loai bo tu dung pho bien)
    stopwords = {"nhan", "vien", "duoc", "theo", "quy", "dinh", "la", "co", "trong", "va", "cua", "cac", "mot"}
    words = [w.lower() for w in re.findall(r"\w+", claim) if len(w) > 2 and w.lower() not in stopwords]
    if not words:
        words = [w.lower() for w in re.findall(r"\w+", claim) if len(w) > 2]
    if not words:
        return True
    match_count = sum(1 for w in words if w in context.lower())
    return (match_count / len(words)) >= 0.6


def check_faithfulness(answer: str, context: str | list, client=None) -> tuple[float, list[dict]]:
    """Tinh diem Faithfulness = (so menh de dung) / (tong so menh de).

    Tra ve (diem_so [0.0 - 1.0], chi_tiet_tung_claim).
    """
    if isinstance(context, list):
        context_text = "\n\n".join(str(c) for c in context)
    else:
        context_text = str(context)

    claims = decompose_claims(answer, client=client)
    if not claims:
        return 0.0, []

    results = []
    supported_count = 0
    for claim in claims:
        is_supported = judge_claim(claim, context_text, client=client)
        if is_supported:
            supported_count += 1
        results.append({"claim": claim, "supported": is_supported})

    score = supported_count / len(claims)
    return round(score, 4), results


def check_refusal(answer: str, expect_refusal: bool) -> tuple[bool, str]:
    """Kiem tra xem cau tra loi co tu choi dung nhu ky vong hay khong."""
    lower_ans = answer.lower()
    refused = any(kw in lower_ans for kw in REFUSAL_KEYWORDS)

    if expect_refusal:
        if refused:
            return True, "Tu choi dung vi cau hoi nam ngoai quy che / thieu du lieu"
        return False, "Ky vong tu choi nhung he thong van co tra loi"
    else:
        if refused:
            return False, "Cau hoi hop le nhung he thong lai tu choi"
        return True, "Tra loi dung khong bi tu choi sai"


def check_citation_hit(answer: str, expected_doc_ids: list[str]) -> float:
    """Kiem tra xem cau tra loi co trich dan du cac doc_id yeu cau khong.

    Diem so tu 0.0 den 1.0. Neu khong yeu cau trich dan doc_id thi tra ve 1.0.
    """
    if not expected_doc_ids:
        return 1.0

    hit_count = 0
    for doc_id in expected_doc_ids:
        # Tim dang [DOCxxxx] hoac DOCxxxx
        pattern = r"\b" + re.escape(doc_id) + r"\b"
        if re.search(pattern, answer, re.IGNORECASE):
            hit_count += 1

    return round(hit_count / len(expected_doc_ids), 4)


def check_action_success(trace_steps: list[dict], requests_path: Path | None = None) -> bool:
    """Kiem tra hanh dong tao don va verify co day du khong:

    1. Co goi tool create_request va co tra ve request_id hop le.
    2. Co goi tool get_request ngay sau do de verify dung request_id do.
    3. File requests.json thuc su chua ban ghi do.
    """
    created_id = None
    verified_id = None

    for step in trace_steps:
        action = step.get("action", "")
        args = step.get("args", {})
        obs = step.get("observation", "")

        if action == "create_request":
            # Tim request_id tu observation
            match = re.search(r"REQ-[a-f0-9]+", obs)
            if match:
                created_id = match.group(0)

        elif action == "get_request":
            req_id_arg = args.get("request_id", "")
            if created_id and req_id_arg == created_id:
                verified_id = req_id_arg

    # Neu khong co id duoc tao thi coi nhu khong thanh cong
    if not created_id or not verified_id:
        return False

    # Kiem tra file requests.json neu co truyen vao
    if requests_path is not None and Path(requests_path).exists():
        try:
            content = Path(requests_path).read_text(encoding="utf-8")
            data = json.loads(content)
            found = any(row.get("request_id") == created_id for row in data)
            return found
        except Exception as e:
            logger.warning("Loi doc file requests.json: %s", e)
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
    """Tong hop toan bo chi so cho 1 cau hoi."""
    expect_refusal = item.get("expect_refusal", False)
    expect_write = item.get("expect_write", False)
    expected_doc_ids = item.get("expected_doc_ids", [])

    # 1. Refusal Check
    refusal_correct, refusal_reason = check_refusal(final_answer, expect_refusal)

    # 2. Citation Hit
    citation_score = check_citation_hit(final_answer, expected_doc_ids)

    # 3. Action Check
    steps = trace.get("steps", [])
    action_ok = True
    if expect_write:
        action_ok = check_action_success(steps, requests_path=requests_path)

    # 4. Faithfulness (chi danh cho cau hoi khong phai tu choi)
    faithfulness = 1.0
    if not expect_refusal:
        ctx = context_chunks or []
        if not ctx:
            # Lay context tu cac observation cua step search_policy
            ctx = [s.get("observation", "") for s in steps if s.get("action") == "search_policy"]
        faithfulness, _ = check_faithfulness(final_answer, ctx, client=client)

    # 5. Token Usage
    usage = trace.get("usage", {})
    prompt_tokens = usage.get("prompt_tokens", 0)
    completion_tokens = usage.get("completion_tokens", 0)
    total_tokens = prompt_tokens + completion_tokens
    llm_calls = usage.get("calls", 0)

    # Danh gia vuot qua hay khong
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
