# 90s TV — Project Guide

## What This Is

A Python program that acts like a TV schedule. It opens a browser on a timer and plays
specific videos at specific times — like a real TV channel, but for whatever you want.

## Coding Style

Write code like you're explaining it to a junior engineer at 3am. They are tired,
stressed, and need to understand what's happening immediately.

Rules:
- **Simple over clever.** If you can do it in 10 obvious lines instead of 3 magic ones, do the 10 lines.
- **Name things what they are.** `current_time` not `ct`. `video_url` not `u`.
- **Comments explain WHY, not WHAT.** The code says what. The comment says why it's that way.
- **If something is complex, explain it well.** A short paragraph comment above a tricky block is fine.
- **No abstractions unless something is actually repeated.** Don't build a framework. Build a feature.
- **Flat is better than nested.** Avoid deep indentation. Break things into small, named functions.

## Project Structure

- `main.py` — entry point, runs the scheduler loop and manages the two-tab preloading system
- `services.py` — one load function per streaming service, plus shared helpers (mute, fullscreen, etc.)
- `schedule.json` — defines what plays at what time (edit this to change the lineup)
- `browser_profile/` — Chromium profile directory, **do not read or commit this** (contains login sessions)

## Tech

- Python + Playwright (Firefox, persistent browser profile so login sessions are saved)
- No external scheduler libraries — we use Python's `datetime` to check the clock

## Known Limitations

- YouTube blocks automated logins, so you must log in manually once using the browser profile
- Autoplay may be blocked by the browser — we click the play button as a fallback
