---
description: Analyze collected PR review data to enhance the pr-review command with team-specific patterns
---

## Purpose

Learn from historical PR reviews in the project to identify recurring **categories** of issues and project-specific conventions. Use these insights to enhance the pr-review command with actionable, team-specific guidance.

The output should capture patterns at the *category* level (e.g., "check i18n for user-facing strings"), not prescribe specific code fixes (e.g., "use `reserve()`" or "rename the JSON field").

## Process

### 1. **Load the data**

Read all JSON files from the `data/` directory in the working tree. These files contain historical PR reviews fetched via `fetch_pr_reviews.py`.

Each file has the structure:
```json
{
  "repo": "owner/repo",
  "fetched_at": "...",
  "pull_requests": [ ... ]
}
```

Each PR object contains: `number`, `title`, `url`, `author`, `body`, `labels`, `reviewDecision`, `comments[]`, and `reviews[]` (with `inline_comments[]`).

Also read the current `commands/pr-review.md` file, specifically section 4 ("Review").

### 2. **Extract patterns (per-batch)**

The data is too large to analyze in one pass. Process PRs in batches of ~30 at a time.

For each batch, examine:
- Inline code comments (`reviews[].inline_comments[]`)
- Review summary bodies (`reviews[].body`)
- PR discussion comments (`comments[]`)

Extract a list of **issue categories** observed in the batch. For each category, record:
- Category name (e.g., "Internationalization", "Error handling")
- How many times it appeared in this batch
- One representative example quote (to preserve context for synthesis)

Skip PRs that have no review comments or inline comments — they provide no signal.

**Focus on categories, not specific fixes.** The goal is to identify *what kinds of things* reviewers care about, not to catalog individual suggestions.

### 3. **Synthesize across batches**

After processing all batches, combine the per-batch category lists:

**a) Recurring themes and categories**

Merge categories across batches. Rank by total frequency. Focus on categories that appear across multiple PRs and authors — one-offs are noise.

Example categories (discover from data, don't assume):
- Memory safety / resource management
- Internationalization (i18n)
- API design / breaking changes
- Documentation quality
- Code style / naming conventions
- License header compliance
- Error handling
- Test coverage
- Performance concerns
- Code deduplication

**b) Project-specific conventions**

What standards does this team enforce that aren't universal? Look for patterns like:
- Specific license headers or copyright formats
- Naming conventions unique to the project
- Documentation requirements (man pages, API docs, changelog)
- Code organization expectations (where logic should live)
- Required or prohibited patterns

**c) Common mistakes**

What issues appear repeatedly across different PRs and authors? These are high-value review checklist items — things any contributor is likely to miss.

**d) Architecture and design preferences**

What structural decisions do reviewers push for? Look for patterns around:
- Code sharing between components
- Const-correctness and reference semantics
- Error propagation patterns
- API stability considerations

**e) Review communication culture**

- What's the balance between CHANGES_REQUESTED vs APPROVED-with-nitpicks?
- How do reviewers phrase blocking vs non-blocking feedback?
- Do reviewers acknowledge when issues can be deferred to follow-up PRs?

### 4. **Generate enhanced review section**

Produce a **replacement** for section 4 ("Review") of `commands/pr-review.md`. The output should:

1. **Preserve existing generic items**: correctness, security, clarity, commit messages, referenced issues
2. **Add project-specific checklist items** learned from the data — phrased as categories to check, not specific code changes
3. **Group by priority**:
   - **Critical** — likely to block merge (security, correctness, breaking changes)
   - **Important** — should be addressed but may not block (documentation, naming, code sharing)
   - **Suggestions** — nice-to-have improvements (const-correctness, minor refactoring)
4. **Include brief rationale** where helpful (e.g., "Check license headers — team enforces consistency")
5. **Write as instructions for the reviewer**, not as a report about the data
6. **Stay general** — checklist items should apply to any PR in the project, not reference specific functions, APIs, or data structures

### 5. **Output format**

Present the enhanced review section in markdown, ready to replace section 4 of `commands/pr-review.md`. Begin with:

```markdown
### 4. **Review**

Focus on:
...
```

Then include the enhanced checklist with team-specific items clearly integrated.

After the review section, include a brief summary (2-3 paragraphs) of:
- Most common review themes observed
- Most valuable project-specific insights
- Suggested priorities for the team's review process

This summary helps the user understand what was learned and decide whether to adopt the suggestions.

---

## Notes

- Process PRs in batches to stay within context limits — extract categories per batch, then synthesize
- Weight patterns by frequency — items that appear across multiple PRs are more valuable than one-offs
- Preserve the actionable, concise style of the original pr-review.md command
- Stay at the category level: "Check i18n for user-facing strings" > "Wrap this printf in _()"
- If multiple data files exist, analyze all of them to find cross-project patterns
