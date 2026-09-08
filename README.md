# 90s TV

An experiment in bringing back the feeling from the 90s of turning on the TV and watching whatever's on.

## What it does and why

90s TV plays videos in a browser according to a set schedule, switching shows automatically. The idea is to put together a lineup once, then sit back and enjoy it without having to choose what to watch next. Eventually, short filler clips (ads!) between shows could recreate more of that old TV rhythm.

## Tech

Built with Python and Playwright controlling Chromium, with a JSON file defining the lineup. No web server or frontend framework.

## Current status

An early prototype, not ready for use. Basic scheduling, YouTube playback, and manual show switching have worked in development. Clean transitions, reliable fullscreen during show changes, and background preloading are still being worked out. Filler clips and support for other streaming services are not implemented yet.
