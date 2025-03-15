---
type: task
status: open
priority: high
story_points: 3
summary: Create a /prioritize command to analyze and focus on the most important issue
tags:
  - commands
  - productivity
affected: aider/commands.py
related:
  - issues/prioritize_prompt_design.md
subtasks:
  - issues/prioritize_prompt_design.md
---

# Add cmd_prioritize Command

## Description
Create a new `/prioritize` command that will ask the LLM to analyze all open issues, determine which one is most important to tackle next, and automatically focus on that issue.

## Checklist
- [ ] Add `cmd_prioritize` method to the Commands class
- [ ] Get the repomap with include_text_and_md=True, to ensure all the issue files are visible
- [ ] Create a prompt for the LLM to evaluate and prioritize issues
- [ ] Parse the LLM's response to identify the chosen issue
- [ ] Ask the user to confirm the chosen issue and that they would like to /focus on it
- [ ] Automatically execute the `/focus` command on the chosen issue
- [ ] Add command to the help documentation
- [ ] Write tests for the new command

## Open Questions
1. How should we handle issues without explicit priority in their YAML frontmatter?
2. Should we consider dependencies between issues (via the `related` field) when prioritizing?
3. What criteria should the LLM use to determine importance (urgency, impact, complexity)?
4. Should we allow the user to specify additional prioritization criteria as arguments?
5. How should we handle the case where there are no open issues?
6. Should we provide a preview of the LLM's reasoning before automatically focusing on the chosen issue?
