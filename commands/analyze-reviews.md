---
description: Analyze collected PR review data to enhance the pr-review command with team-specific patterns
---

## Purpose

Learn from historical PR reviews in the project to identify recurring patterns, common issues, and project-specific conventions. Use these insights to enhance the pr-review command with actionable, team-specific guidance.

## Process

### 1. **Load the data**

Read all JSON files from the `data/` directory in the working tree. These files contain historical PR reviews fetched via `fetch_pr_reviews.py`.

Also read the current `commands/pr-review.md` file, specifically section 4 ("Review").

### 2. **Analyze review patterns**

Examine the review data across these dimensions:

**a) Recurring themes and categories**

What types of issues do reviewers flag most often? Look through:
- Inline code comments (`reviews[].inline_comments[]`)
- Review summary bodies (`reviews[].body`)
- PR discussion comments (`comments[]`)

Group findings into categories such as:
- Memory safety / resource management
- Internationalization (i18n)
- API design / breaking changes
- Documentation quality
- Code style / naming conventions
- License header compliance
- Error handling
- Test coverage
- Performance concerns
- Thread safety / concurrency
- Code deduplication

**b) Project-specific conventions**

What standards does this team enforce that aren't universal? Examples:
- Specific license headers required (e.g., GPL-2.0-or-later vs LGPL)
- Naming patterns (e.g., `n_read` vs `n` vs `readed`)
- Documentation requirements (man pages, API docs)
- Code sharing expectations (between dnf5 CLI and libdnf5)
- Specific APIs or patterns to use/avoid

**c) Common mistakes**

What issues appear repeatedly across different PRs and authors? These are high-value review checklist items. For example:
- Forgetting to update documentation
- Memory allocation failure handling
- Internationalization of user-facing strings
- Variable naming clarity

**d) Architecture and design patterns**

What structural decisions do reviewers push for? Examples:
- Code sharing between components (dnf5 and libdnf5)
- Const-correctness (const references vs copies)
- Error propagation patterns
- API stability considerations

**e) Review communication culture**

- What's the balance between CHANGES_REQUESTED vs APPROVED-with-nitpicks?
- How do reviewers phrase blocking vs non-blocking feedback?
- Do reviewers acknowledge when issues can be deferred to follow-up PRs?

### 3. **Generate enhanced review section**

Produce a **replacement** for section 4 ("Review") of `commands/pr-review.md`. The output should:

1. **Preserve existing generic items**: correctness, security, clarity, commit messages, referenced issues
2. **Add project-specific checklist items** learned from the data
3. **Group by priority**:
   - **Critical** — likely to block merge (security, correctness, breaking changes)
   - **Important** — should be addressed but may not block (documentation, naming, code sharing)
   - **Suggestions** — nice-to-have improvements (const-correctness, minor refactoring)
4. **Include brief rationale** where helpful (e.g., "Check license headers match `GPL-2.0-or-later` — team enforces consistency per PR #2654")
5. **Write as instructions for the reviewer**, not as a report about the data

### 4. **Output format**

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

- If multiple data files exist, analyze all of them to find cross-project patterns
- Weight patterns by frequency — items that appear 5+ times are more valuable than one-offs
- Preserve the actionable, concise style of the original pr-review.md command
- Be specific: "Check for GPL-2.0-or-later license headers" > "Check licensing"
