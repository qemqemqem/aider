---
type: design_decision
status: open
priority: high
story_points: 3
tags:
  - repomap
  - documentation
  - issues
affected: aider/repomap.py
related:
  - issues/repo_map_issue_summarization.md
subtasks:
  - issues/repo_map_file_filtering.md
  - issues/repo_map_content_prioritization.md
---

# Repo Map Content Filtering Design

## Description
Design and implement a system to allow the repo map to focus on specific file types (like issues or markdown files) while deprioritizing or excluding code files. This would improve the context provided to the AI when working with documentation or issue management tasks.

## Checklist
- [ ] Define filtering criteria for different file types
- [ ] Determine how to prioritize/deprioritize different content types
- [ ] Consider how to handle mixed content repositories
- [ ] Design API for user control of filtering preferences
- [ ] Evaluate impact on token usage and performance
