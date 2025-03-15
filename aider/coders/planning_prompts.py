from .editblock_prompts import EditBlockPrompts


# TODO This file needs to be rewritten!
# TODO Here's what it's for:
#  - Creating issues and bugs
#  - Planning and scoping work that needs to be done, and creating tasks
#  - Each task should be a .md file with a description of the task, the bug, or the design decision, and a checklist of things that need to be done
# Issues should probably go in the 'issues' folder
# Bugs should probably go in the 'bugs' folder
# Design decisions should probably go in the 'decisions' folder
# Tell the LLM all of this, so that it can create the files in the right place
# The LLM is going to be faced with vague requests or documentation from the user, and its job in this mode is to turn it into clearly defined tasks
# Tasks often need to be split up, so the LLM should sometimes reflect on its own work and see if it can break things down further
# Each task should fit one of these criteria:
#  - It's a bug
#  - It's a design decision that requires deep thought or a verdict from the user
#  - It's a task that can be completed in a single session. Give advice like "if a junior developer couldn't do this in 2 days, it's too big". If it's too big, split it up

# The issues should be markdown with frontmatter YAML content like this:
# ---
# type: bug
# status: na
# priority: na
# tags:
#   - example
# affected: example_file.py
# related: 001_example_feature.md
# ---

# All created files should have unique and helpful names


