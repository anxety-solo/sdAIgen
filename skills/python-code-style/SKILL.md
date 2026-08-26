---
name: python-code-style
description: Personal Python code formatting style belonging to a specific user (author tag "ANXETY" by default). Apply this style ONLY when the user explicitly asks for it — e.g. "format this in my style", "use my Python style", "apply ANXETY style", or an earlier standing instruction in the conversation to always use it. Do NOT apply it by default to ordinary Python requests. Once invoked, it governs: an optional one-line module docstring naming an author (default "ANXETY", override if the user names someone else), blank-line spacing between functions/methods, compact function bodies with blank lines only at real logic shifts, `# ~~ SECTION ~~` markers with nested `# --- Sub-section ---`, single vs double quotes (with an f-string/docstring/HTML exception), naming caught exceptions `exc` not `e`, no period on single-line docstrings, opt-in type annotations with a defaulted-argument mapping, import ordering (bare then from-imports, `as`-aliases in their own sub-group, sorted by descending length, plus a `# === PROJECT NAME ===` marker for local imports), aligning variables/dicts/lists into columns, and a trailing blank line at EOF.
---

# Python Code Style (ANXETY)

This skill encodes one user's personal Python style conventions. It differs from plain PEP 8 in specific, deliberate ways.

**This is opt-in, not a default.** Only apply these rules when the user explicitly asks for their personal/custom style — by name ("ANXETY style", "my style") or by clear standing instruction earlier in the conversation ("always format my Python like this from now on"). For ordinary Python requests with no such signal, write normal idiomatic Python and ignore this skill entirely.

## 1. Module docstring (on by default, but skippable)

Every `.py` file starts with a one-line docstring at the very top of the file — before imports, before anything else — in this exact form:

```python
""" <Name Case> | by <Author> """
```

- `<Name Case>` is not just a filename label — it's a short, Title Case description of the script's **core purpose and logic**: what the file is actually for. Think "what would I tell someone this file does in five words", not "what would I name this file".
- If a file serves more than one distinct purpose (e.g. it bundles a couple of related components, or handles a main task plus a clearly secondary one), name the main parts, separated by `&` or `:` as fits naturally.
- `<Author>` defaults to **ANXETY**, written in uppercase. If the user tells you to credit a different name or handle, use that instead — it replaces ANXETY, it doesn't get appended to it.
- This docstring is added **by default** whenever this skill is active. If the user says they don't want a header docstring (for this file, or in general), skip it — don't argue for it.
- It's fine to expand into a multi-line docstring when the file is large or complex enough that one line doesn't cover it — still open with the `<Name Case> | by <Author>` line.

```python
""" Image Resizer | by ANXETY """
```

```python
""" Main Widgets: Settings Hub & GDrive Panel | by ANXETY """
```

## 2. Blank lines between functions

- Top-level functions: **2 blank lines** between them (same as PEP 8).
- Methods inside a class: **1 blank line** between them.

```python
def enqueue_task(task):
    ...


def dequeue_task():
    ...


class TaskQueue:
    def push(self, task):
        ...

    def pop(self):
        ...
```

## 3. Compact, readable functions

Write functions tight and lean — no filler blank lines, no padding just to spread code out. But compactness never trumps readability: put a blank line inside a function exactly where the logic actually shifts (setup done and now validating, validation done and now computing, right before a `return` that closes out a distinct block) — not as a reflex between every couple of lines, and not omitted just to save lines when it would actually help someone follow the logic.

```python
def fetch_with_retry(url, max_attempts):
    attempts = 0
    last_error = None

    while attempts < max_attempts:
        try:
            return send_request(url)
        except ConnectionError as exc:
            last_error = exc
            attempts += 1

    raise last_error
```

Here the blank lines mark the two real shifts — setup into the retry loop, and the loop into the final raise — everything else stays packed together.

## 4. Section markers

Mark logical sections of a file with a comment in this exact form:

```python
# ~~ SECTION NAME ~~
```

Spacing is asymmetric on purpose: **2 blank lines above** the marker (same spacing as between top-level functions, so it reads as a clear break from whatever came before), but only **1 blank line below** it, so the marker sits close to the code it labels and it's obvious which block it belongs to.

```python
# ~~ COMMANDS ~~

def run_build():
    ...


def run_deploy():
    ...


# ~~ HELPERS ~~

def parse_flags(argv):
    ...
```

**Nested sub-sections:** when a section is large and contains several distinct smaller pieces of logic, break it up further with a lighter marker:

```python
# --- Sub-section Name ---
```

Each word in the sub-section name is capitalized (Title Case), same as the top-level marker — e.g. `# --- API Tokens ---`.

