# 90s TV

An experiment in bringing back the feeling from the 90s of turning on the TV and watching whatever happens to be on.

## What it does and why

90s TV plays videos in a browser according to a set schedule, switching shows automatically. The idea is to put together a lineup once, then sit back and enjoy it without having to choose what to watch next.

Eventually, short filler clips (ads!) between shows could recreate more of that old TV rhythm. Apparently removing choice from streaming required building software.

## Tech

Built with Python and Playwright controlling Chromium, with a JSON file defining the schedule and lineup.

## Current status

The current prototype supports scheduled playback, YouTube, fullscreen viewing, and manual show switching during development.

The next step is improving transitions between shows, including preloading content in the background and adding filler clips between programs. Support for additional streaming services can then be added as the project grows.

The ultimate goal is fairly simple: turn it on, see what's playing, and stop spending 20 minutes scrolling through streaming services trying to decide what to watch.