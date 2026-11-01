"""Check the interface strings without opening a window.

Three things go wrong silently and this catches all of them:

* a visible string that never reaches ``t()``, so Spanish shows English;
* a tooltip key the code asks for that no catalogue defines, which shows no
  help at all rather than raising;
* a key present in one catalogue and missing from the other.

It parses the source instead of importing it, so it needs no display and no
third-party package.

    python tools/check_strings.py
"""
import ast
import pathlib
import sys

SRC = pathlib.Path(__file__).resolve().parent.parent / "src"

# Where Tk shows a string to the user.
VISIBLE_KEYWORDS = {"text", "title", "message", "label"}
TRANSLATORS = {"t", "tooltip"}
# Punctuation and placeholders carry no words to translate. '100%' is replaced
# the moment its variable is read, and 'name'/'pages'/'size' are column ids.
IGNORE_VALUES = {"...", "", "%", "-", "+", "/", "100%", "end", "☕"}


def dict_keys(path, name, problems):
    """The keys of a module-level dict literal, reporting any repeated one."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) \
                and node.targets[0].id == name and isinstance(node.value, ast.Dict):
            keys = [k.value for k in node.value.keys if isinstance(k, ast.Constant)]
            seen = set()
            for key in keys:
                if key in seen:
                    problems.append(f"{path.name}: {name} repite la clave {key!r}")
                seen.add(key)
            return seen
    problems.append(f"{path.name}: no encuentro el diccionario {name}")
    return set()


def untranslated(path):
    """Visible string literals in this module that no translator wraps."""
    found = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if not isinstance(node, ast.Call):
            continue
        for keyword in node.keywords:
            value = keyword.value
            if keyword.arg in VISIBLE_KEYWORDS and isinstance(value, ast.Constant) \
                    and isinstance(value.value, str) and value.value not in IGNORE_VALUES \
                    and any(c.isalpha() for c in value.value):
                found.append((value.lineno, f"{keyword.arg}={value.value!r}"))
        name = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
        if name == "Tooltip":
            for arg in node.args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str) \
                        and arg.value not in IGNORE_VALUES:
                    found.append((arg.lineno, f"Tooltip({arg.value!r})"))
    return found


def tooltip_keys_used(path):
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "tooltip" \
                and node.args and isinstance(node.args[0], ast.Constant):
            yield node.lineno, node.args[0].value


def main():
    problems = []
    spanish = dict_keys(SRC / "i18n.py", "SPANISH", problems)
    english_tips = dict_keys(SRC / "tooltips.py", "TOOLTIP_TEXT", problems)
    spanish_tips = dict_keys(SRC / "tooltips.py", "TOOLTIP_TEXT_ES", problems)

    for key in sorted(english_tips - spanish_tips):
        problems.append(f"tooltips.py: {key!r} no está traducido al español")
    for key in sorted(spanish_tips - english_tips):
        problems.append(f"tooltips.py: {key!r} sólo existe en español")

    for path in sorted(SRC.glob("*.py")):
        if path.name in {"i18n.py", "tooltips.py"}:
            continue
        for line, what in sorted(untranslated(path)):
            problems.append(f"{path.name}:{line}: texto visible sin traducir: {what}")
        for line, key in tooltip_keys_used(path):
            if key not in english_tips:
                problems.append(f"{path.name}:{line}: tooltip({key!r}) no está en el catálogo")

    print(f"i18n: {len(spanish)} cadenas · ayudas: {len(english_tips)} en / {len(spanish_tips)} es")
    if problems:
        for line in problems:
            print(" -", line)
        print(f"\nFALLOS: {len(problems)}")
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
