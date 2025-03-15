---
type: task
status: open
priority: high
story_points: 2
tags:
  - repomap
  - filtering
affected: aider/repomap.py
related:
  - decisions/repo_map_content_filtering.md
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