These nested markers get **1 blank line above and 1 blank line below** — both sides equal, unlike the top-level `# ~~ SECTION ~~` marker's asymmetric spacing. This keeps them visually smaller/lighter than a top-level section, since they're a subdivision of it rather than a new section in their own right.

```python
# ~~ FORM VALIDATION ~~

# --- Field Checks ---

def check_email(value):
    ...


def check_phone(value):
    ...

# --- Cross-Field Checks ---

def check_passwords_match(pw1, pw2):
    ...


def check_dates_in_order(start, end):
    ...
```

**Inside a class:** if a `# ~~ SECTION ~~` or `# --- Sub-section ---` marker is the very **first** thing in a class body — right after the `class ...:` line, before any method — skip the blank line(s) above it. There's nothing preceding it inside the class to separate from, so the leading blank lines would just be empty space at the top of the class.

```python
class NotificationSender:
    # ~~ LIFECYCLE ~~

    def connect(self):
        ...

    def disconnect(self):
        ...
```

## 5. Quotes

- Default: **single quotes** (`'...'`) everywhere — strings, dict keys, imports, etc.
- Exception: **docstrings** and **f-strings** use **double quotes** (`"""..."""` / `f"..."`).
- Exception to the exception: if an f-string contains HTML markup (whose tags/attributes use double quotes, e.g. `f'<div class="alert">'`), use **single quotes** for that f-string so the HTML's own double quotes don't need escaping.

```python
status = 'idle'
headers = {'content-type': 'application/json'}

def build_summary(name: str) -> str:
    """Return a short status summary for the given worker"""
    return f"Worker {name} is currently active"

def render_alert_row(message, level):
    return f'<tr class="alert-{level}"><td>{message}</td></tr>'
```

## 6. Exception variable naming

Name a caught exception `exc`, never `e` or any other single-letter name.

```python
try:
    connection = open_database()
except TimeoutError as exc:
    log.warning(f"Database connection timed out: {exc}")
```

## 7. Single-line docstrings

A single-line docstring inside a function does **not** end with a period.

```python
def get_cache_dir():
    """Return the path to the local cache directory"""
    return CACHE_DIR
```

