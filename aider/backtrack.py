import json
import os
import re
from datetime import datetime

class BacktrackManager:
    """Manages the backtracking functionality to revert to previous git commits."""

    def __init__(self, io, coder):
        self.io = io
        self.coder = coder
        # Use the ANY_GIT_ERROR from the commands_advanced module
        from aider.commands_advanced import AdvancedCommandsMixin
        self.ANY_GIT_ERROR = AdvancedCommandsMixin.ANY_GIT_ERROR

    def backtrack(self, query):
        """
        Main method to handle backtracking to a previous git commit.
        
        Args:
            query: User's description of what to backtrack from
            
        Returns:
            bool: True if backtracking was successful, False otherwise
        """
        if not self.coder.repo:
            self.io.tool_error("No git repository found.")
            return False

        # Validate query
        if not query:
            self.io.tool_error("Please describe what you want to backtrack from.")
            self.io.tool_output("Example: /backtrack the login system changes")
            self.io.tool_output("Example: /backtrack before we started using React")
            return False

        # Get commit history
        try:
            # Get all commits, but limit to a reasonable number to avoid token limits
            commits = list(self.coder.repo.repo.iter_commits(max_count=50))
        except self.ANY_GIT_ERROR as err:
            self.io.tool_error(f"Unable to retrieve git history: {err}")
            return False

        if not commits:
            self.io.tool_error("No commits found in the repository.")
            return False

        # Inform the user we're analyzing the history
        self.io.tool_output(f"Analyzing git history to find where to backtrack...")

        # Analyze commit history
        analysis = self._analyze_commit_history(commits, query)
        if not analysis:
            return False

        target_commit = analysis.get("target_commit")
        if not target_commit:
            self.io.tool_error("Could not identify a target commit to revert to.")
            return False

        # Verify the target commit exists
        try:
            commit_obj = self.coder.repo.repo.commit(target_commit)
        except self.ANY_GIT_ERROR:
            self.io.tool_error(f"Target commit {target_commit} not found in repository.")
            return False

        # Get summary and explanation
        summary = analysis.get("summary", "Attempted approach encountered issues.")
        explanation = analysis.get("explanation", "")

        # Show information and ask for confirmation
        return self._confirm_and_execute_backtrack(
            commit_obj, target_commit, summary, explanation, 
            analysis.get("related_commits", []), query, commits
        )

    def _analyze_commit_history(self, commits, query):
        """
        Analyze commit history to find the best commit to backtrack to.
        
        Args:
            commits: List of git commits
            query: User's description of what to backtrack from
            
        Returns:
            dict: Analysis results including target commit and explanation
        """
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
                return json.loads(json_str)
            except json.JSONDecodeError:
                self.io.tool_error("Failed to parse LLM response as JSON.")
                return None
        else:
            self.io.tool_error("LLM did not provide a valid JSON response.")
            return None

    def _confirm_and_execute_backtrack(self, commit_obj, target_commit, summary, explanation, 
                                      related_commits, query, commits):
        """
        Show information about the backtrack operation and ask for confirmation.
        If confirmed, execute the backtrack.
        
        Returns:
            bool: True if backtracking was successful, False otherwise
        """
        # Show target commit info
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
        except self.ANY_GIT_ERROR as err:
            self.io.tool_output("  (Unable to list commits that will be lost)")

        # Show summary and warnings
        self.io.tool_output(f"\nSummary of failed attempt: \n{summary}")
        self.io.tool_output("\nWARNING: This will use 'git reset --hard' which will:")
        self.io.tool_output("  1. Discard ALL uncommitted changes")
        self.io.tool_output("  2. Reset your working directory to the state at the target commit")
        self.io.tool_output("  3. Lose any work not committed to git")

        # Ask for confirmation
        if not self.io.confirm_ask(f"Do you want to backtrack to commit {commit_obj.hexsha[:7]}?", default="n"):
            self.io.tool_output("Backtracking cancelled.")
            return False

        # Create documentation and execute backtrack
        return self._execute_backtrack(commit_obj, target_commit, summary, explanation, 
                                      related_commits, query, commits)

    def _execute_backtrack(self, commit_obj, target_commit, summary, explanation, 
                          related_commits, query, commits):
        """
        Execute the backtrack operation and create documentation.
        
        Returns:
            bool: True if backtracking was successful, False otherwise
        """
        # Create the failed attempt report
        failed_attempt_report = self._create_failed_attempt_report(
            query, summary, explanation, related_commits, commits
        )

        # Create the failed_attempts directory if it doesn't exist
        failed_attempts_dir = os.path.join(self.coder.root, "failed_attempts")
        os.makedirs(failed_attempts_dir, exist_ok=True)

        # Save the failed attempt report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Create a safe filename from the first few words of the query
        query_words = re.sub(r'[^\w\s\-]', '', query).split()[:3]
        safe_query = '_'.join(query_words) if query_words else 'backtrack'
        report_filename = f"{timestamp}_{safe_query}.md"
        report_path = os.path.join(failed_attempts_dir, report_filename)

        with open(report_path, "w", encoding=self.io.encoding) as f:
            f.write(failed_attempt_report)

        # Perform the git reset
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
            
            return True

        except self.ANY_GIT_ERROR as err:
            self.io.tool_error(f"Failed to backtrack: {err}")
            self.io.tool_output(f"The failed attempt documentation was still saved to: {report_path}")
            return False

    def _create_failed_attempt_report(self, query, summary, explanation, related_commits, commits):
        """
        Create a detailed report of the failed attempt.
        
        Returns:
            str: The formatted report
        """
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
        for commit_hash in related_commits:
            try:
                commit = self.coder.repo.repo.commit(commit_hash)
                commits_list += f"- {commit.hexsha[:7]}: {commit.message.strip()}\n"
            except self.ANY_GIT_ERROR:
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
        return failed_attempt_template.format(
            query=query,
            summary=summary,
            explanation=explanation,
            commits_list=commits_list,
            date=commits[0].committed_datetime.strftime("%Y-%m-%d %H:%M:%S"),
            conversation=conversation
        )
