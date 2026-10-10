"""Side-effect store for procedure requests: data/state/requests.json.

Owner: SV C.
TODO:
- [ ] create(request) -> request_id (validate request_type against DOC0102)
- [ ] get(request_id) -> record | None
- [ ] atomic write (temp file + replace)
"""
