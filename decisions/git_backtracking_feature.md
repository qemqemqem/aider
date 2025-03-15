---
type: design_decision
status: open
priority: high
summary: Git backtracking and failed attempts documentation
tags:
  - git
  - user_experience
  - history_management
affected:
  - aider/repo.py
  - aider/commands.py
related:
  - issues/git_backtracking_implementation.md
  - issues/failed_attempts_documentation.md
---

# Git Backtracking and Failed Attempts Documentation

## Description

Design a feature that allows aider to naturally interact with git to backtrack to previous states when users indicate that current approaches aren't working. This would include:

1. Allowing natural language commands like "go back to before we started using foobar"
2. Automatically documenting failed approaches in a structured way
3. Creating a `failed_attempts/` directory to store information about unsuccessful approaches

## Key Questions

- How should aider interpret natural language backtracking requests?
- What information should be captured about failed attempts?
- How should the git history be navigated to find appropriate points to revert to?
- Should this feature be integrated with the existing undo functionality?
- How can we ensure the failed_attempts documentation is useful for future reference?

## Potential Implementation Approaches

### Natural Language Backtracking

- Implement keyword recognition for phrases like "go back", "revert", "undo", etc.
- Use context from conversation history to identify what feature or approach to revert
- Map natural language to specific git commits or ranges of commits

### Failed Attempts Documentation

- Create a structured template for documenting failed approaches
- Include information such as:
  - Description of the attempted approach
  - Code changes that were made
  - Errors or issues encountered
  - Reason for abandoning the approach
  - Timestamp and related conversation context

### Git Integration

- Enhance the existing GitRepo class to support more sophisticated history navigation
- Implement functionality to identify commits related to specific features or approaches
- Create a safe way to revert to previous states without losing history

## Success Criteria

- Users can naturally request to backtrack without needing to know git commands
- Failed approaches are automatically documented for future reference
- The system can identify the appropriate point in history to revert to
- The failed_attempts documentation provides valuable insights for future work
