# AGENTS.md

## Project Overview

90s TV is a Python application that recreates the experience of a traditional
scheduled TV channel.

The application uses Playwright to control a browser and play scheduled content
from services such as YouTube. Content is defined in a configurable schedule
and should play automatically at the appropriate time.

The goal is to create a continuous TV-like experience where the user can start
the application and watch whatever is currently scheduled without manually
selecting content.

## How It Should Work

At a high level:

1. Load the configured TV schedule.
2. Determine what content should currently be playing.
3. Open the appropriate streaming service in the browser.
4. Start playback and enter fullscreen.
5. Monitor the schedule for the next transition.
6. Move to the next scheduled item automatically.
7. Continue indefinitely.

The system should eventually support multiple streaming services and filler
content between scheduled shows.

## Project Structure

- `main.py` - Main application and scheduling loop.
- `test.py` - Development utilities for testing playback and transitions.
- `services.py` - Streaming-service handlers and shared playback functionality.
- `schedule.json` - Defines what content should play and when.
- `manual.md` - User documentation.
- `browser_profile/` - Persistent browser session data. Do not read or commit.

## Development Principles

- Prefer simple, explicit solutions over clever ones.
- Keep functions small and focused.
- Use descriptive variable and function names.
- Comments should explain why, not simply restate what the code does.
- Avoid unnecessary abstractions.
- Prefer flat control flow over deeply nested logic.
- Keep service-specific behaviour isolated from the core scheduling logic.
- Preserve the TV-like experience when designing playback and transitions.

## Safety

- Never commit credentials, cookies, session data, or API keys.
- Do not inspect or modify `browser_profile/` unless explicitly instructed.
- Do not make git commits or push changes unless explicitly instructed.