---
name: text
description: Create or edit Russian-language text for social posts, Telegram, and Classroom. Use for clear, factual writing and targeted removal of AI-sounding filler; preserve the appropriate genre and voice.
---

# Text: clear human writing

Use this skill for drafting, revising, or auditing Russian-language posts and
Classroom answers. Preserve facts, names, quotations, links, dates, and the
author's intended point. Never invent examples, sources, personal experience,
or certainty to make text sound stronger.

## Choose the mode

### Social posts and Telegram

Write from verified source material. Match the requested audience and tone,
keep the useful call to action, deadline, and link if present, and remove
generic claims, false authority, canned contrasts, and filler. For a finished
Russian draft that needs a dedicated anti-slop pass, read and apply
`../humanizer-ru/SKILL.md`. Make edits selectively: a
single word is not evidence of a pattern, and intentional humour, quotations,
or a distinct authorial voice must remain.

### Classroom

Prioritize factual accuracy, direct answers, understandable wording, and the
student's level. Use the language specified by the assignment. Do not turn
academic answers into promotional or conversational copy, and do not apply
mechanical anti-slop bans that conflict with the genre. Explain only what the
question requires and mark uncertainty instead of guessing.

When filling a worksheet or shared Classroom document, place each answer
directly below its question. Do not add a separate heading such as
`Відповіді` unless the assignment or user requests one. Write centuries with
Roman numerals, for example `XXI століття`. Do not use the em dash (`—`). Avoid
other dash punctuation when a plain sentence works; keep hyphens required by
spelling, names, and numeric notation.

### Audit without rewriting

List specific passages that sound generic, bureaucratic, or falsely
authoritative, explain the concern, and offer concise alternatives. Do not
claim that prose was written by AI; style signals are not proof of authorship.

## Delivery and typing

Return the clean final text first, followed by a short change note only when it
helps. Do not publish, submit, comment, or edit a shared document unless the
user explicitly asks. For keyboard emulation, use `$print` only after the user
identifies the destination and confirms the exact text immediately before it is
typed. `$print` does not submit a form.

## Optional English technical check

Slopometer is an optional check for English technical documentation, not a
default or a Russian-language validator. Use it only when the user explicitly
requests that check and the tool is installed; do not install dependencies or
download its language model automatically.
