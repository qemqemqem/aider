---
type: task
status: open
priority: medium
story_points: 2
summary: Create system for documenting failed attempts
tags:
  - documentation
  - git
affected: aider/repo.py
related:
  - decisions/git_backtracking_feature.md
---

# Create System for Documenting Failed Attempts

## Description

Develop a system that automatically documents failed approaches when a user requests to backtrack. This will create a structured record in a `failed_attempts/` directory, describing what was attempted and what issues were encountered.

## Checklist

- [ ] Create a `failed_attempts/` directory structure
- [ ] Design a markdown template for failed attempt documentation
- [ ] Implement functionality to extract relevant information from the conversation history
- [ ] Develop a mechanism to analyze what went wrong based on error messages and user feedback
- [ ] Create a naming convention for failed attempt documents
- [ ] Add functionality to reference failed attempts in future conversations
- [ ] Ensure failed attempt documentation includes code snippets of what was tried
