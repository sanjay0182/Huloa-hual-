import os
import random
import time

from playwright.sync_api import sync_playwright

URL = os.environ["APP_URL"]
WAIT_SECONDS = int(os.environ.get("WAIT_MINUTES", "0") or 0) * 60

VISIT_SECONDS = 45 * 60            # visiting window per run
GAP_MIN, GAP_MAX = 80, 480         # 1m20s .. 8m between visits
RETRY_GAP = 60                     # if a visit fails, retry after 1 min
NEW_BROWSER_EVERY = (12 * 60, 20 * 60)

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


def visit(browser):
    w, h = random.choice(VIEWPORTS)
    ctx = browser.new_context(
        viewport={"width": w, "height": h},
        user_agent=random.choice(USER_AGENTS),
        locale=random.choice(["en-US", "en-GB", "en-IN"]),
    )
    ok = False
    try:
        page = ctx.new_page()
        resp = page.goto(URL, wait_until="load", timeout=60000)  # wake-up can take ~10-30s
        status = resp.status if resp else None
        log(f"visit status={status}")
        ok = status is not None and status < 500
        act_like_person(page, w, h)
    except Exception as e:
        log(f"visit failed: {e}")
    finally:
        ctx.close()
    return ok


def main():
    if WAIT_SECONDS:
        log(f"waiting {WAIT_SECONDS // 60} min before visiting")
        time.sleep(WAIT_SECONDS)

    start = time.time()
    with sync_playwright() as p:
        while time.time() - start < VISIT_SECONDS:
            browser = p.chromium.launch()
            browser_until = time.time() + random.randint(*NEW_BROWSER_EVERY)
            while time.time() < browser_until and time.time() - start < VISIT_SECONDS:
                ok = visit(browser)
                gap = random.randint(GAP_MIN, GAP_MAX) if ok else RETRY_GAP
                remaining = VISIT_SECONDS - (time.time() - start)
                if remaining <= 0:
                    break
                time.sleep(min(gap, remaining))
            browser.close()
    log("visiting window finished")


if __name__ == "__main__":
    main()
