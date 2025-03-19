import json
import os
import re
from datetime import datetime

class AdvancedCommandsMixin:
    """Mixin class providing advanced commands."""
    
    # Define ANY_GIT_ERROR for use in the BacktrackManager
    ANY_GIT_ERROR = (Exception,)  # Replace with actual git error types if needed

    def cmd_document(self, args):
        """Enter document/editor mode using 2 different models. If no prompt provided, switches to document/editor mode."""  # noqa
        return self._generic_chat_command(args, "document")

    def completions_document(self):
        files = set(self.coder.get_all_relative_files())
        files = files - set(self.coder.get_inchat_relative_files())
        files = [self.quote_fname(fn) for fn in files]
        return files

    def cmd_plan(self, args):
        """Enter plan/editor mode using 2 different models. If no prompt provided, switches to plan/editor mode."""  # noqa
        return self._generic_chat_command(args, "plan")

    def cmd_advise(self, args):
        """Creates an advisor persona based on the question, and gives advice based on that persona. If no persona is found, it creates one."""
        # TODO:
        # [x] 1. Check if the question is empty, return error if it is
        # [x] 3. Ask LLM to identify which persona should answer this question
        #    - Analyze existing persona files in the repository
        #    - Either select an existing persona or suggest a new one with full path
        # [x] 4. If persona file doesn't exist, ask LLM to create it
        #    - Generate detailed persona description
        #    - Save to file in suggested location
        # [x] 5. Read the persona file content
        # [x] 6. Create a prompt that includes the persona and the question
        # [x] 7. Run the prompt through the LLM using ask mode
        # [x] 8. Return the response to the user

        # 1. Check if the question is empty, return error if it is
        if not args.strip():
            self.io.tool_error("Please provide a question for advice (e.g., /advise what would legal think of this code?)")
            return

        advisor_manager = AdvisorManager(self.io, self.coder)

        # Get or create the appropriate persona
        persona_content, persona_type = advisor_manager.get_persona(args)

        if persona_content is None:
            return

        # Generate advice using the persona
        advisor_manager.generate_advice(persona_content, persona_type, args)

        # No need to call _generic_chat_command as we've already added the advice to the chat history
        return

    def cmd_backtrack(self, args):
        "Go back to a previous state when the current approach isn't working"
        from aider.backtrack import BacktrackManager
        
        backtrack_manager = BacktrackManager(self.io, self.coder)
        backtrack_manager.backtrack(args.strip())

    def cmd_prioritize(self, args):
        "Analyze all open issues and determine which one is most important to tackle next"

        # Get the repomap with include_text_and_md=True to ensure all issue files are visible
        if not self.coder.repo_map:
            self.io.tool_error("Repository map is not available. Unable to analyze issues.")
            return

        # Common directories where issues might be stored
        issue_dirs = [
            "issues/",
            "bugs/",
            "tasks/",
            "docs/issues/",
            "documentation/issues/",
            ".github/issues/",
            "todo/",
            "backlog/",
            "features/",
            "enhancements/"
        ]

        # Get all issue files from the repository
        issue_files = []
        if self.coder.repo:
            all_files = self.coder.repo.get_tracked_files()

            # First try to find issues in common directories
            for issue_dir in issue_dirs:
                dir_issues = [f for f in all_files if f.startswith(issue_dir) and f.endswith(".md")]
                issue_files.extend(dir_issues)

            # If no issues found in common directories, ask the LLM to find them
            if not issue_files:
                self.io.tool_output("No issues found in standard directories. Asking LLM to locate issue files...")
                issue_files = self._find_issue_files_with_llm(all_files)

        if not issue_files:
            self.io.tool_error("No issue files found in the repository.")
            return

        self.io.tool_output(f"Analyzing {len(issue_files)} issues to determine priority...")

        # Read the content of each issue file
        issues_data = []
        for issue_file in issue_files:
            abs_path = self.coder.abs_root_path(issue_file)
            content = self.io.read_text(abs_path)
            if content:
                issues_data.append({"file": issue_file, "content": content})

        # Create a prompt for the LLM to evaluate and prioritize issues
        prompt = self._create_prioritize_prompt(issues_data)

        # Get the LLM's response
        messages = [{"role": "user", "content": prompt}]
        response = self.coder.main_model.simple_send_with_retries(messages)

        # Parse the response to identify the chosen issue
        chosen_issue, reasoning = self._parse_prioritize_response(response)

        if not chosen_issue:
            self.io.tool_error("Failed to identify a priority issue from the LLM's response.")
            return

        # Display the chosen issue and reasoning
        self.io.tool_output(f"\nPriority issue: {chosen_issue}")
        self.io.tool_output(f"\nReasoning:\n{reasoning}")

        # Ask the user to confirm focusing on this issue
        if self.io.confirm_ask(f"Would you like to focus on {chosen_issue}?", default="y"):
            # Execute the focus command on the chosen issue
            self.cmd_focus(chosen_issue)

    def cmd_focus(self, args):
        "Focus on a specific file and its related files, dropping others from the chat"

        if not args.strip():
            self.io.tool_error("Please specify a file to focus on.")
            return

        # Parse the filename from args
        filenames = parse_quoted_filenames(args)
        if not filenames:
            self.io.tool_error("Please specify a valid file to focus on.")
            return

        focus_file = filenames[0]

        # Convert to absolute path if needed
        if os.path.isabs(focus_file):
            abs_focus_file = focus_file
            rel_focus_file = self.coder.get_rel_fname(abs_focus_file)
        else:
            rel_focus_file = focus_file
            abs_focus_file = self.coder.abs_root_path(rel_focus_file)

        # Check if the file exists
        if not os.path.exists(abs_focus_file):
            self.io.tool_error(f"File '{focus_file}' not found.")
            return

        # Make sure the focus file is in the chat
        if abs_focus_file not in self.coder.abs_fnames:
            self.coder.abs_fnames.add(abs_focus_file)
            self.io.tool_output(f"Added {rel_focus_file} to the chat.")

        # Get all files in the repo
        all_files = self.coder.get_all_relative_files()

        # Remove the focus file from the list
        other_files = [f for f in all_files if f != rel_focus_file]

        # Ask the LLM which files are related to the focus file
        self.io.tool_output(f"Analyzing relationships for {rel_focus_file}...")
        related_files = self._get_related_files(rel_focus_file, other_files)

        if not related_files:
            self.io.tool_output(f"No related files found for {rel_focus_file}.")
            # Keep only the focus file
            current_files = list(self.coder.abs_fnames)
            for file in current_files:
                rel_file = self.coder.get_rel_fname(file)
                if rel_file != rel_focus_file:
                    self.coder.abs_fnames.remove(file)
                    self.io.tool_output(f"Dropped {rel_file} from the chat.")
            return

        # Drop all files except the focus file
        current_files = list(self.coder.abs_fnames)
        for file in current_files:
            rel_file = self.coder.get_rel_fname(file)
            if rel_file != rel_focus_file and rel_file not in related_files:
                self.coder.abs_fnames.remove(file)
                self.io.tool_output(f"Dropped {rel_file} from the chat.")

        # Add the related files
        for file in related_files:
            if file != rel_focus_file:  # Skip the focus file as it's already added
                abs_file = self.coder.abs_root_path(file)
                if abs_file not in self.coder.abs_fnames:
                    self.coder.abs_fnames.add(abs_file)
                    self.io.tool_output(f"Added related file: {file}")

        self.io.tool_output(f"Now focusing on {rel_focus_file} and {len(related_files)} related files.")

    def _get_related_files(self, focus_file, other_files):
        """
        Ask the LLM to suggest files related to the focus file.
        """
        # Prepare a prompt for the LLM
        prompt = f"""
I want to focus on the file `{focus_file}`. Based on this file, which other files in the repository 
should I include in my context to better understand and work with this file?

Here are all the available files:
{os.linesep.join(['- ' + f for f in other_files[:100]])}  # Limit to 100 files to avoid token limits

RESPOND ONLY WITH A JSON ARRAY of the most relevant files (up to 5) that would help me understand 
and work with `{focus_file}`. For example:
["file1.py", "file2.py"]

Only include files that are directly related to `{focus_file}` in terms of:
1. Imports/dependencies
2. Inheritance relationships
3. Function calls between files
4. Shared data structures
5. Related functionality

If you're not sure about the relationships, make your best guess based on the filenames.
DO NOT include any explanation, just the JSON array.
"""

        # Get the response from the LLM
        try:
            messages = [{"role": "user", "content": prompt}]
            response = self.coder.main_model.simple_send_with_retries(messages)
            # Handle different response formats - could be a dict or a string
            if isinstance(response, dict):
                content = response.get("content", "")
            else:
                content = str(response)

            # Try to extract JSON array from the response
            # First try direct JSON parsing of the entire content
            try:
                # Try parsing the entire response as JSON
                parsed_json = json.loads(content)
                if isinstance(parsed_json, list):
                    related_files = parsed_json
                    # Filter out any files that don't exist
                    related_files = [f for f in related_files if f in other_files]
                    return related_files
            except json.JSONDecodeError:
                # If that fails, try to extract a JSON array using regex
                match = re.search(r'\[.*?\]', content, re.DOTALL)
                if match:
                    json_str = match.group(0)
                    try:
                        related_files = json.loads(json_str)
                        # Filter out any files that don't exist
                        related_files = [f for f in related_files if f in other_files]
                        return related_files
                    except json.JSONDecodeError:
                        self.io.tool_error("Failed to parse the LLM's response as JSON.")
                        return []
                else:
                    self.io.tool_error("The LLM didn't provide a valid JSON response.")
                    return []
        except Exception as e:
            self.io.tool_error(f"Error getting related files: {str(e)}")
            return []
