---
type: design_decision
status: open
priority: medium
story_points: 1
summary: Design an effective prompt for the LLM to evaluate and prioritize open issues
tags:
  - commands
  - prompts
related:
  - issues/cmd_prioritize_command.md
---

# Design Prompt for Issue Prioritization

## Description
Design an effective prompt for the LLM to evaluate and prioritize open issues. The prompt needs to guide the LLM to analyze issue metadata and content to determine which issue is most important to tackle next.

## Checklist
- [ ] Define the criteria for prioritization (urgency, impact, complexity, dependencies)
- [ ] Create a structured format for the LLM to receive issue data
- [ ] Design a response format that clearly identifies the chosen issue and explains the reasoning
- [ ] Include handling for edge cases (no priority field, conflicting priorities)
- [ ] Test the prompt with various issue combinations to ensure consistent results

## Considerations
- The prompt should instruct the LLM to consider:
  - Explicit priority markers in YAML frontmatter
  - Issue type (bug vs. feature vs. design decision)
  - Dependencies between issues
  - Story points (complexity/effort)
  - Tags that might indicate critical areas
  - The actual content/description of the issue
