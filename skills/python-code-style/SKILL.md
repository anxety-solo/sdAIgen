---
name: python-code-style
description: Custom Python code formatting style used by this user. Apply whenever writing, generating, editing, or reformatting Python code for this user — scripts, functions, classes, refactors, code review. Covers a one-line module docstring (`""" Name | by ANXETY """`), blank-line spacing between functions/methods, compact function bodies with blank lines only at real logic shifts, `# ~~ SECTION ~~` markers with nested `# --- Sub-section ---`, single vs double quotes (f-strings/docstrings/HTML exception), naming caught exceptions `exc` not `e`, no period on single-line docstrings, opt-in type annotations with a defaulted-argument mapping (concrete defaults drop annotation, `None` default keeps type and drops `| None`; 3.10+ syntax), import ordering (bare then from-imports, `as`-aliases in their own sub-group, by descending length; `# === PROJECT NAME ===` before local imports), aligning variables/dicts/lists into columns, and a trailing blank line at EOF. Use instead of PEP 8 defaults, even unprompted.
---

# Python Code Style

This skill encodes one user's personal Python style conventions. They differ from PEP 8 in specific, deliberate ways — apply them by default any time you write or edit Python code for this user, not just when they explicitly ask for formatting.

## 1. Module docstring

Every `.py` file starts with a one-line docstring at the very top of the file — before imports, before anything else — in this exact form:

```python
""" <Name Case> | by ANXETY """
```

- `<Name Case>` is a short Title Case name describing what the file does.
- `ANXETY` is the fixed author name and is always written in uppercase.
- It's allowed to expand into a multi-line docstring when the file is large or its functionality is complex enough that one line doesn't cover it — in that case give a brief multi-line description, still opening with the `<Name Case> | by ANXETY` line.

```python
""" Test Module Name | by ANXETY """
```

## 2. Blank lines between functions

- Top-level functions: **2 blank lines** between them (same as PEP 8).
- Methods inside a class: **1 blank line** between them.

```python
def load_config():
    ...


def save_config():
    ...


class Manager:
    def start(self):
        ...

    def stop(self):
        ...
```

## 3. Compact, readable functions

Write functions tight and lean — no filler blank lines, no padding just to spread code out. But compactness never trumps readability: put a blank line inside a function exactly where the logic actually shifts (setup done and now validating, validation done and now computing, right before a `return` that closes out a distinct block) — not as a reflex between every couple of lines, and not omitted just to save lines when it would actually help someone follow the logic.

```python
def process_order(order):
    validate(order)
    total = calculate_total(order)

    if total > order.limit:
        raise ValueError('Order exceeds limit')

    return total
```

Here the blank lines mark the two real shifts — setup into the limit check, and the check into the return — everything else stays packed together.

## 4. Section markers

Mark logical sections of a file with a comment in this exact form:

```python
# ~~ SECTION NAME ~~
```

Spacing is asymmetric on purpose: **2 blank lines above** the marker (same spacing as between top-level functions, so it reads as a clear break from whatever came before), but only **1 blank line below** it, so the marker sits close to the code it labels and it's obvious which block it belongs to.

```python
# ~~ CONFIG ~~

def load_config():
    ...


def save_config():
    ...


# ~~ HELPERS ~~

def normalize(value):
    ...
```

**Nested sub-sections:** when a section is large and contains several distinct smaller pieces of logic, break it up further with a lighter marker:

```python
# --- Sub-section Name ---
```

These nested markers get **1 blank line above and 1 blank line below** — both sides equal, unlike the top-level `# ~~ SECTION ~~` marker's asymmetric spacing. This keeps them visually smaller/lighter than a top-level section, since they're a subdivision of it rather than a new section in their own right.

```python
# ~~ VALIDATION ~~

# --- Type checks ---

def check_str(value):
    ...


def check_int(value):
    ...

# --- Range checks ---

def check_min(value, minimum):
    ...


def check_max(value, maximum):
    ...
```

**Inside a class:** if a `# ~~ SECTION ~~` or `# --- Sub-section ---` marker is the very **first** thing in a class body — right after the `class ...:` line, before any method — skip the blank line(s) above it. There's nothing preceding it inside the class to separate from, so the leading blank lines would just be empty space at the top of the class.

