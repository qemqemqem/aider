class AdvancedCommandsMixin:
    """Mixin class providing advanced commands."""

    def cmd_document(self, args):
        """Enter document/editor mode using 2 different models. If no prompt provided, switches to document/editor mode."""  # noqa
        return self._generic_chat_command(args, "document")

    def completions_document(self):
        files = set(self.coder.get_all_relative_files())
        files = files - set(self.coder.get_inchat_relative_files())
        files = [self.quote_fname(fn) for fn in files]
        return files

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

        if not self.coder.repo:
            self.io.tool_error("No git repository found.")
            return

        # Get the user's query about what to backtrack from
        query = args.strip()
        if not query:
            self.io.tool_error("Please describe what you want to backtrack from.")
            self.io.tool_output("Example: /backtrack the login system changes")
            self.io.tool_output("Example: /backtrack before we started using React")
            return

        # Get full commit history
        try:
            # Get all commits, but limit to a reasonable number to avoid token limits
            commits = list(self.coder.repo.repo.iter_commits(max_count=50))
        except ANY_GIT_ERROR as err:
            self.io.tool_error(f"Unable to retrieve git history: {err}")
            return

        if not commits:
            self.io.tool_error("No commits found in the repository.")
            return

        # Inform the user we're analyzing the history
        self.io.tool_output(f"Analyzing git history to find where to backtrack...")

        # Create a prompt for the LLM to analyze commit history
        commit_info = []
        for commit in commits:
            commit_info.append({
                "hash": commit.hexsha,
                "short_hash": commit.hexsha[:7],
                "message": commit.message.strip(),
                "date": commit.committed_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                "files_changed": [item for item in commit.stats.files]
            })

        prompt = f"""
The user has this request to backtrack. The user feels that the code has gotten messed up, and we need to go back to a previous state, by reverting changes in git. 

User Request to Backtrack: {query}

Analyze these git commits and identify the best commit to revert to.

Commits (from newest to oldest):
"""

        for i, info in enumerate(commit_info):
            prompt += f"\n{i + 1}. {info['short_hash']} ({info['date']}): {info['message']}\n"
            prompt += f"   Files changed: {', '.join(info['files_changed'][:5])}"
            if len(info['files_changed']) > 5:
                prompt += f" and {len(info['files_changed']) - 5} more"
            prompt += "\n"

        prompt += f"""
Consider the user's request to backtrack. Consider what they want to undo, and what changes they seem to be unhappy about.

User Request to Backtrack: {query}

Now, determine which commit we should revert to.

Respond with a JSON object containing:
1. "target_commit": The hash of the commit we should revert to
2. "related_commits": Array of hashes of commits related to what the user wants to backtrack from
3. "explanation": Brief explanation of your reasoning
4. "summary": A summary of what was attempted and why it didn't work. This is going to be used as a post-mortem for the failed attempt, so be as detailed as you can. Explain what was tried, and explain what went wrong, as best as you can tell.

Example response:
{{
  "target_commit": "abc1234",
  "related_commits": ["def5678", "ghi9012"],
  "explanation": "We should revert to abc1234 because it's the commit right before the changes related to the user's query.",
  "summary": "The attempt to implement X encountered problems with Y and Z."
}}
"""

        # Get the LLM's analysis
        messages = [{"role": "user", "content": prompt}]
        response = self.coder.main_model.simple_send_with_retries(messages)

        if isinstance(response, dict):
            content = response.get("content", "")
        else:
            content = str(response)

        # Extract JSON from the response

        json_match = re.search(r'```json\n(.*?)\n```|(\{.*\})', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1) or json_match.group(2)
            try:
                analysis = json.loads(json_str)
            except json.JSONDecodeError:
                self.io.tool_error("Failed to parse LLM response as JSON.")
                return
        else:
            self.io.tool_error("LLM did not provide a valid JSON response.")
            return

        target_commit = analysis.get("target_commit")
        if not target_commit:
            self.io.tool_error("Could not identify a target commit to revert to.")
            return

        # Verify the target commit exists
        try:
            commit_obj = self.coder.repo.repo.commit(target_commit)
        except ANY_GIT_ERROR:
            self.io.tool_error(f"Target commit {target_commit} not found in repository.")
            return

        # Create a summary of the failed attempt
        summary = analysis.get("summary", "Attempted approach encountered issues.")
        explanation = analysis.get("explanation", "")

        # Create a detailed report of the failed attempt using the template
        failed_attempt_template = """# Failed Attempt

## Query
{query}

## Summary
{summary}

## Explanation
{explanation}

## Commits Involved
{commits_list}

## Date
{date}

## Conversation Context
The following conversation led to this backtracking:
{conversation}
"""

        # Build the commits list
        commits_list = ""
        for commit_hash in analysis.get("feature_commits", []):
            try:
                commit = self.coder.repo.repo.commit(commit_hash)
                commits_list += f"- {commit.hexsha[:7]}: {commit.message.strip()}\n"
            except ANY_GIT_ERROR:
                continue

        # Build the conversation context
        conversation = ""
        all_messages = self.coder.done_messages + self.coder.cur_messages
        for msg in all_messages[-10:]:  # Last 10 messages
            if msg["role"] == "user":
                conversation += f"\n### User\n{msg['content']}\n"
            elif msg["role"] == "assistant":
                conversation += f"\n### Assistant\n{msg['content']}\n"

        # Format the template with all the data
        failed_attempt_report = failed_attempt_template.format(
            query=query,
            summary=summary,
            explanation=explanation,
            commits_list=commits_list,
            date=commits[0].committed_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            conversation=conversation
        )

        # Add recent conversation context
        all_messages = self.coder.done_messages + self.coder.cur_messages
        for msg in all_messages[-10:]:  # Last 10 messages
            if msg["role"] == "user":
                failed_attempt_report += f"\n### User\n{msg['content']}\n"
            elif msg["role"] == "assistant":
                failed_attempt_report += f"\n### Assistant\n{msg['content']}\n"

        # Ask for confirmation with clear warning about git reset --hard
        self.io.tool_output(f"Found target commit: {commit_obj.hexsha[:7]} - {commit_obj.message.strip()}")
        self.io.tool_output("\nThe following commits will be lost:")

        # List the commits that will be lost (commits between HEAD and target_commit)
        try:
            lost_commits = list(self.coder.repo.repo.iter_commits(f"{target_commit}..HEAD"))
            if lost_commits:
                for commit in lost_commits:
                    self.io.tool_output(f"  • {commit.hexsha[:7]} - {commit.message.strip().split('\n')[0]}")
            else:
                self.io.tool_output("  (No commits will be lost)")
        except ANY_GIT_ERROR as err:
            self.io.tool_output("  (Unable to list commits that will be lost)")

        self.io.tool_output(f"\nSummary of failed attempt: \n{summary}")
        self.io.tool_output("\nWARNING: This will use 'git reset --hard' which will:")
        self.io.tool_output("  1. Discard ALL uncommitted changes")
        self.io.tool_output("  2. Reset your working directory to the state at the target commit")
        self.io.tool_output("  3. Lose any work not committed to git")

        if not self.io.confirm_ask(f"Do you want to backtrack to commit {commit_obj.hexsha[:7]}?", default="n"):
            self.io.tool_output("Backtracking cancelled.")
            return

        # Create the failed_attempts directory if it doesn't exist
        failed_attempts_dir = os.path.join(self.coder.root, "failed_attempts")
        os.makedirs(failed_attempts_dir, exist_ok=True)

        # Save the failed attempt report
        timestamp = commits[0].committed_datetime.strftime("%Y%m%d_%H%M%S")
        # Create a safe filename from the first few words of the query
        query_words = re.sub(r'[^\w\s\-]', '', query).split()[:3]
        safe_query = '_'.join(query_words) if query_words else 'backtrack'
        report_filename = f"{timestamp}_{safe_query}.md"
        report_path = os.path.join(failed_attempts_dir, report_filename)

        with open(report_path, "w", encoding=self.io.encoding) as f:
            f.write(failed_attempt_report)

        # Perform the git revert
        try:
            # Reset to the target commit
            self.coder.repo.repo.git.reset("--hard", target_commit)

            self.io.tool_output(f"Successfully backtracked to commit {commit_obj.hexsha[:7]}.")
            self.io.tool_output(f"Saved failed attempt documentation to: {report_path}")

            # Add a message to the chat history about the backtracking
            backtrack_msg = f"""I've backtracked to commit {commit_obj.hexsha[:7]} based on your request.

A record of this failed attempt has been saved to: {report_path}

Summary of what didn't work:
{summary}

We can now try a different approach.
"""

            self.coder.cur_messages += [
                dict(role="user", content=f"This approach isn't working. Let's go back and try something else: {query}"),
                dict(role="assistant", content=backtrack_msg),
            ]

        except ANY_GIT_ERROR as err:
            self.io.tool_error(f"Failed to backtrack: {err}")
            self.io.tool_output("The failed attempt documentation was still saved to: {report_path}")

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
