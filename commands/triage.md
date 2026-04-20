---
description: Triage a bug report from Bugzilla, GitHub Issues, or GitHub Discussions. Assess validity, severity, impact, and suggest a reproducer if missing.
---

## User Input
```text
$ISSUE_URL
```

`$ISSUE_URL` is required. It must be a URL pointing to one of:
- A Bugzilla bug (e.g. `https://bugzilla.redhat.com/show_bug.cgi?id=12345`)
- A GitHub issue (e.g. `https://github.com/owner/repo/issues/123`)
- A GitHub discussion (e.g. `https://github.com/owner/repo/discussions/456`)


## Purpose
Triage an incoming bug report or issue. Determine whether the issue is valid, assess its severity and user impact, and provide a reproducer if one is missing. Gather context from any linked or related issues.


## Process

### 1. **Fetch the issue**

Determine the issue type from the URL and fetch its full content:

- **GitHub issue**: Extract `owner/repo` and issue number from the URL, then:
  ```
  gh issue view <number> --repo <owner/repo> --comments
  ```
- **GitHub discussion**: Extract `owner/repo` and discussion number from the URL, then:
  ```
  gh api graphql -f query='
    query {
      repository(owner: "<owner>", name: "<repo>") {
        discussion(number: <number>) {
          title
          body
          comments(first: 50) { nodes { body author { login } } }
          labels(first: 10) { nodes { name } }
        }
      }
    }'
  ```
- **Bugzilla bug**: Fetch the bug page using WebFetch. Extract the bug summary, description, comments, status, severity, priority, and any linked bugs.

Record the title, description, all comments, labels/tags, and any metadata (reporter, date, assignee, status).

---

### 2. **Gather linked issues**

Scan the issue description and comments for references to other issues:
- GitHub cross-references (`#123`, `owner/repo#456`, full GitHub URLs)
- Bugzilla references (bug IDs, Bugzilla URLs)
- CVE references

For each linked issue, fetch its content using the same approach as step 1. Read these for context — they may reveal duplicates, prior discussion, or related symptoms.

---

### 3. **Understand the relevant code**

If the issue references specific components, files, error messages, or stack traces:
- Search the local codebase for the referenced code using Grep and Glob.
- Read the relevant source files to understand the current behavior.
- Check git log for recent changes in the affected area that might be related.

This step is essential for assessing validity — skip it only if the issue is purely about documentation, packaging, or something outside this repository.

---

### 4. **Assess validity**

Determine whether the reported issue is valid:
- **Is it reproducible?** Does the reporter provide clear steps, and do they make sense given the code?
- **Is it a real bug vs. expected behavior?** Check documentation and code intent.
- **Is it a duplicate?** Check if the linked issues or your code search reveal an existing report.
- **Is it still relevant?** Has the code changed since the report? Has it already been fixed?

Classify as: **Valid bug**, **Expected behavior**, **Needs more information**, **Already fixed**, or **Duplicate** (with link).

---

### 5. **Assess severity and impact**

Evaluate along two axes:

**Severity** (how bad is it when it happens):
- **Critical** — data loss, security vulnerability, complete feature breakage, crash
- **High** — significant functionality broken, no workaround
- **Medium** — functionality impaired but workaround exists
- **Low** — cosmetic issue, minor inconvenience, edge case

**Impact** (how many users are affected):
- Look for signals: number of reports/duplicates, number of comments or upvotes, whether it affects a default/common configuration vs. niche setup
- Consider whether the affected code path is in a hot path or rarely exercised
- Note any environment-specific constraints (specific OS, specific version, specific config)

---

### 6. **Reproducer**

If the issue does not include a clear reproducer:
- Draft a minimal step-by-step reproducer based on the description, comments, and your understanding of the code.
- Include specific commands, configuration, and expected vs. actual output.
- If you cannot construct a confident reproducer, state what information is missing and suggest questions to ask the reporter.

If the issue already includes a reproducer, evaluate whether it is complete and correct. Suggest improvements if needed.

---

### 7. **Report**

Produce a structured triage report:

```
## Triage Summary

**Issue:** <title and URL>
**Validity:** <Valid bug | Expected behavior | Needs more info | Already fixed | Duplicate>
**Severity:** <Critical | High | Medium | Low>
**Impact:** <High | Medium | Low> — <brief justification>

## Analysis
<Explanation of the root cause or suspected root cause, referencing specific code when possible>

## Reproducer
<Step-by-step reproducer, or note that one was already provided and is adequate>

## Linked Issues
<Summary of related issues and how they connect>

## Recommended Next Steps
<Suggested actions: fix, close, request more info, mark as duplicate, etc.>
```
