#!/usr/bin/env python3
"""Check the export without invoking typing, accounts, uploads or other helpers."""
import ast
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SECRET_PATTERNS = [
    re.compile(rb"gh[pousr]_[A-Za-z0-9]{30,}"),
    re.compile(rb"github_pat_[A-Za-z0-9_]{30,}"),
    re.compile(rb"sk-(?:proj-)?[A-Za-z0-9_-]{30,}"),
    re.compile(rb"AIza[A-Za-z0-9_-]{30,}"),
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(rb"\b\d{8,12}:[A-Za-z0-9_-]{30,}\b"),
]


def main():
    errors = []
    inventory = json.loads((ROOT / "inventory.json").read_text())
    config = json.loads((ROOT / "config/classroom.json").read_text())
    assert config["screenshots"]["attach_to_classroom"] is False
    assert config["submission"]["explicit_user_authorization_required"] is True
    assert config["preserve_questions"] is True
    count = {"files": 0, "python": 0, "json": 0, "skills": 0}
    for p in sorted(ROOT.rglob("*")):
        if not p.is_file() or any(x in p.relative_to(ROOT).parts for x in [".git", "__pycache__", "state", "work"]):
            continue
        rel = str(p.relative_to(ROOT))
        content = p.read_bytes()
        count["files"] += 1
        if p.name == "SKILL.md": count["skills"] += 1
        if any(pattern.search(content) for pattern in SECRET_PATTERNS):
            errors.append(rel + ": possible secret; inspect locally without printing values")
        if p.name == ".env" or p.suffix in [".sqlite", ".db", ".pem", ".key"]:
            errors.append(rel + ": forbidden private file type")
        if p.suffix == ".py":
            ast.parse(content, filename=rel)
            count["python"] += 1
        if p.suffix == ".json":
            json.loads(content)
            count["json"] += 1
        if p.name.startswith("LICENSE") and b"Extract these materials from the Services" in content:
            errors.append(rel + ": restricted export license")
    for entry in inventory["files"]:
        p = ROOT / entry["path"]
        if not p.is_file(): errors.append(entry["path"] + ": missing exported file")
        elif hashlib.sha256(p.read_bytes()).hexdigest() != entry["export_sha256"]:
            errors.append(entry["path"] + ": export hash mismatch")
    for entry in inventory["skills"]:
        if not (ROOT / "skills" / entry["name"] / "SKILL.md").is_file():
            errors.append(entry["name"] + ": skill entry point missing")
    for rel in inventory["project_files"]:
        if not (ROOT / rel).is_file():
            errors.append(rel + ": project file missing")
    subject_index = ROOT / config["subject_guides"]["index"]
    if subject_index.is_file():
        links = set(re.findall(r"\]\(([-a-z]+\.md)\)", subject_index.read_text(encoding="utf-8")))
        guides = {p.name for p in subject_index.parent.glob("*.md") if p != subject_index}
        if links != guides:
            errors.append("docs/subjects: index links do not match guide files")
    else:
        errors.append("docs/subjects: subject index missing")
    print(json.dumps({"ok": not errors, "counts": count, "errors": errors}, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
