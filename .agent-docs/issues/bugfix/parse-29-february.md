# Issues: bugfix/parse-29-february

## Scraper fails to parse a collection dated 29 February

**GitHub issue**: #298

**Blocked by**: None

**User stories**: 1, 2, 3

### What to build

Read the month from the month name in the cleaned date text, derive the target year from it as today (current year, or next year for a January date read in December), and parse the full date once with that year, instead of the year-less parse that assumed 1900. A 29 February collection read with a clock in a leap year then parses to that date. All other parsing rules are unchanged.

### Acceptance criteria

- [ ] Given a page listing "Tuesday, 29th February" and a clock on Friday 25 February 2028 in London, the Scraper returns a collection dated 29 February 2028 in London time
- [ ] The regression test fails before the fix and passes after it
- [ ] The existing Scraper tests pass unchanged (suffixes, "(In Progress)", the December-to-January rollover, a missing next collection, an empty page, a render failure)
- [ ] A malformed date still raises `ValueError`
- [ ] All tests pass

---
