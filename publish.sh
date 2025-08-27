#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./publish.sh           # upload na PyPI
#   ./publish.sh --test    # upload na TestPyPI

REPO_URL="https://upload.pypi.org/legacy/"
if [[ "${1:-}" == "--test" ]]; then
  REPO_URL="https://test.pypi.org/legacy/"
  echo "→ Používám TestPyPI: $REPO_URL"
else
  echo "→ Používám PyPI: $REPO_URL"
fi

# Kontrola pyproject.toml
if [[ ! -f "pyproject.toml" ]]; then
  echo "❌ Nenalezen pyproject.toml v aktuálním adresáři."
  exit 1
fi

# Doporučené: mít připravené přihlašovací údaje
export TWINE_USERNAME="__token__"
export TWINE_PASSWORD="pypi-REDACTED"
if [[ -z "${TWINE_USERNAME:-}" || -z "${TWINE_PASSWORD:-}" ]]; then
  echo "⚠️  TWINE_USERNAME/TWINE_PASSWORD nejsou nastavené."
  echo "    Buď je nastav (doporučeno), nebo tě Twine vyzve k zadání."
fi

echo "→ Čistím staré artefakty…"
rm -rf dist/ build/ ./**.egg-info

echo "→ Aktualizuji nástroje…"
python3 -m pip install -U pip build setuptools wheel twine >/dev/null

echo "→ Build sdist + wheel…"
python3 -m build

echo "→ Kontrola METADATA…"
python3 - <<'PY'
import glob, zipfile, sys
wheels = glob.glob("dist/*.whl")
if not wheels:
    print("❌ Nebyl vytvořen žádný .whl")
    sys.exit(1)
w = sorted(wheels)[-1]
with zipfile.ZipFile(w) as z:
    meta = [n for n in z.namelist() if n.endswith("METADATA")][0]
    data = z.read(meta).decode("utf-8", errors="replace")
    lines = [l for l in data.splitlines() if l.startswith(("Name:", "Version:", "License", "Dynamic:"))]
    print("\n".join(lines))
    if any(l.lower().startswith("dynamic: license-file") for l in lines):
        print("❌ Detekováno 'Dynamic: license-file' v METADATA – upload selže na PyPI.")
        sys.exit(2)
PY

echo "→ Twine check…"
python3 -m twine check dist/*

echo "→ Upload…"
python3 -m twine upload --repository-url "$REPO_URL" --skip-existing dist/*

echo "✅ Hotovo."
