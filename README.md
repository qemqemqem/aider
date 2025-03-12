# Aider - Enhanced Fork

This project is a fork of [aider.chat](https://aider.chat/), an AI pair programming tool that lets you collaborate with GPT to edit code in your local Git repository.

## New Features

This enhanced fork includes all the original aider functionality plus two new commands:

- `/focus`: Helps you concentrate on specific parts of your codebase during a session by automatically removing files that the LLM determines are not relevant to the focused file, streamlining your workflow
- `/document`: Similar to the `/code` command but instructs the LLM to specifically focus on documentation tasks rather than code changes

## Getting Started

See the original documentation at [aider.chat](https://aider.chat/) for installation and basic usage instructions.

## Using the New Commands

### Focus Command

The `/focus` command allows you to direct the AI's attention to specific files or code sections:

```
/focus path/to/file.py
```

### Document Command

The `/document` command helps you generate or improve documentation. You can use it in two ways:

```
# Focus on documenting a specific file
/document path/to/file.py

# Make a specific documentation request
/document add docstrings to all functions in utils.py
```

The `/document` command instructs aider to focus exclusively on documentation changes - it will update comments, docstrings, and documentation files without modifying actual code functionality. This is particularly useful when you want to improve code documentation without risking changes to the underlying implementation.

## Credits

This enhanced fork was developed by Andrew Keenan Richardson, building upon the excellent foundation of the original aider project.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
