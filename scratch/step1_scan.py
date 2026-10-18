
from backend.repo import clone, scan

URL = "https://github.com/pallets/flask"

print("[STEP 1] Starting repository clone...")

try:
    path = clone(URL)
    print(f"[SUCCESS] Cloned to: {path}")

    print("[STEP 2] Scanning project files...")
    found = scan(path)
    print("[RESULT] Found files:", found)

except Exception as e:
    print(f"[ERROR] {type(e).__name__}: {e}")
