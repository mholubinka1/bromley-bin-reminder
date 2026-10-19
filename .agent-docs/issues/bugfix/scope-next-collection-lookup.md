# Issues: bugfix/scope-next-collection-lookup

## Scraper gives a service without a 'Next collection' row the next service's date

**GitHub issue**: #302

**Blocked by**: None

**User stories**: 1, 2, 3

### What to build

Bound each service's "Next collection" lookup to its own section: walk forward from the service heading in document order and stop at the next service heading (or the end of the page). A service with no such row in its range is skipped. The test page builder mirrors the real page's structure and can build a service with or without the row, and a test reproduces the real page's service order.

### Acceptance criteria

- [ ] A service in the middle of the page without a "Next collection" row is skipped, and the services around it keep their own dates
- [ ] A service first on the page without the row is skipped, and the next service keeps its own date
- [ ] Given the real page's order (five services with a row, then two without), exactly the five are returned with their own dates
- [ ] The existing Scraper tests pass unchanged (last service without the row, empty page, suffixes, rollover, leap day, malformed dates, render failure)
- [ ] The test page builder mirrors the real structure, with invented dates and no household data
- [ ] All tests pass

---