(Multi-line docstrings aren't covered by this rule — use normal judgment/punctuation for those.)

## 8. Type annotations

**Opt-in only:** by default, do **not** add type annotations to functions. Write plain, unannotated signatures unless the user explicitly asks for type annotations (in that request, or as a standing instruction for the conversation/project).

When annotations are requested, follow these rules:

- Every function gets type annotations for its arguments and for its return value.
- Exception: an argument with a **concrete-value default** (a literal like `True`, `30`, `'utf-8'`) is **not** annotated — the literal already makes the type obvious, so the annotation is dropped entirely.
- Special case: an argument whose default is **`None`** and whose type would otherwise be written `type | None` keeps its annotation, but the `| None` is dropped — write `param: type = None`, not `param: type | None = None` and not `param=None`. The base type still isn't obvious from `None` alone, so it stays; the `| None` is redundant once you can see the default is `None`.
- Exception: if a function just performs an action and doesn't return a value (no `return`, or a bare `return` used only to exit early), **omit the return annotation entirely** — don't write it.
- Never write `-> None:` explicitly. It's the one case where "no annotation" and "explicit `None` annotation" would look different, but this style always omits it — a function with no return annotation is understood to return nothing.
- Write annotations using modern Python 3.10+ syntax: built-in generics (`list[int]`, `dict[str, int]`, `tuple[str, ...]`) instead of `typing.List`/`typing.Dict`/`typing.Tuple`, and `X | None` / `X | Y` instead of `Optional[X]` / `Union[X, Y]`. Don't import from `typing` for things the built-ins and `|` now cover.

Mapping for defaulted arguments:

```
param: bool = True         → param=True           # concrete value -> annotation dropped
param: int = 30            → param=30              # concrete value -> annotation dropped
param: str = 'utf-8'       → param='utf-8'         # concrete value -> annotation dropped
param: type | None = None  → param: type = None    # None default -> type kept, '| None' dropped
```

```python
def add_items(cart: list[str], item: str) -> list[str]:
    cart.append(item)
    return cart

def open_socket(timeout=30, retries=3, encoding='utf-8'):
    # all three defaults are concrete values -> no annotations
    ...

def find_adapter(adapter: Adapter = None):
    # default is None -> base type kept, '| None' dropped
    ...

def find_record(record_id: int) -> dict[str, str] | None:
    ...

def log_metric(name: str, value=1):
    print(f"[{name}] {value}")
```

## 9. Import order within a group

Within the standard-library / third-party import block of a script:

1. All bare `import x` statements first.
2. Then all `from x import y` statements.
3. Within each of those two groups, sort by **descending line length** (longest line first).
4. Within each of those two groups, `as`-aliased imports (`import x as y` / `from x import y as z`) form their own sub-group **below** the plain (non-aliased) imports of that same group — separated by a blank line — and are themselves sorted by descending line length. A short aliased import still goes below a longer plain import, because it belongs to the aliased sub-group, not the plain one.

```python
import sys
import re

from html.parser import HTMLParser
from urllib.parse import urljoin
```

Example with aliased imports (the `as` sub-group sits below the plain `import` lines, in its own descending-length order — note `element_tree` outranks `numpy` there even though `sys`/`csv` above are shorter still, because they belong to different sub-groups):

```python
import csv
import sys

import xml.etree.ElementTree as element_tree
import numpy as np

from dataclasses import dataclass, field
```

## 10. Project-local imports

After the standard-library/third-party import block, add project-local imports as their own group, following the same ordering rule as #9 (bare imports first, then from-imports, each sorted by descending length, `as`-aliases in their own sub-group below). Precede this group with a section marker naming the project, in uppercase:

```python
# === PROJECT NAME ===
```

Full example combining #9 and #10 (the project name below is just a stand-in — always use the actual current project's name, uppercased, not this literal string):

```python
import json
import time

from collections import defaultdict
from pathlib import Path

# === SCRAPER TOOLKIT ===
import scraper.throttling

from scraper.parsers import extract_links
from scraper.storage import save_page
```

(Only **1 blank line** between the main import block and the `# === PROJECT NAME ===` marker — that's different from the 2-blank-line spacing section markers normally get elsewhere in the file, because this marker is directly continuing the imports, not starting a new code section.)

## 11. Align variables, dicts, and lists

Where it's reasonable to do so, align the `=` signs (or `:` in dicts) of related consecutive assignments so they form a neat column. Group related constants together (blank line between unrelated groups) and pad names/keys with spaces so the values line up. (Names/paths below are just an example shape to imitate, not fixed values.)

```python
DEFAULT_TIMEOUT  = 10
MAX_RETRIES      = 5
BACKOFF_SECONDS  = 2
USER_AGENT       = 'toolkit/1.0'

READ_CHUNK_SIZE  = 8192
WRITE_CHUNK_SIZE = 4096

STATUS_CODES = {
    'ok':      200,
    'created': 201,
    'error':   500,
}
```

This applies to dict literals and lists of related values too — line them up in columns whenever the values are short and the alignment doesn't hurt readability (don't force alignment on structures with very long or highly variable-length keys/values, where it would just create huge gaps).

**Exception — only 2 items in the group:** if a group has exactly **2** names/keys to align, and aligning them would require padding of **5 or more spaces** on the shorter one, skip alignment entirely and just use a single space around `=` or `:`. With only two lines, a big gap reads as wasted space rather than a clean column — alignment earns its keep with 3+ lines, or with 2 lines where the gap is small. (This exception is specific to pairs — a group of 3+ items always gets aligned regardless of gap size.)

```python
# small gap on a pair -> still align
self.host = host
self.port = port

# big gap on a pair (6 spaces) -> leave unaligned
self.enabled = enabled
self.max_concurrent_uploads = max_uploads

# same exception applies to dicts: big gap on a 2-key dict -> unaligned
LIMITS = {
    'id': 1,
    'maximum_requests_per_minute': 120,
}

# and to tuples/lists: small, even gap on a pair -> still align
THUMBNAIL_SIZE = (128, 128)
BANNER_SIZE    = (1024, 256)
```

## 12. Trailing blank line

Every script ends with a single blank line — i.e. the file's last line is empty (the file content ends with a newline character after the last line of code, so there's exactly one blank line before EOF, not zero and not several).

## Applying this in practice

Only follow the steps below once the user has actually invoked this style (see the "opt-in, not a default" note above). When writing or editing a Python file under this style:

- Assume a modern-Python target (3.10+) throughout — use current syntax and stdlib features, don't write code that supports older Python versions.
- Start the file with the module docstring (rule 1), unless the user has said not to.
- Run through rules 2–7 as you write each function/class/docstring/string literal (rule 8's annotations only if the user has asked for them) — keep function bodies compact per rule 3, and name caught exceptions `exc` per rule 6.
- Build the import block per rules 9–10 before writing the rest of the file.
- After a first pass, do one alignment pass (rule 11) over constant blocks, dicts, and lists.
- Make sure the file ends with exactly one trailing blank line (rule 12).
- If editing existing code that violates these rules, bring the parts you touch into line with this style rather than matching the surrounding non-conforming code.
- If the user later asks for plain/idiomatic Python again, drop back to normal conventions — this style stays active only while they want it.
