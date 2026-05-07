# 90s TV — User Manual

## What Is This?

90s TV is a program that turns your computer into a TV channel. You define a schedule —
what plays and when — and the program handles the rest. It opens a browser, loads the
right video at the right time, and switches shows automatically.

---

## How to Use It

1. Open `schedule.json` and fill in your lineup (see the Schedule Format section below).
2. Run `python main.py`.
3. The browser will open and start playing whatever is scheduled for the current time.
4. Leave it running. It checks the clock every 30 seconds and switches shows automatically.
5. Press `Ctrl+C` in the terminal to stop.

---

## Schedule Format

The schedule lives in `schedule.json`. It's a list of shows, each with three fields:

```json
[
  {
    "label": "Seinfeld - The Soup",
    "time": "20:00",
    "url": "https://www.youtube.com/watch?v=..."
  },
  {
    "label": "Friends - The One Where...",
    "time": "20:30",
    "url": "https://www.youtube.com/watch?v=..."
  }
]
```

- **label** — A name for your own reference. Shows up in the terminal logs. Not displayed on screen.
- **time** — When the show starts, in 24-hour `HH:MM` format. (`20:30` = 8:30 PM)
- **url** — The full URL of the video to play.

Times must be in order, earliest to latest.

---

## Rules of the System

### Rule 1 — The clock decides what's on, not when you press play.

When the program starts, it looks at the current time and immediately loads whatever
show should be on right now. It does not start from the beginning of the schedule.

**Example:** Your schedule has a show at 9:30 and a show at 10:00. You start the
program at 9:55. It will load the 9:30 show and play it for 5 minutes, then switch
to the 10:00 show — just like tuning into a real TV channel mid-episode.

This means:
- Starting late puts you in the middle of whatever is currently scheduled.
- There is no "catch up." You get what's on now.

---

## Testing Transitions (Developers)

There is a separate script for testing show transitions without waiting for scheduled times.

**Run it with:**
```
python test.py
```

**What it does:**
1. Loads the first show in `schedule.json` immediately.
2. A **NEXT** button appears in the top-right corner of the browser.
3. Click it to cut to the next show (you'll see a brief black screen, then the new show loads).
4. It loops — after the last show it wraps back to the first.

**What to expect:**
- The browser opens fullscreen but YouTube's own fullscreen controls are visible.
  This is intentional in test mode — it makes the NEXT button reliably clickable.
  Production mode (`main.py`) runs with full fullscreen.
- There will be a short black screen during each transition while the new video loads.
  This is the intended channel-change feel, not a bug.

---

## Known Limitations

- **YouTube login:** YouTube blocks automated logins. You must log in manually once
  by launching the browser profile yourself. After that, your session is saved and
  the program will use it automatically.

- **Video length vs. slot length:** The program doesn't know how long a video actually
  is. If a video ends before the next show starts, it will sit on the end screen until
  the next scheduled show kicks in.

- **Midnight reset:** The schedule is based on today's time. Shows do not carry over
  past midnight. If your last show starts at 11:30 PM, it plays until the first show
  of the next day begins.

- **Transitions are not instant:** When switching shows, the browser navigates to a new
  URL. The user will see a brief black screen while the next video loads. This is expected
  behaviour and intentional — it mimics a TV channel change. True seamless preloading
  (where the next show buffers silently in the background) is a known limitation of
  the current architecture and is planned for a future release.
