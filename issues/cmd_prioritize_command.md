---
type: task
status: open
priority: high
story_points: 2
tags:
  - commands
  - productivity
affected: aider/commands.py
---

# Add cmd_prioritize Command

## Description
Create a new `/prioritize` command that will ask the LLM to analyze all open issues, determine which one is most important to tackle next, and automatically focus on that issue.

## Checklist
- [ ] Add `cmd_prioritize` method to the Commands class
- [ ] Implement logic to gather all open issues
- [ ] Create a prompt for the LLM to evaluate and prioritize issues
- [ ] Parse the LLM's response to identify the chosen issue
- [ ] Automatically execute the `/focus` command on the chosen issue
- [ ] Add command to the help documentation
- [ ] Write tests for the new command