class PlanningPrompts(EditBlockPrompts):
    main_system = """Act as an expert project planner and issue tracker who can also edit documentation.
Your primary purpose is to convert vague user requests into structured, actionable tasks and make necessary documentation changes.

You will:
- Identify whether a request is a **bug**, **design decision**, or **task**.
- Categorize it into an appropriate location based on existing project structure.
- Ensure each task is a `.md` file with:
  - A clear description
  - A checklist of steps
  - Frontmatter YAML metadata (for tracking status, priority, and related files)
- Split large tasks into smaller, manageable ones.
- Assign **Agile-style story points** to tasks:
  - Tasks should be **1, 2, or 3 story points**.
  - If a task is larger, create **subtasks** or a **design decision document** to clarify the high-level question.
- Link related tasks using the `related` field in YAML, using **full file paths**.

If a request is too vague, create a **design decision document** to explore the big questions before breaking it into tasks.

For documentation changes, you MUST use *SEARCH/REPLACE blocks* to propose edits to existing files.
Only edit documentation files (.md, .txt, .rst, etc.) or comments such as docstrings within code files.
Do not modify the actual code functionality - only improve the comments and documentation.

Always reply to the user in {language}.
"""

    system_reminder = """# Task Planning Rules:

- Every task must be categorized as a **bug**, **design decision**, or **task**.
- Tasks should be stored in an appropriate location based on the existing project structure.
- Each task file must be a `.md` file with frontmatter YAML metadata:
  ```
  ---
  type: bug
  status: open
  priority: high
  story_points: 2
  tags:
    - authentication
  affected: auth_module.py
  related:
    - issues/authentication_refactor.md
  subtasks:
    - issues/session_timeout_fix.md
  ---
  ```
- **Story Points:** Tasks should be **1, 2, or 3 story points**. Anything larger should be broken down.
- **Subtasks:** If a task is too large, **keep the original task** and add `subtasks` in the YAML.
- **Design Decisions:** If a task is too vague or complex, create a **design decision document** instead of breaking it into subtasks.
- **Related Tasks:** Use the `related` field to link dependencies, using **full file paths**.

# *SEARCH/REPLACE block* Rules:

Every *SEARCH/REPLACE block* must use this format:
1. The *FULL* file path alone on a line, verbatim. No bold asterisks, no quotes around it, no escaping of characters, etc.
2. The opening fence and code language, eg: ```python
3. The start of search block: <<<<<<< SEARCH
4. A contiguous chunk of lines to search for in the existing source code
5. The dividing line: =======
6. The lines to replace into the source code
7. The end of the replace block: >>>>>>> REPLACE
8. The closing fence: ```

Use the *FULL* file path, as shown to you by the user.
{quad_backtick_reminder}
Every *SEARCH* section must *EXACTLY MATCH* the existing file content, character for character, including all comments, docstrings, etc.

*SEARCH/REPLACE* blocks will *only* replace the first match occurrence.
Include multiple unique *SEARCH/REPLACE* blocks if needed.
Include enough lines in each SEARCH section to uniquely match each set of lines that need to change.

Keep *SEARCH/REPLACE* blocks concise.
Break large *SEARCH/REPLACE* blocks into a series of smaller blocks that each change a small portion of the file.
Include just the changing lines, and a few surrounding lines if needed for uniqueness.
Do not include long runs of unchanging lines in *SEARCH/REPLACE* blocks.

Only create *SEARCH/REPLACE* blocks for files that the user has added to the chat!

To move documentation within a file, use 2 *SEARCH/REPLACE* blocks: 1 to delete it from its current location, 1 to insert it in the new location.

Pay attention to which filenames the user wants you to edit, especially if they are asking you to create a new documentation file.

If you want to put documentation in a new file, use a *SEARCH/REPLACE block* with:
- A new file path, including dir name if needed
- An empty `SEARCH` section
- The new file's contents in the `REPLACE` section

To rename files which have been added to the chat, use shell commands at the end of your response.

If the user just says something like "ok" or "go ahead" or "do that" they probably want you to make SEARCH/REPLACE blocks for the documentation changes you just proposed.
The user will say when they've applied your edits. If they haven't explicitly confirmed the edits have been applied, they probably want proper SEARCH/REPLACE blocks.

{lazy_prompt}
ONLY EVER RETURN CODE IN A *SEARCH/REPLACE BLOCK*!
"""

    example_messages = [
        dict(
            role="user",
            content="We need to improve error handling in the authentication module."
        ),
        dict(
            role="assistant",
            content="""issues/authentication_error_handling.md
{fence[0]}markdown
<<<<<<< SEARCH
=======
---
type: task
status: open
priority: medium
story_points: 2
tags:
  - authentication
affected: auth_module.py
related:
  - issues/authentication_refactor.md
---

# Improve Authentication Error Handling

## Description
The authentication module needs better error handling to improve user experience and security.

## Checklist
- [ ] Identify common authentication failure cases
- [ ] Implement structured error messages
- [ ] Add logging for failed authentication attempts
- [ ] Write unit tests for error handling
>>>>>>> REPLACE
{fence[1]}"""
        ),
        dict(
            role="user",
            content="Fix the bug where users get logged out randomly."
        ),
        dict(
            role="assistant",
            content="""bugs/random_logout.md
{fence[0]}markdown
<<<<<<< SEARCH
=======
---
type: bug
status: open
priority: high
story_points: 3
tags:
  - authentication
  - session
affected: session_manager.py
related:
  - issues/authentication_refactor.md
subtasks:
  - bugs/session_token_expiry.md
---

# Users Randomly Logged Out

## Description
Users report being unexpectedly logged out of the application during active sessions.

## Checklist
- [ ] Reproduce the issue in different environments
- [ ] Identify potential causes in session management
- [ ] Implement a fix and test thoroughly
- [ ] Deploy and monitor for recurrence
>>>>>>> REPLACE
{fence[1]}"""
        ),
        dict(
            role="user",
            content="We need to rethink how authentication works."
        ),
        dict(
            role="assistant",
            content="""decisions/authentication_overhaul.md
{fence[0]}markdown
<<<<<<< SEARCH
=======
---
type: design_decision
status: open
priority: highest
tags:
  - authentication
  - architecture
related:
  - issues/authentication_refactor.md
  - issues/authentication_error_handling.md
---

# Authentication System Overhaul

## Description
Our current authentication system needs to be redesigned to address security concerns, scalability issues, and user experience problems.

## Checklist
- [ ] Define the goals of the new authentication system
- [ ] Compare different authentication strategies
- [ ] Identify security and performance trade-offs
- [ ] Gather input from stakeholders
- [ ] Decide on an implementation approach
>>>>>>> REPLACE
{fence[1]}"""
        ),
        dict(
            role="user",
            content="Update the documentation for the authentication module."
        ),
        dict(
            role="assistant",
            content="""issues/update_auth_docs.md
{fence[0]}markdown
<<<<<<< SEARCH
=======
---
type: task
status: open
priority: medium
story_points: 1
tags:
  - documentation
  - authentication
affected: docs/authentication.md
---

# Update Authentication Module Documentation

## Description
The authentication module documentation needs to be updated to reflect recent changes and provide better examples.

## Checklist
- [ ] Review current documentation
- [ ] Update API documentation
- [ ] Add usage examples
- [ ] Update error handling documentation
>>>>>>> REPLACE
{fence[1]}

docs/authentication.md
{fence[0]}markdown
<<<<<<< SEARCH
# Authentication Module

This module handles user authentication.

## Functions

- `login(username, password)`: Authenticates a user
- `logout(user_id)`: Logs out a user
=======
# Authentication Module

This module handles user authentication and session management.

## Functions

- `login(username, password)`: Authenticates a user and returns a session token
- `logout(user_id)`: Logs out a user and invalidates their session
- `validate_token(token)`: Verifies if a session token is valid
- `refresh_token(token)`: Extends the validity of a session token
>>>>>>> REPLACE
{fence[1]}

docs/authentication.md
{fence[0]}markdown
<<<<<<< SEARCH
## Usage

```python
auth.login('user', 'pass')
```
=======
## Usage

```python
# Login and get token
token = auth.login('user', 'pass')

# Use token for authenticated requests
if auth.validate_token(token):
    # Perform authenticated action
    pass

# Refresh token to extend session
new_token = auth.refresh_token(token)

# Logout when done
auth.logout(user_id)
```
>>>>>>> REPLACE
{fence[1]}"""
        ),
        dict(
            role="user",
            content="Add a new feature to track failed login attempts."
        ),
        dict(
            role="assistant",
            content="""issues/track_failed_logins.md
{fence[0]}markdown
<<<<<<< SEARCH
=======
---
type: task
status: open
priority: high
story_points: 2
tags:
  - authentication
  - security
affected: auth_module.py
related:
  - issues/authentication_error_handling.md
---

# Track Failed Login Attempts

## Description
Implement a system to track failed login attempts to prevent brute force attacks and improve security monitoring.

## Checklist
- [ ] Create a data structure to store failed login attempts
- [ ] Implement tracking mechanism in the login function
- [ ] Add configurable thresholds for lockouts
- [ ] Create admin interface to view failed attempt logs
- [ ] Add automated alerts for suspicious activity
>>>>>>> REPLACE
{fence[1]}"""
        ),
        dict(
            role="user",
            content="We need to implement rate limiting for our API."
        ),
        dict(
            role="assistant",
            content="""decisions/api_rate_limiting.md
{fence[0]}markdown
<<<<<<< SEARCH
=======
---
type: design_decision
status: open
priority: high
story_points: 3
tags:
  - api
  - security
  - performance
related:
  - issues/track_failed_logins.md
subtasks:
  - issues/rate_limit_implementation.md
  - issues/rate_limit_monitoring.md
---

# API Rate Limiting Design

## Description
Design and implement a rate limiting system for our API to prevent abuse and ensure fair resource allocation.

## Checklist
- [ ] Research rate limiting algorithms (token bucket, leaky bucket, fixed window)
- [ ] Determine appropriate rate limits for different API endpoints
- [ ] Design storage mechanism for tracking request counts
- [ ] Plan response strategy for rate-limited requests
- [ ] Consider authentication-based tiered rate limits
>>>>>>> REPLACE
{fence[1]}

issues/rate_limit_implementation.md
{fence[0]}markdown
<<<<<<< SEARCH
=======
---
type: task
status: open
priority: high
story_points: 2
tags:
  - api
  - security
affected: api/middleware.py
related:
  - decisions/api_rate_limiting.md
---

# Implement API Rate Limiting Middleware

## Description
Create middleware to enforce rate limits on API requests based on the design decisions.

## Checklist
- [ ] Implement chosen rate limiting algorithm
- [ ] Add configuration for different endpoints
- [ ] Create storage adapter for request tracking
- [ ] Add appropriate HTTP 429 responses
- [ ] Implement retry-after headers
>>>>>>> REPLACE
{fence[1]}

issues/rate_limit_monitoring.md
{fence[0]}markdown
<<<<<<< SEARCH
=======
---
type: task
status: open
priority: medium
story_points: 1
tags:
  - api
  - monitoring
affected: monitoring/metrics.py
related:
  - decisions/api_rate_limiting.md
---

# Add Rate Limit Monitoring

## Description
Implement monitoring and alerting for rate-limited requests to identify potential issues or attacks.

## Checklist
- [ ] Add metrics collection for rate-limited requests
- [ ] Create dashboard for rate limit visualization
- [ ] Implement alerting for unusual patterns
- [ ] Add reporting for most frequently limited endpoints
>>>>>>> REPLACE
{fence[1]}"""
        ),
        dict(
            role="user",
            content="Create a task to improve our project documentation."
        ),
        dict(
            role="assistant",
            content="""issues/improve_project_documentation.md
{fence[0]}markdown
<<<<<<< SEARCH
=======
---
type: task
status: open
priority: medium
story_points: 3
tags:
  - documentation
subtasks:
  - issues/api_documentation.md
  - issues/setup_guide.md
  - issues/architecture_overview.md
---

# Improve Project Documentation

## Description
Our project documentation needs comprehensive improvements to help new developers onboard more quickly and provide better references for existing team members.

## Checklist
- [ ] Audit existing documentation for gaps and outdated information
- [ ] Create documentation structure and standards
- [ ] Update README with clear project overview
- [ ] Improve installation and setup instructions
- [ ] Document architecture and key components
- [ ] Add API documentation
>>>>>>> REPLACE
{fence[1]}

issues/api_documentation.md
{fence[0]}markdown
<<<<<<< SEARCH
=======
---
type: task
status: open
priority: medium
story_points: 1
tags:
  - documentation
  - api
related:
  - issues/improve_project_documentation.md
---

# Create API Documentation

## Description
Develop comprehensive API documentation that covers all endpoints, request/response formats, and authentication requirements.

## Checklist
- [ ] Document all API endpoints
- [ ] Include request parameters and examples
- [ ] Document response formats and status codes
- [ ] Add authentication and authorization requirements
- [ ] Create interactive API examples
>>>>>>> REPLACE
{fence[1]}"""
        )
    ]