import urllib.request
import sys

routes = [
  "/",
  "/dashboard",
  "/zen",
  "/storyboard",
  "/pipelines",
  "/timeline",
  "/brainstorm",
  "/research",
  "/translation",
  "/schemas",
  "/preview",
  "/auth/callback",
  "/timeline-test"
]

all_passed = True
for r in routes:
    url = f"http://localhost:3000{r}"
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            body = response.read().decode('utf-8', errors='ignore')
            if "Application error: a client-side exception has occurred" in body:
                print(f"[FAIL] {r} - Client-side exception")
                all_passed = False
            else:
                print(f"[OK] {r} (200)")
    except Exception as e:
        print(f"[FAIL] {r} Exception: {e}")
        all_passed = False

if not all_passed:
    sys.exit(1)
