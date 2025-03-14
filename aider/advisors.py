import json
import os
import re
from pathlib import Path


class AdvisorManager:
    """Manages advisor personas for providing specialized advice."""

    def __init__(self, io, coder):
        """Initialize the advisor manager.
        
        Args:
            io: The input/output interface
            coder: The coder instance
        """
        self.io = io
        self.coder = coder

    def identify_persona(self, question):
        """Identify which advisor persona should answer the question.
        
        Args:
            question: The user's question
            
        Returns:
            A tuple of (persona_type, existing_file, suggested_file, reasoning)
        """
        self.io.tool_output("Analyzing your question to find the right advisor persona...")
        
        # Create a prompt to ask the LLM to identify or suggest a persona
        prompt = f"""
I need to identify which advisor persona would be best suited to answer this question:

"{question}"

Please analyze the repository structure and suggest either:
1. An existing file in the repository that contains a suitable advisor persona, or
2. A new file path and name for creating a persona that would be appropriate for this question.

Your response should be in JSON format:
{{
  "persona_type": "string", // A short name for the type of advisor (e.g., "legal", "security", "performance")
  "existing_file": "string or null", // Full path to existing file if found, or null if none exists
  "suggested_file": "string or null", // Suggested full path for a new file if no existing file is appropriate
  "reasoning": "string" // Brief explanation of your choice
}}

Only return valid JSON that can be parsed. Do not include any other text in your response.
"""
        
        # Get the repository map to help the LLM understand the codebase structure
        repo_map = self.coder.get_repo_map()
        
        # Create a temporary coder to ask this question
        from aider.coders.base_coder import Coder
        
        persona_coder = Coder.create(
            io=self.io,
            from_coder=self.coder,
            edit_format="ask",
            summarize_from_coder=False,
        )
        
        # Add the prompt to the messages
        persona_coder.cur_messages.append({"role": "user", "content": prompt})
        
        # Run the LLM to get the response
        response = persona_coder.main_model.simple_send_with_retries(persona_coder.cur_messages)
        
        # Extract the content from the response
        if isinstance(response, dict):
            content = response.get("content", "")
        else:
            content = str(response)
        
        # Try to parse the JSON response
        try:
            # First try direct JSON parsing
            persona_info = json.loads(content)
        except json.JSONDecodeError:
            # If that fails, try to extract JSON using regex
            match = re.search(r'({.*})', content, re.DOTALL)
            if match:
                try:
                    persona_info = json.loads(match.group(1))
                except json.JSONDecodeError:
                    self.io.tool_error("Failed to parse the LLM's response about the persona.")
                    return None, None, None, None
            else:
                self.io.tool_error("The LLM didn't provide a valid JSON response about the persona.")
                return None, None, None, None
        
        # Extract the persona information
        persona_type = persona_info.get("persona_type", "advisor")
        existing_file = persona_info.get("existing_file")
        suggested_file = persona_info.get("suggested_file")
        reasoning = persona_info.get("reasoning", "")
        
        return persona_type, existing_file, suggested_file, reasoning

    def create_persona(self, persona_type, file_path, question):
        """Create a new persona file if it doesn't exist.
        
        Args:
            persona_type: The type of advisor persona
            file_path: The path where the persona file should be created
            question: The original question to help generate the persona
            
        Returns:
            The content of the persona file
        """
        self.io.tool_output(f"Creating new {persona_type} advisor persona...")
        
        # Create a prompt to generate the persona
        prompt = f"""
I need to create a detailed advisor persona for a {persona_type} expert who will answer questions about code.

The first question this persona will answer is:
"{question}"

Please create a detailed description of this persona including:
1. Background and expertise
2. Perspective and approach to problems
3. Key principles they follow
4. Tone and communication style
5. Areas of special focus within their domain

The description should be comprehensive enough to guide consistent advice-giving in the persona's voice.
"""
        
        # Create a temporary coder to ask this question
        from aider.coders.base_coder import Coder
        
        persona_coder = Coder.create(
            io=self.io,
            from_coder=self.coder,
            edit_format="ask",
            summarize_from_coder=False,
        )
        
        # Add the prompt to the messages
        persona_coder.cur_messages.append({"role": "user", "content": prompt})
        
        # Run the LLM to get the response
        response = persona_coder.main_model.simple_send_with_retries(persona_coder.cur_messages)
        
        # Extract the content from the response
        if isinstance(response, dict):
            content = response.get("content", "")
        else:
            content = str(response)
        
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Write the persona to the file
        with open(file_path, 'w') as f:
            f.write(f"# {persona_type.title()} Advisor Persona\n\n")
            f.write(content)
        
        self.io.tool_output(f"Created new persona file at: {file_path}")
        
        return content

    def get_persona_content(self, file_path):
        """Read the content of an existing persona file.
        
        Args:
            file_path: The path to the persona file
            
        Returns:
            The content of the persona file
        """
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            return content
        except FileNotFoundError:
            self.io.tool_error(f"Persona file not found: {file_path}")
            return None
        except Exception as e:
            self.io.tool_error(f"Error reading persona file: {e}")
            return None

    def create_advice_prompt(self, persona_content, question):
        """Create a prompt that includes the persona and the question.
        
        Args:
            persona_content: The content of the persona file
            question: The user's question
            
        Returns:
            A prompt for the LLM
        """
        prompt = f"""
You are an advisor with the following persona:

{persona_content}

Please answer this question from the perspective of your persona:

{question}

Provide a thoughtful, detailed response that reflects your expertise and perspective as described in your persona.
"""
        return prompt
        
    def generate_advice(self, persona_content, persona_type, question):
        """Generate advice using the persona.
        
        Args:
            persona_content: The content of the persona file
            persona_type: The type of advisor persona
            question: The user's question
            
        Returns:
            The advice from the persona, or None if there was an error
        """
        self.io.tool_output(f"Generating advice from the {persona_type} advisor persona...")
        
        # Create a prompt that includes the persona and the question
        advice_prompt = self.create_advice_prompt(persona_content, question)
        
        # Create a temporary coder to ask this question
        from aider.coders.base_coder import Coder
        
        advice_coder = Coder.create(
            io=self.io,
            from_coder=self.coder,
            edit_format="ask",
            summarize_from_coder=False,
        )
        
        # Add the prompt to the messages
        advice_coder.cur_messages.append({"role": "user", "content": advice_prompt})
        
        # Run the LLM to get the advice
        response = advice_coder.main_model.simple_send_with_retries(advice_coder.cur_messages)
        
        # Extract the content from the response
        if isinstance(response, dict):
            advice = response.get("content", "")
        else:
            advice = str(response)
        
        # Add the advice to the chat history
        self.coder.cur_messages += [
            {"role": "user", "content": f"Advice from {persona_type} advisor persona:\n\n{advice}"},
            {"role": "assistant", "content": "I've provided advice based on the requested persona."}
        ]
        
        return advice

    def get_persona(self, question):
        """Get or create a persona for the given question.
        
        Args:
            question: The user's question
            
        Returns:
            A tuple of (persona_content, persona_type) or (None, None) if there was an error
        """
        # Identify which persona should answer this question
        persona_type, existing_file, suggested_file, reasoning = self.identify_persona(question)
        
        if not (existing_file or suggested_file):
            self.io.tool_error("The LLM couldn't identify or suggest a persona file.")
            return None, None
        
        # Get or create the persona content
        if existing_file:
            self.io.tool_output(f"Found suitable {persona_type} advisor persona in: {existing_file}")
            self.io.tool_output(f"Reasoning: {reasoning}")
            persona_content = self.get_persona_content(existing_file)
            if not persona_content:
                return None, None
        else:
            self.io.tool_output(f"No existing {persona_type} advisor persona found.")
            self.io.tool_output(f"Suggested creating new persona at: {suggested_file}")
            self.io.tool_output(f"Reasoning: {reasoning}")
            
            # Confirm with the user before creating a new persona file
            if not self.io.confirm_ask(f"Create new {persona_type} advisor persona?", default="y"):
                self.io.tool_output("Persona creation cancelled.")
                return None, None
                
            persona_content = self.create_persona(persona_type, suggested_file, question)
            if not persona_content:
                return None, None
        
        return persona_content, persona_type
