# AGENTS.md — Session Handoff Notes

This file is for AI agents picking up this project mid-stream.
Read this before touching any code. It will save you from re-learning lessons
that have already been learned the hard way.

---

## What This Project Is

A Python + Playwright program that acts like a scheduled TV channel.
It opens a Chromium browser, navigates to video URLs on a timed schedule,
and plays them fullscreen — like a real TV.

**Stack:** Python, Playwright (Chromium), schedule.json config, no web framework.

---

## File Map

| File | Purpose |
|---|---|
| `main.py` | Production scheduler — reads the clock, plays the right show |
| `test.py` | Dev tool — loads shows immediately, NEXT button to trigger transitions |
| `services.py` | Per-service handlers (YouTube, Netflix stubs) + shared helpers |
| `schedule.json` | The TV lineup — edit this to change what plays and when |
| `manual.md` | End-user documentation |
| `browser_profile/` | Chromium persistent profile — **do not read, do not commit** |

---

## What Is Working

- **Schedule-based playback** — `main.py` reads the clock, loads the right show,
  checks every 10 seconds for transitions. Works correctly.
- **YouTube playback** — navigates to URL, clicks play if needed, runs smoothly.
- **OS-level fullscreen** — `--start-fullscreen` Chromium flag keeps the browser
  fullscreen reliably.
- **Persistent login session** — `browser_profile/` stores Chromium cookies so
  YouTube login survives between runs.
- **NEXT button (JS global polling)** — the button sets `window.__90sTVNextClicked = true`
  and Python polls it via `page.evaluate()` every second. Confirmed working.
- **Show looping in test mode** — test.py correctly loops from the last show back
  to the first using `(index + 1) % len(schedule)`.
- **Autoplay through transitions** — videos auto-start after each navigation. Confirmed.
- **Audio through transitions** — audio carries through correctly. Confirmed.
- **YouTube fullscreen through transitions** — `go_fullscreen()` correctly re-enters
  YouTube's internal fullscreen after each navigation. Confirmed.

---

## Known Issues & Hard-Won Lessons

### 1. YouTube's internal fullscreen ('f' key) breaks injected UI

When YouTube enters fullscreen via the browser's Fullscreen API (`element.requestFullscreen()`),
it creates a separate stacking context. Any element we inject into `document.body`
is hidden behind it, regardless of z-index.

**Workarounds tried:**
- Injecting into `document.fullscreenElement` — partially works but click events
  are swallowed by YouTube's overlay layers
- `fullscreenchange` event listener to move the button in — timing is unreliable
- `page.add_init_script` black overlay with `fullscreenchange` listener to auto-move
  the div inside the fullscreen element — the overlay does NOT persist through navigation
  reliably enough; user still briefly sees the YouTube page during transitions

**Current state (test.py):** YouTube fullscreen IS active and working through transitions.
The NEXT button is injected into `document.fullscreenElement` and is clickable.
The black overlay during transitions does not fully hide the YouTube UI — the user
briefly sees the YouTube page between navigation and fullscreen activating.

**Next step:** Hide the YouTube UI (address bar area, recommended videos, etc.) during
the loading phase so the user sees only black then video, never the YouTube page.
Options to explore:
- CSS injection to hide YouTube UI elements during load
- `add_init_script` that hides everything except `#movie_player` until ready
- Waiting longer before removing the overlay (but this already happens)

### 2. Opening a new browser tab breaks OS fullscreen

Chrome exits OS-level fullscreen whenever a new tab opens, even if the tab is
opened programmatically via Playwright. There is no flag or API to suppress this.

**Implication:** The two-tab preloading approach (open background tab to preload,
seamlessly swap) is not viable without the user seeing the transition.

**What we tried:**
- Two tabs with `bring_to_front()` — fullscreen exits on new tab creation
- `--kiosk` flag instead of `--start-fullscreen` — not tested yet, worth trying
- Two separate Playwright instances (visible + headless) — headless doesn't share
  cache with visible browser, so doesn't actually help preload

**Current approach:** Single tab, navigate in place, black overlay hides the load.
User sees a brief black screen (channel change feel) then new show plays.

**Suggested next step:** Try `--kiosk` flag. In kiosk mode, there is no tab bar UI.
Tab creation might not break fullscreen the same way. Worth a test.

### 3. expose_function callbacks unreliable when main thread sleeps

`page.expose_function(name, callback)` registers a Python function that JS can call.
We tried using this for the NEXT button: JS calls `window.__90sTVNext()` → Python callback fires.

It did not work reliably. The button click changed the button text (so onclick fired),
but the Python callback was never invoked. Likely cause: Playwright's sync API may
not dispatch expose_function callbacks while the main thread is blocked in `time.sleep()`.

**Solution:** Abandoned expose_function. Instead, the button sets a JS global
(`window.__90sTVNextClicked = true`) and Python polls it with `page.evaluate()` every second.
This is simple and works.

### 4. F11 cannot be sent via Playwright keyboard

`page.keyboard.press("F11")` sends the key to the page's JavaScript context, not to the
browser as a system event. F11 is browser-level, so it gets ignored.
Use `--start-fullscreen` as a launch arg instead.

---

## Preloading — The Unsolved Problem

The goal is: next show loads silently in the background while the current show plays,
so the transition is instant (no loading screen).

The challenge: any approach that involves a second visible browser tab or window
causes the OS fullscreen to exit.

**Options not yet tried:**
- `--kiosk` flag — might handle tab creation differently
- Two separate OS windows (Playwright doesn't expose window z-order/focus APIs on Windows)
- Injecting a YouTube embed (iframe) for preloading (but Netflix/Disney block iframes)
- Using the filler/ads content as the "loading" buffer — show filler while next main show loads

**Filler content idea (discussed with user):**
The plan is to add "filler" (short clips, like ads) between main shows.
This could be the natural solution to preloading:
  1. Current show ends
  2. Filler content plays (a short clip, maybe 30-60 seconds)
  3. During filler, the next main show navigates and loads in the same tab
  4. Main show starts seamlessly after filler finishes
This is how real TV works — commercials are the preload buffer.

---

## Coding Style (Very Important)

**Write like you're explaining to a junior engineer at 3am.**
- Full descriptive variable names, no abbreviations
- Comments explain WHY, not WHAT
- Simple over clever — 10 obvious lines beats 3 magic ones
- No premature abstractions
- Flat structure, small named functions

---

## Next Priorities (as of last session)

1. **Hide YouTube UI during transitions** — user briefly sees the YouTube page (recommended
   videos, search bar etc.) between navigation and fullscreen activating. Fix this so the
   transition is black screen → video only, never the YouTube page. CSS injection via
   `add_init_script` is the most promising approach.
2. **Filler/ads content** — add short filler clips between main shows. This doubles as the
   preloading buffer: filler plays while the next main show loads, then cuts seamlessly.
3. Figure out if `--kiosk` mode solves the background tab fullscreen problem (untested).
4. Add Netflix, Disney+, Stan handlers to `services.py` once we have test URLs.
