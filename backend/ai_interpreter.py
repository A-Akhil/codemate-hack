"""
AI Interpreter Module
Handles natural language command interpretation using Google Gemini AI.
"""

import os
import json
import re
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

class AIInterpreter:
    """
    Interprets natural language commands using Google Gemini AI.
    """
    
    def __init__(self):
        # Initialize Gemini AI
        self.api_key = os.environ.get('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY must be set in environment variables")
        
        genai.configure(api_key=self.api_key)
        
        # Initialize the model with the correct model name
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Define the system prompt for command interpretation
        self.system_prompt = """You are a helpful assistant that converts natural language instructions into Linux/Unix terminal commands. 

RULES:
1. Only respond with valid terminal commands that are safe to execute
2. Focus on file operations, text processing, and system monitoring commands
3. Do not generate commands that could be destructive or harmful
4. If a request is unclear or potentially dangerous, respond with an error message
5. Keep commands simple and focused
6. Use relative paths when possible
7. Avoid sudo, rm -rf /, or other potentially dangerous operations

AVAILABLE COMMANDS:
- File operations: ls, pwd, cd, mkdir, rmdir, rm, cp, mv, touch, cat, head, tail, find, stat
- Text operations: echo, grep, wc, sort, diff
- System info: ps, uptime, date, env
- Custom commands: system (shows CPU/memory usage), help, clear, history

RESPONSE FORMAT:
Respond with ONLY the terminal command, no explanations or additional text.
If the request cannot be safely converted to a command, respond with: ERROR: [reason]

EXAMPLES:
Input: "show me all files in the current directory"
Output: ls -la

Input: "create a folder called test"
Output: mkdir test

Input: "copy file1.txt to backup.txt"
Output: cp file1.txt backup.txt

Input: "show system information"
Output: system

Input: "delete everything on the system"
Output: ERROR: Destructive operation not allowed
"""
    
    def interpret(self, natural_language_input: str) -> Dict[str, Any]:
        """
        Interpret natural language input and convert to terminal command.
        
        Args:
            natural_language_input (str): Natural language command description
            
        Returns:
            Dict containing interpretation results
        """
        try:
            # Validate input
            if not natural_language_input.strip():
                return {
                    'success': False,
                    'error': 'Empty input provided'
                }
            
            # Check for potentially dangerous requests first
            if self._is_dangerous_request(natural_language_input):
                return {
                    'success': False,
                    'error': 'Request contains potentially dangerous operations'
                }
            
            # Create the full prompt
            full_prompt = f"{self.system_prompt}\n\nInput: {natural_language_input.strip()}\nOutput:"
            
            # Generate response using Gemini
            response = self.model.generate_content(full_prompt)
            
            if not response or not response.text:
                return {
                    'success': False,
                    'error': 'No response from AI model'
                }
            
            # Parse the response
            ai_output = response.text.strip()
            
            # Check if AI returned an error
            if ai_output.startswith('ERROR:'):
                return {
                    'success': False,
                    'error': ai_output[6:].strip()  # Remove "ERROR:" prefix
                }
            
            # Validate the generated command
            validation_result = self._validate_generated_command(ai_output)
            
            if not validation_result['valid']:
                return {
                    'success': False,
                    'error': f"AI generated invalid command: {validation_result['error']}"
                }
            
            return {
                'success': True,
                'command': ai_output,
                'original_input': natural_language_input,
                'confidence': self._estimate_confidence(natural_language_input, ai_output)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'AI interpretation failed: {str(e)}'
            }
    
    def _is_dangerous_request(self, input_text: str) -> bool:
        """
        Check if the input contains dangerous keywords or patterns.
        
        Args:
            input_text (str): Input text to check
            
        Returns:
            bool: True if potentially dangerous
        """
        dangerous_patterns = [
            r'delete\s+everything',
            r'format\s+disk',
            r'wipe\s+system',
            r'remove\s+all',
            r'destroy\s+',
            r'hack\s+',
            r'password\s+',
            r'sudo\s+',
            r'root\s+access',
            r'system\s+shutdown',
            r'kill\s+all',
            r'format\s+drive'
        ]
        
        input_lower = input_text.lower()
        
        for pattern in dangerous_patterns:
            if re.search(pattern, input_lower):
                return True
        
        return False
    
    def _validate_generated_command(self, command: str) -> Dict[str, Any]:
        """
        Validate that the AI-generated command is safe and valid.
        
        Args:
            command (str): Generated command to validate
            
        Returns:
            Dict containing validation results
        """
        # Define allowed commands
        allowed_commands = {
            'ls', 'pwd', 'cd', 'mkdir', 'rmdir', 'rm', 'cp', 'mv', 'touch',
            'cat', 'head', 'tail', 'find', 'stat', 'echo', 'grep', 'wc',
            'sort', 'diff', 'ps', 'uptime', 'date', 'env', 'system',
            'help', 'clear', 'history'
        }
        
        # Parse command
        command_parts = command.strip().split()
        if not command_parts:
            return {
                'valid': False,
                'error': 'Empty command'
            }
        
        main_command = command_parts[0]
        
        # Check if command is allowed
        if main_command not in allowed_commands:
            return {
                'valid': False,
                'error': f'Command not allowed: {main_command}'
            }
        
        # Check for dangerous patterns in the full command
        dangerous_patterns = [
            r'rm\s+-rf\s+/',
            r'rm\s+-rf\s+\*',
            r'sudo\s+',
            r'su\s+',
            r'chmod\s+777',
            r'/dev/null',
            r'&\s*$',
            r'\|\s*sh',
            r'`.*`',
            r'\$\(',
            r'>\s*/dev/',
            r'2>&1',
            r'\|\s*bash'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, command):
                return {
                    'valid': False,
                    'error': f'Dangerous pattern detected: {pattern}'
                }
        
        # Additional validation for rm command
        if main_command == 'rm':
            # Don't allow rm without specific file/directory
            if len(command_parts) < 2:
                return {
                    'valid': False,
                    'error': 'rm command requires specific target'
                }
            
            # Check for dangerous rm patterns
            for arg in command_parts[1:]:
                if arg in ['/', '*', '/*', '~', '~/*']:
                    return {
                        'valid': False,
                        'error': f'Dangerous rm target: {arg}'
                    }
        
        return {
            'valid': True,
            'command': main_command,
            'args': command_parts[1:]
        }
    
    def _estimate_confidence(self, input_text: str, generated_command: str) -> float:
        """
        Estimate confidence in the AI interpretation.
        
        Args:
            input_text (str): Original natural language input
            generated_command (str): Generated command
            
        Returns:
            float: Confidence score between 0 and 1
        """
        confidence = 0.5  # Base confidence
        
        # Increase confidence for clear, common patterns
        clear_patterns = [
            (r'list\s+(files|directory|contents)', ['ls'], 0.3),
            (r'show\s+(files|directory)', ['ls'], 0.3),
            (r'create\s+(folder|directory)', ['mkdir'], 0.3),
            (r'make\s+(folder|directory)', ['mkdir'], 0.3),
            (r'copy\s+\w+\s+to\s+\w+', ['cp'], 0.3),
            (r'move\s+\w+\s+to\s+\w+', ['mv'], 0.3),
            (r'show\s+(contents?|text)\s+of', ['cat'], 0.3),
            (r'display\s+(contents?|text)', ['cat'], 0.3),
            (r'current\s+directory', ['pwd'], 0.3),
            (r'where\s+am\s+i', ['pwd'], 0.3),
            (r'system\s+(info|information)', ['system'], 0.3),
            (r'help|commands', ['help'], 0.3)
        ]
        
        input_lower = input_text.lower()
        command_parts = generated_command.split()
        
        for pattern, expected_commands, boost in clear_patterns:
            if re.search(pattern, input_lower):
                if command_parts and command_parts[0] in expected_commands:
                    confidence += boost
                break
        
        # Decrease confidence for complex or unusual requests
        if len(input_text.split()) > 10:
            confidence -= 0.1
        
        # Decrease confidence for generated commands with many arguments
        if len(command_parts) > 5:
            confidence -= 0.1
        
        # Ensure confidence is between 0 and 1
        return max(0.0, min(1.0, confidence))
    
    def get_command_suggestions(self, partial_input: str) -> List[Dict[str, Any]]:
        """
        Get command suggestions based on partial natural language input.
        
        Args:
            partial_input (str): Partial input text
            
        Returns:
            List of suggested commands with descriptions
        """
        suggestions = []
        
        # Define common command patterns and their suggestions
        patterns = [
            {
                'keywords': ['list', 'show', 'display', 'files', 'directory'],
                'command': 'ls',
                'description': 'List directory contents',
                'examples': ['ls', 'ls -la', 'ls /path/to/directory']
            },
            {
                'keywords': ['create', 'make', 'folder', 'directory'],
                'command': 'mkdir',
                'description': 'Create directory',
                'examples': ['mkdir foldername', 'mkdir -p path/to/folder']
            },
            {
                'keywords': ['copy', 'duplicate'],
                'command': 'cp',
                'description': 'Copy files or directories',
                'examples': ['cp source.txt dest.txt', 'cp -r folder1 folder2']
            },
            {
                'keywords': ['move', 'rename'],
                'command': 'mv',
                'description': 'Move or rename files',
                'examples': ['mv old.txt new.txt', 'mv file.txt /path/to/']
            },
            {
                'keywords': ['remove', 'delete'],
                'command': 'rm',
                'description': 'Remove files or directories',
                'examples': ['rm file.txt', 'rm -r directory']
            },
            {
                'keywords': ['content', 'read', 'text'],
                'command': 'cat',
                'description': 'Display file contents',
                'examples': ['cat file.txt', 'cat *.txt']
            },
            {
                'keywords': ['where', 'current', 'location'],
                'command': 'pwd',
                'description': 'Show current directory',
                'examples': ['pwd']
            },
            {
                'keywords': ['system', 'monitor', 'performance'],
                'command': 'system',
                'description': 'Show system information',
                'examples': ['system']
            }
        ]
        
        input_lower = partial_input.lower()
        
        for pattern in patterns:
            # Check if any keywords match the input
            if any(keyword in input_lower for keyword in pattern['keywords']):
                suggestions.append({
                    'command': pattern['command'],
                    'description': pattern['description'],
                    'examples': pattern['examples'],
                    'relevance': self._calculate_relevance(input_lower, pattern['keywords'])
                })
        
        # Sort by relevance
        suggestions.sort(key=lambda x: x['relevance'], reverse=True)
        
        return suggestions[:5]  # Return top 5 suggestions
    
    def _calculate_relevance(self, input_text: str, keywords: List[str]) -> float:
        """
        Calculate relevance score for a suggestion.
        
        Args:
            input_text (str): Input text
            keywords (List[str]): Keywords for the suggestion
            
        Returns:
            float: Relevance score
        """
        score = 0.0
        words = input_text.split()
        
        for keyword in keywords:
            if keyword in input_text:
                # Exact keyword match
                score += 1.0
                
                # Bonus for keyword at start of input
                if input_text.startswith(keyword):
                    score += 0.5
        
        # Normalize by number of words in input
        if words:
            score = score / len(words)
        
        return score
    
    def explain_command(self, command: str) -> Dict[str, Any]:
        """
        Explain what a terminal command does in natural language.
        
        Args:
            command (str): Terminal command to explain
            
        Returns:
            Dict containing explanation
        """
        try:
            explain_prompt = f"""Explain what this terminal command does in simple, clear language:

Command: {command}

Provide a brief explanation of:
1. What the command does
2. What the arguments mean (if any)
3. What the expected output would be

Keep the explanation concise and user-friendly."""
            
            response = self.model.generate_content(explain_prompt)
            
            if response and response.text:
                return {
                    'success': True,
                    'explanation': response.text.strip(),
                    'command': command
                }
            else:
                return {
                    'success': False,
                    'error': 'Could not generate explanation'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to explain command: {str(e)}'
            }