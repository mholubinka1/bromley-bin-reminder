# Issues: bugfix/firefox-quit-on-render-failure

## Firefox is always shut down when a page render fails

**GitHub issue**: #333

**Blocked by**: None

**User stories**: 1, 2, 3

### What to build

Move `driver.get(url)` inside `SeleniumPageSource.render`'s `try` and shut the driver down
once in `finally`, logging and swallowing a failing `quit()`. Name the 300-second wait.

### Acceptance criteria

- [x] Given `get` fails on every attempt, render raises `ScraperError` and every Firefox it created was quit
- [x] Given the wait never finds the service heading, render raises `ScraperError` and the Firefox was quit
- [x] Given a page that renders, render returns its page source and the Firefox was quit exactly once
- [x] Given `quit()` itself raises after a failed `get`, render still raises `ScraperError` and the shutdown failure is logged
- [x] The new tests fail before the fix where it changes behaviour, and all tests pass
