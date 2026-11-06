#!/usr/bin/env python3
"""Mechanical outcomes that need no judge: decided from the response alone, identically for every model.

  zero   (score 0, never sent to the judge)
    inference_failure  the run recorded an error (token cap, timeout, unclosed thinking, ...) or no text
    exact_echo         the source returned untranslated: equal after NFKC, whitespace and speaker-tag removal
  flags  (recorded only; the Sol score is unchanged; see docs/method.md "Output compliance")
    commentary         an alternative, note or "literally" gloss appended to the translation
    format             speaker labels rewritten as Name: / **Name:**, or markdown emphasis

Partial echoes and kept Japanese terms are left to the judge: the echo test is deliberately exact.

  contract (hard slice: the line fails whatever the judge said; raw check verdicts are kept)
    leaked_scaffold    a prompt section header returned as text ([Source Text], [Background Information], Translation:)
    source_echo        the Japanese line returned beside its translation
    extra_lines        more speaker turns than the source line holds: translated history or invented continuation
  Ordinary wrapping, a speaker label on its own line and label-style differences are not violations.
"""
from __future__ import annotations

import re
import unicodedata

SPEAKER = re.compile(r'【[^】]*】|\[[^\]]{1,20}\]')
COMMENTARY_LINE = re.compile(
    # "or" only in its alternative-offering forms: "Or," "(or)" "Or more literally" "Or, depending..." -- not
    # "(Or maybe it was my imagination.)", which can be a translation (JMB-234 気のせいだろうか)
    r'^\s*[(\[*_]*\s*(?:or\s*[,:)]|or\s+(?:more|in a|depending|perhaps more|alternatively|simply)\b|'
    r'(?:alternatively|alternatives?(?: translations?| versions?| options?)?|another option|more literally|literally|'
    r'literal translation|notes?|translation note|translator.?s note|explanation)\b)',
    re.I)
COMMENTARY_INLINE = re.compile(r'\((?:lit\.|literally|or:)[^)]*\)', re.I)
MARKDOWN = re.compile(r'\*\*[^*\n]+\*\*|(?<![*\w])\*[^*\n]+\*(?![*\w])')
NAME_LABEL = re.compile(r'^\s*\**[A-Z][\w .\'-]{0,24}\**\s*[:：]', re.M)


SCAFFOLD_WORDS = r'(?:source(?: text)?|background(?: information)?|context|history|original(?: text)?|japanese|translation|english)'
SCAFFOLD_LINE = re.compile(r'^\s*[\[(（【]?\s*' + SCAFFOLD_WORDS + r'\s*[:：]?\s*[\])）】]?\s*[:：]?\s*$', re.I)
SCAFFOLD_LABEL = re.compile(r'^\s*(?:[\[(（【]\s*' + SCAFFOLD_WORDS + r'\s*[\])）】]|' + SCAFFOLD_WORDS + r'\s*[:：])', re.I)
TURN_LABEL = re.compile(r'^\s*(?:\[[^\]]{1,40}\]|\**[A-Z][\w .\'-]{0,24}\**\s*[:：]\s*["“「])')
BRACKET_NAME = re.compile(r'【[^】]{1,30}】')
JP_BODY = re.compile(r'^\s*【[^】]*】\s*|[「」『』]')


def _norm(s: str) -> str:
    return re.sub(r'\s+', '', SPEAKER.sub('', unicodedata.normalize('NFKC', s or '')))


def zero_reason(source: str, translation: str | None, error: str | None) -> str | None:
    if error or not (translation or '').strip():
        return 'inference_failure'
    if _norm(translation) and _norm(translation) == _norm(source):
        return 'exact_echo'
    return None


def flags(source: str, translation: str) -> list[str]:
    out = []
    lines = [l for l in translation.splitlines() if l.strip()]
    if any(COMMENTARY_LINE.match(l) for l in lines[1:]) or COMMENTARY_INLINE.search(translation):
        out.append('commentary')
    if MARKDOWN.search(translation) or ('【' in source and '【' not in translation and NAME_LABEL.search(translation)):
        out.append('format')
    return out


def contract_violation(source: str, translation: str) -> str | None:
    """Screen-output contract for one delivered line (hard slice). None when the reply is a clean single turn."""
    lines = [l for l in (translation or '').splitlines() if l.strip()]
    if any(SCAFFOLD_LINE.match(l) or SCAFFOLD_LABEL.match(l) for l in lines):
        return 'leaked_scaffold'
    body = _norm(JP_BODY.sub('', source))
    if len(body) >= 4 and body in _norm(translation):
        return 'source_echo'
    turns = sum(len(BRACKET_NAME.findall(l)) + (0 if l.lstrip().startswith('【') else bool(TURN_LABEL.match(l))) for l in lines)
    if turns > max(1, len(BRACKET_NAME.findall(source))):
        return 'extra_lines'
    return None
