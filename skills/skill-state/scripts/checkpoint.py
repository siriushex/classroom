#!/usr/bin/env python3
"""Native Codex task checkpoints. No model calls, tools, shell or auto-retries.

SQLite transactions atomically append full bounded states. Local hash chains detect
accidental corruption, not malicious rewriting by an actor who owns the database.
"""
import argparse
import copy
from contextlib import closing
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import uuid

LIMIT = 8192
LIST_FIELDS = ('decisions', 'completed', 'pending', 'blockers')
FIELDS = {'goal', 'scope', 'criteria', 'phase', 'facts', 'next_step', 'evidence', 'checks', *LIST_FIELDS}
IMMUTABLE = {'goal', 'scope', 'criteria'}
UNSAFE_KEYS = {'__proto__', 'prototype', 'constructor'}


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def hashed(value):
    return hashlib.sha256(encoded(value).encode()).hexdigest()


def decode(text):
    def pairs(items):
        result = {}
        for k, v in items:
            if k in result or k in UNSAFE_KEYS:
                raise ValueError('duplicate or forbidden JSON key')
            result[k] = v
        return result
    def constant(value):
        raise ValueError('non-finite JSON number')
    return json.loads(text, object_pairs_hook=pairs, parse_constant=constant)


def timestamp():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def identity(project, task):
    project = Path(project).resolve(strict=True)
    if not project.is_dir() or not isinstance(task, str) or not task.strip() or len(task) > 200:
        raise ValueError('valid project directory and stable task ID required')
    return str(project), task


def string(value, *, nonempty=False):
    if not isinstance(value, str) or len(value) > 2048 or (nonempty and not value.strip()):
        raise ValueError('expected bounded string')


def strings(value, nonempty=False):
    if not isinstance(value, list) or len(value) > 24 or (nonempty and not value):
        raise ValueError('expected bounded list')
    for item in value:
        string(item, nonempty=True)
    if len(value) != len(set(value)):
        raise ValueError('duplicate list entries')


def validate(state):
    if not isinstance(state, dict) or set(state) != FIELDS:
        raise ValueError('unknown or missing state fields')
    # Reparse to reject unsafe dictionary keys even for direct Python callers.
    data = encoded(state)
    decode(data)
    if len(data.encode()) > LIMIT:
        raise ValueError('state exceeds 8192 bytes; move detail to referenced evidence')
    string(state['goal'], nonempty=True)
    string(state['scope'], nonempty=True)
    string(state['next_step'])
    strings(state['criteria'], nonempty=True)
    if state['phase'] not in ('inspect', 'work', 'verify', 'blocked', 'done'):
        raise ValueError('invalid phase')
    for field in LIST_FIELDS:
        strings(state[field])
    if not isinstance(state['facts'], dict) or len(state['facts']) > 32:
        raise ValueError('facts must be a bounded map')
    for k, v in state['facts'].items():
        string(k, nonempty=True)
        string(v)
    refs = set()
    if not isinstance(state['evidence'], list) or len(state['evidence']) > 24:
        raise ValueError('invalid evidence list')
    for item in state['evidence']:
        if not isinstance(item, dict) or not {'id', 'source', 'observed_at'} <= set(item) or set(item) - {'id', 'source', 'observed_at', 'sha256'}:
            raise ValueError('invalid evidence record')
        for key in ('id', 'source', 'observed_at'):
            string(item[key], nonempty=True)
        try:
            when = dt.datetime.fromisoformat(item['observed_at'].replace('Z', '+00:00'))
            if when.tzinfo is None:
                raise ValueError('timezone required')
        except ValueError as exc:
            raise ValueError('evidence requires timezone-aware ISO timestamp') from exc
        if item['id'] in refs:
            raise ValueError('duplicate evidence ID')
        refs.add(item['id'])
        if 'sha256' in item and (not isinstance(item['sha256'], str) or not re.fullmatch('[a-f0-9]{64}', item['sha256'])):
            raise ValueError('invalid sha256')
    if not isinstance(state['checks'], list) or len(state['checks']) > 24:
        raise ValueError('invalid checks list')
    checked, passed = set(), set()
    for check in state['checks']:
        if not isinstance(check, dict) or set(check) != {'criterion', 'status', 'evidence_ids'}:
            raise ValueError('invalid check record')
        criterion = check['criterion']
        if criterion not in state['criteria'] or criterion in checked:
            raise ValueError('unknown or duplicate criterion')
        checked.add(criterion)
        if check['status'] not in ('passed', 'failed', 'not_run'):
            raise ValueError('invalid check status')
        strings(check['evidence_ids'])
        if not set(check['evidence_ids']) <= refs:
            raise ValueError('unknown evidence reference')
        if check['status'] == 'passed':
            if not check['evidence_ids']:
                raise ValueError('passed check requires evidence')
            passed.add(criterion)
    if state['phase'] == 'done' and (state['pending'] or state['blockers'] or state['next_step'] or passed != set(state['criteria'])):
        raise ValueError('done requires all criteria proved, no pending work or blockers')


