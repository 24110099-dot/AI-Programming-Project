"""retrieve(query, mode="dense"|"hybrid", top_k, category=None) -> list[(chunk, score)].

Owner: SV A.
TODO:
- [ ] metadata filter BEFORE scoring (category, latest version only)
- [ ] MIN_SCORE gate -> empty result => no_answer path
"""
