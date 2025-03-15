---
type: task
status: open
priority: medium
story_points: 2
summary: Enhance repo map to prioritize content types with different levels of detail
tags:
  - repomap
  - prioritization
affected: aider/repomap.py
related:
  - decisions/repo_map_content_filtering.md
  - issues/repo_map_file_filtering.md
  - issues/repo_map_issue_summarization.md
---

# Implement Content Prioritization for Repo Map

## Description
Enhance the repo map to prioritize certain content types over others, allowing for more nuanced control than simple filtering. This would allow including both code and non-code files but with different levels of detail or prominence.

## Checklist
- [ ] Design prioritization scoring system
- [ ] Implement content type detection beyond file extensions
- [ ] Create token allocation strategy based on priorities
- [ ] Add user configuration for priority weights
- [ ] Test with mixed repositories containing various file types