def merge(target, patch):
    if not isinstance(patch, dict):
        return copy.deepcopy(patch)
    result = copy.deepcopy(target) if isinstance(target, dict) else {}
    for key, value in patch.items():
        if value is None:
            result.pop(key, None)
        else:
            result[key] = merge(result.get(key), value)
    return result


def initialize(project, task, goal, scope, criteria, root):
    project, task = identity(project, task)
    state = dict(goal=goal, scope=scope, criteria=criteria, phase='inspect', facts={},
                 next_step='Inspect relevant evidence', evidence=[], checks=[],
                 **{k: [] for k in LIST_FIELDS})
    validate(state)
    run_id = uuid.uuid4().hex
    directory = Path(root).expanduser().resolve() / hashed(project)[:16] / (hashed(task)[:12] + '-' + run_id)
    directory.mkdir(parents=True, mode=0o700)
    dbpath = directory / 'state.sqlite3'
    fd = os.open(dbpath, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(fd)
    meta = {'format': 1, 'project': project, 'task_id': task, 'run_id': run_id, 'created_at': timestamp()}
    with closing(sqlite3.connect(dbpath)) as db, db:
        db.execute('PRAGMA synchronous=FULL')
        db.execute('CREATE TABLE metadata (id INTEGER PRIMARY KEY CHECK(id=1), data TEXT NOT NULL)')
        db.execute('CREATE TABLE revisions (revision INTEGER PRIMARY KEY, state TEXT NOT NULL, previous TEXT NOT NULL, hash TEXT NOT NULL, at TEXT NOT NULL)')
        db.execute('INSERT INTO metadata VALUES(1,?)', (encoded(meta),))
        _append(db, 0, state, hashed(meta))
    return directory


def connect(directory, write=False):
    directory = Path(directory).absolute()
    dbpath = directory / 'state.sqlite3'
    if any(p.is_symlink() for p in (directory, *directory.parents)) or dbpath.is_symlink():
        raise ValueError('checkpoint path must not use symlinks; pass a canonical path')
    if not dbpath.is_file():
        raise ValueError('checkpoint database does not exist')
    return sqlite3.connect(dbpath.as_uri() + ('?mode=rw' if write else '?mode=ro'), uri=True, timeout=5)


def _append(db, revision, state, previous):
    at = timestamp()
    entry = {'revision': revision, 'state': state, 'previous': previous, 'at': at}
    digest = hashed(entry)
    db.execute('INSERT INTO revisions VALUES(?,?,?,?,?)', (revision, encoded(state), previous, digest, at))


def _replay(db, project, task):
    project, task = identity(project, task)
    raw = db.execute('SELECT data FROM metadata WHERE id=1').fetchone()
    if not raw:
        raise ValueError('missing checkpoint identity')
    meta = decode(raw[0])
    if not isinstance(meta, dict) or meta.get('format') != 1 or meta.get('project') != project or meta.get('task_id') != task:
        raise ValueError('checkpoint project/task/format mismatch')
    head, count, state, original = hashed(meta), 0, None, None
    for revision, raw_state, previous, digest, at in db.execute('SELECT * FROM revisions ORDER BY revision'):
        state = decode(raw_state)
        validate(state)
        if revision != count or previous != head or hashed({'revision': revision, 'state': state, 'previous': previous, 'at': at}) != digest:
            raise ValueError('checkpoint journal integrity failure')
        if original is None:
            original = {k: state[k] for k in IMMUTABLE}
        if any(state[k] != original[k] for k in IMMUTABLE):
            raise ValueError('immutable task contract changed')
        count, head = count + 1, digest
    if not count:
        raise ValueError('empty checkpoint journal')
    return {'identity': meta, 'revision': count - 1, 'state': state, 'head': head, 'state_bytes': len(encoded(state).encode())}


def load(directory, project, task):
    with closing(connect(directory)) as db, db:
        db.execute('BEGIN')
        return _replay(db, project, task)


def update(directory, project, task, expected_revision, patch):
    if type(expected_revision) is not int or expected_revision < 0:
        raise ValueError('expected revision must be a non-negative integer')
    if not isinstance(patch, dict) or set(patch) - (FIELDS - IMMUTABLE):
        raise ValueError('unknown or immutable patch fields')
    with closing(connect(directory, write=True)) as db, db:
        db.execute('PRAGMA synchronous=FULL')
        db.execute('BEGIN IMMEDIATE')
        current = _replay(db, project, task)
        if current['revision'] != expected_revision:
            raise ValueError('stale revision; read current state and reconcile before retry')
        state = merge(current['state'], patch)
        validate(state)
        if state == current['state']:
            return current
        _append(db, expected_revision + 1, state, current['head'])
        return _replay(db, project, task)


def main():
    parser = argparse.ArgumentParser(description='Native task checkpoints; no commands or model calls')
    subs = parser.add_subparsers(dest='command', required=True)
    init = subs.add_parser('init')
    init.add_argument('--goal', required=True)
    init.add_argument('--scope', required=True)
    init.add_argument('--criterion', action='append', required=True)
    init.add_argument('--root', type=Path, default=Path.home()/'.local/state/skill-state/native')
    for name in ('show', 'verify', 'update'):
        p = subs.add_parser(name)
        p.add_argument('--run', type=Path, required=True)
        if name == 'update':
            p.add_argument('--expected-revision', type=int, required=True)
            p.add_argument('--patch-file', type=Path, required=True)
    for p in [init, *[subs.choices[n] for n in ('show', 'verify', 'update')]]:
        p.add_argument('--project', type=Path, required=True)
        p.add_argument('--task-id', required=True)
    args = parser.parse_args()
    try:
        if args.command == 'init':
            directory = initialize(args.project, args.task_id, args.goal, args.scope, args.criterion, args.root)
            result = {'run': str(directory), **load(directory, args.project, args.task_id)}
        elif args.command == 'update':
            with args.patch_file.open('r', encoding='utf-8') as f:
                raw = f.read(LIMIT * 2 + 1)
            if len(raw.encode()) > LIMIT * 2:
                raise ValueError('patch file too large')
            result = update(args.run, args.project, args.task_id, args.expected_revision, decode(raw))
        else:
            result = load(args.run, args.project, args.task_id)
        if args.command == 'verify':
            result = {k: result[k] for k in ('identity', 'revision', 'head', 'state_bytes')}
        elif args.command == 'update':
            result = {k: result[k] for k in ('revision', 'head', 'state_bytes')}
        print(encoded(result))
    except (OSError, ValueError, TypeError, RecursionError, sqlite3.Error) as exc:
        print(encoded({'error': type(exc).__name__, 'detail': str(exc)[:240]}), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
