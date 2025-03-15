# Aider - Enhanced Fork

> **⚠️ BETA WARNING**: This enhanced fork is currently in beta. Features may change, break, or be removed without notice. Use at your own risk in production environments.

This project is a fork of [aider.chat](https://aider.chat/), an AI pair programming tool that lets you collaborate with an LLM to edit code in your local Git repository.

## New Features

This enhanced fork includes all the original aider functionality plus these new commands:

- `/focus`: Helps you concentrate on specific parts of your codebase during a session by automatically removing files that the LLM determines are not relevant to the focused file, streamlining your workflow
- `/document`: Similar to the `/code` command but instructs the LLM to specifically focus on documentation tasks rather than code changes
- `/prioritize`: Analyzes all open issues in your repository and determines which one is most important to tackle next
- `/advise`: Creates an advisor persona based on your question and gives advice from that perspective (e.g., `/advise Tell me what legal would think of this code`)
- `/plan`: Helps you create a structured plan for implementing features or changes without making immediate code modifications

## Installation

You can install this enhanced fork directly from GitHub:

```bash
pip install git+https://github.com/qemqemqem/aider-advanced.git
```

For a specific version or branch:

```bash
# Install from a specific tag
pip install git+https://github.com/qemqemqem/aider-advanced.git@v0.x.x

# Install from a specific branch
pip install git+https://github.com/qemqemqem/aider-advanced.git@branch-name
```

Or clone the repository and install locally:

```bash
git clone https://github.com/qemqemqem/aider-advanced.git
cd aider-advanced
pip install -e .
```

### Requirements

- Python 3.8 or higher
- Git
- An API key for your preferred LLM provider (OpenAI, Anthropic, etc.)

## Getting Started

See the original documentation at [aider.chat](https://aider.chat/) for basic usage instructions.

## Using the New Commands

### Focus Command

The `/focus` command allows you to direct the AI's attention to specific files or code sections:

```
/focus path/to/file.py
```

### Document Command

The `/document` command helps you generate or improve documentation. You can use it like this:

```
/document add docstrings to all functions in utils.py
```

The `/document` command instructs aider to focus exclusively on documentation changes - it will update comments, docstrings, and documentation files without modifying actual code functionality. This is particularly useful when you want to improve code documentation without risking changes to the underlying implementation.

When `/document` is run with no message, aider will enter document mode, which is just like `/code` mode but with a focus on documentation tasks.

### Advise Command

The `/advise` command creates an advisor persona based on your question and provides advice from that perspective:

```
/advise Tell me what legal would think of this code
```

This command will either use an existing persona file or create a new one appropriate to your question, then generate advice from that perspective. It's useful for getting specialized feedback on your code from different viewpoints. For example, in the above command, the command will create a "legal" persona and provide advice on the code pretending to be that character. 

### Plan Command

The `/plan` command helps you create a structured plan for implementing features or changes:

```
/plan Create a plan to implement the foo function
```

This command focuses on planning rather than immediate code changes. When run without arguments, it switches to plan mode.

When run, it will create issues and bugs in the `issues/` and `bugs/` directories of your repository, respectively. These will be markdown files with YAML frontmatter containing metadata about the task, such as priority, story points, and related issues.

### Prioritize Command

The `/prioritize` command analyzes all open issues in your repository and helps you decide which one to work on next:

```
/prioritize
```

This command will scan your repository for issue files (typically markdown files in an issues directory), analyze their content, priority markers, dependencies, and other metadata, then recommend the most important issue to tackle next.

It's intended to be used after the `/plan` command, to sort through the tasks you've identified and determine which one should be prioritized first. If you accept its suggestion, it will automatically execute the `/focus` command on the chosen issue.

## Credits

This enhanced fork was developed by Andrew Keenan Richardson, building upon the excellent foundation of the original aider project. I suppose a great deal of credit goes to aider itself (and Claude), who have contributed a majority of the commits to this codebase. 

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
