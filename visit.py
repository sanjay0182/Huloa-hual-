import os
import random
import sys
import time

from playwright.sync_api import sync_playwright

# --- check the link FIRST, before any waiting ---
URL = (os.environ.get("APP_URL") or "").strip()
if URL and not URL.startswith(("http://", "https://")):
    URL = "https://" + URL
if not URL:
    print("ERROR: APP_URL is empty. Add it in Settings > Secrets and variables > "
          "Actions (Variables tab, or Secrets tab) with your full app link.", flush=True)
    sys.exit(1)

START_DELAY = random.randint(0, 60)               # small random wait before first visit
VISIT_SECONDS = random.randint(30 * 60, 59 * 60)  # visiting window per run (30-59 min)
GAP_MIN, GAP_MAX = 3 * 60, 15 * 60  # 3 to 15 min between visits (app sleeps after 30 min)
RETRY_GAP = 60                      # if a visit fails, retry after 1 min

VIEWPORTS = [(1366, 768), (1440, 900), (1536, 864), (1280, 720), (1920, 1080)]
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]


def log(msg):
    print(time.strftime("%H:%M:%S"), msg, flush=True)


def act_like_person(page, w, h):
    for _ in range(random.randint(3, 6)):
        page.mouse.move(
            random.randint(40, w - 40),
            random.randint(40, h - 40),
            steps=random.randint(8, 25),
        )
        page.wait_for_timeout(random.randint(300, 1500))
    page.mouse.wheel(0, random.randint(300, 900))
    page.wait_for_timeout(random.randint(800, 2500))
    page.mouse.wheel(0, -random.randint(100, 500))
    page.wait_for_timeout(random.randint(3000, 8000))


def visit(p):
    """Open Chrome, visit once, close Chrome. Returns True if the app answered OK."""
    w, h = random.choice(VIEWPORTS)
    browser = p.chromium.launch()
    ok = False
    try:
        ctx = browser.new_context(
            viewport={"width": w, "height": h},
            user_agent=random.choice(USER_AGENTS),
            locale=random.choice(["en-US", "en-GB", "en-IN"]),
        )
        page = ctx.new_page()
        resp = page.goto(URL, wait_until="load", timeout=60000)  # wake-up can take ~10-30s
        status = resp.status if resp else None
        ok = status is not None and status < 400
        log(f"visit status={status} ok={ok}")
        if not ok:
            try:
                snippet = " ".join(page.inner_text("body").split())[:200]
            except Exception:
                snippet = "(could not read page)"
            log(f"page said: {snippet}")
        act_like_person(page, w, h)
    except Exception as e:
        log(f"visit problem: {e}")
    finally:
        browser.close()
    return ok


def main():
    log(f"url={URL}")
    log(f"start delay {START_DELAY} sec, visiting for {VISIT_SECONDS // 60} min")
    time.sleep(START_DELAY)

    good = bad = 0
    start = time.time()
    with sync_playwright() as p:
        while time.time() - start < VISIT_SECONDS:
            ok = visit(p)
            if ok:
                good += 1
            else:
                bad += 1
            gap = random.randint(GAP_MIN, GAP_MAX) if ok else RETRY_GAP
            remaining = VISIT_SECONDS - (time.time() - start)
            if remaining <= 0:
                break
            time.sleep(min(gap, remaining))  # browser is closed during this wait
    log(f"visiting window finished: {good} ok, {bad} failed")
    if good == 0:
        log("ERROR: not a single visit worked, so this run is marked failed (check the lines above)")
        sys.exit(1)


if __name__ == "__main__":
    main()
