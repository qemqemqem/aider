---
type: task
status: open
priority: high
story_points: 2
summary: Add file type filtering to repo map for focusing on specific file categories
tags:
  - repomap
  - filtering
affected: aider/repomap.py
related:
  - decisions/repo_map_content_filtering.md
  - issues/repo_map_content_prioritization.md
  - issues/repo_map_issue_summarization.md
---

# Implement File Type Filtering for Repo Map

## Description
Add functionality to filter repo map content based on file types, allowing users to focus on specific file categories (like .md files) while excluding others (like code files).

## Checklist
- [ ] Add configuration options for file type filtering
- [ ] Implement file extension-based filtering logic
- [ ] Create path-based filtering for specific directories
- [ ] Add command-line options to control filtering
- [ ] Update documentation to explain filtering capabilities