```python
class Manager:
    # ~~ LIFECYCLE ~~

    def start(self):
        ...

    def stop(self):
        ...
```

## 5. Quotes

- Default: **single quotes** (`'...'`) everywhere — strings, dict keys, imports, etc.
- Exception: **docstrings** and **f-strings** use **double quotes** (`"""..."""` / `f"..."`).
- Exception to the exception: if an f-string contains HTML markup (whose tags/attributes use double quotes, e.g. `f'<div class="box">'`), use **single quotes** for that f-string so the HTML's own double quotes don't need escaping.

```python
name = 'worker'
config = {'path': 'settings.json'}

def greet(user: str) -> str:
    """Return a greeting for the user"""
    return f"Hello, {user}!"

def render_row(label, value):
    return f'<div class="row"><span>{label}</span>: {value}</div>'
```

## 6. Exception variable naming

Name a caught exception `exc`, never `e` or any other single-letter name.

```python
try:
    load_config()
except FileNotFoundError as exc:
    print(f"Config file missing: {exc}")
```

## 7. Single-line docstrings

A single-line docstring inside a function does **not** end with a period.

```python
def get_path():
    """Return the resolved project path"""
    return PROJECT_PATH
```

(Multi-line docstrings aren't covered by this rule — use normal judgment/punctuation for those.)

## 8. Type annotations

**Opt-in only:** by default, do **not** add type annotations to functions. Write plain, unannotated signatures unless the user explicitly asks for type annotations (in that request, or as a standing instruction for the conversation/project).

When annotations are requested, follow these rules:

- Every function gets type annotations for its arguments and for its return value.
- Exception: an argument with a **concrete-value default** (a literal like `True`, `512`, `'x'`) is **not** annotated — the literal already makes the type obvious, so the annotation is dropped entirely.
- Special case: an argument whose default is **`None`** and whose type would otherwise be written `type | None` keeps its annotation, but the `| None` is dropped — write `param: type = None`, not `param: type | None = None` and not `param=None`. The base type still isn't obvious from `None` alone, so it stays; the `| None` is redundant once you can see the default is `None`.
- Exception: if a function just performs an action and doesn't return a value (no `return`, or a bare `return` used only to exit early), **omit the return annotation entirely** — don't write it.
- Never write `-> None:` explicitly. It's the one case where "no annotation" and "explicit `None` annotation" would look different, but this style always omits it — a function with no return annotation is understood to return nothing.
- Write annotations using modern Python 3.10+ syntax: built-in generics (`list[int]`, `dict[str, int]`, `tuple[str, ...]`) instead of `typing.List`/`typing.Dict`/`typing.Tuple`, and `X | None` / `X | Y` instead of `Optional[X]` / `Union[X, Y]`. Don't import from `typing` for things the built-ins and `|` now cover.

Mapping for defaulted arguments:

```
param: bool = True        → param=True          # concrete value -> annotation dropped
param: int = 512          → param=512            # concrete value -> annotation dropped
param: str = 'x'          → param='x'            # concrete value -> annotation dropped
param: type | None = None → param: type = None   # None default -> type kept, '| None' dropped
```

```python
def add(a: int, b: int) -> int:
    return a + b

def configure(enabled=True, retries=512, name='x'):
    # all three defaults are concrete values -> no annotations
    ...

def find_handler(handler: Callable = None):
    # default is None -> base type kept, '| None' dropped
    ...

def find_user(user_id: int) -> dict[str, str] | None:
    ...

def log_event(message: str, level=1):
    print(f"[{level}] {message}")
```

## 9. Import order within a group

Within the standard-library / third-party import block of a script:

1. All bare `import x` statements first.
2. Then all `from x import y` statements.
3. Within each of those two groups, sort by **descending line length** (longest line first).
4. Within each of those two groups, `as`-aliased imports (`import x as y` / `from x import y as z`) form their own sub-group **below** the plain (non-aliased) imports of that same group — separated by a blank line — and are themselves sorted by descending line length. A short aliased import still goes below a longer plain import, because it belongs to the aliased sub-group, not the plain one.

```python
import json
import os

from collections import defaultdict
from pathlib import Path
```

Example with aliased imports (the `as` sub-group sits below the plain `import` lines, in its own descending-length order — note `ipywidgets` outranks `gradio` there even though `os`/`time` above are shorter still, because they belong to different sub-groups):

```python
import time
import os

import ipywidgets as widgets
import gradio as gr

from IPython.display import HTML, display
```

## 10. Project-local imports

After the standard-library/third-party import block, add project-local imports as their own group, following the same ordering rule as #9 (bare imports first, then from-imports, each sorted by descending length, `as`-aliases in their own sub-group below). Precede this group with a section marker naming the project, in uppercase:

```python
# === PROJECT NAME ===
```

Full example combining #9 and #10 (the project name below is just a stand-in — always use the actual current project's name, uppercased, not this literal string):

```python
import json
import os

from collections import defaultdict
from pathlib import Path

# === PROJECT NAME ===
import project.utils

from project.config import settings
from project.paths import BASE_PATH
```

(Only **1 blank line** between the main import block and the `# === PROJECT NAME ===` marker — that's different from the 2-blank-line spacing section markers normally get elsewhere in the file, because this marker is directly continuing the imports, not starting a new code section.)

## 11. Align variables, dicts, and lists

Where it's reasonable to do so, align the `=` signs (or `:` in dicts) of related consecutive assignments so they form a neat column. Group related constants together (blank line between unrelated groups) and pad names/keys with spaces so the values line up. (Names/paths below are just an example shape to imitate, not fixed values.)

```python
HOME_PATH     = Path.home()
PROJECT_PATH  = HOME_PATH / 'myapp'
SETTINGS_PATH = PROJECT_PATH / 'settings.json'
VENV_PATH     = HOME_PATH / 'venv'

SCRIPTS_PATH = PROJECT_PATH / 'scripts'
ASSETS_PATH  = PROJECT_PATH / 'assets'

os.environ.update({
    'home_path':     str(HOME_PATH),
    'project_path':  str(PROJECT_PATH),
    'settings_path': str(SETTINGS_PATH),
    'venv_path':     str(VENV_PATH),
})
```

This applies to dict literals and lists of related values too — line them up in columns whenever the values are short and the alignment doesn't hurt readability (don't force alignment on structures with very long or highly variable-length keys/values, where it would just create huge gaps).

**Exception — only 2 items in the group:** if a group has exactly **2** names/keys to align, and aligning them would require padding of **5 or more spaces** on the shorter one, skip alignment entirely and just use a single space around `=` or `:`. With only two lines, a big gap reads as wasted space rather than a clean column — alignment earns its keep with 3+ lines, or with 2 lines where the gap is small. (This exception is specific to pairs — a group of 3+ items always gets aligned regardless of gap size.)

```python
# small gap on a pair -> still align
self.width  = width
self.height = height

# big gap on a pair (7 spaces) -> leave unaligned
self.retries = retries
self.max_connection_pool_size = pool_size

# same exception applies to dicts: big gap on a 2-key dict -> unaligned
LIMITS = {
    'id': 1,
    'maximum_upload_size_bytes': 104857600,
}

# and to tuples/lists: small, even gap on a pair -> still align
SMALL_ICON = (16, 16)
LARGE_ICON = (256, 256)
```

## 12. Trailing blank line

Every script ends with a single blank line — i.e. the file's last line is empty (the file content ends with a newline character after the last line of code, so there's exactly one blank line before EOF, not zero and not several).

## Applying this in practice

When writing or editing a Python file for this user:
- Assume a modern-Python target (3.10+) throughout — use current syntax and stdlib features, don't write code that supports older Python versions.
- Start the file with the module docstring (rule 1).
- Run through rules 2–7 as you write each function/class/docstring/string literal (rule 8's annotations only if the user has asked for them) — keep function bodies compact per rule 3, and name caught exceptions `exc` per rule 6.
- Build the import block per rules 9–10 before writing the rest of the file.
- After a first pass, do one alignment pass (rule 11) over constant blocks, dicts, and lists.
- Make sure the file ends with exactly one trailing blank line (rule 12).
- If editing existing code that violates these rules, bring the parts you touch into line with this style rather than matching the surrounding non-conforming code.
