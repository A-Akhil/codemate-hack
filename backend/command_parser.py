"""
Command Parser Module
Handles parsing of user input to determine command type and arguments.
"""

import re
import shlex
from typing import Dict, List, Any

class CommandParser:
    """
    Parses user input and determines if it's a direct command or natural language.
    """
    
    def __init__(self):
        # Define known terminal commands
        self.terminal_commands = {
            # File operations
            'ls', 'pwd', 'cd', 'mkdir', 'rmdir', 'rm', 'cp', 'mv', 'touch',
            'cat', 'head', 'tail', 'find', 'tree', 'stat',
            
            # Text operations
            'echo', 'grep', 'wc', 'sort', 'diff', 'sed', 'awk',
            
            # System monitoring
            'system', 'top', 'ps', 'uptime', 'disk', 'net', 'who', 'env',
            
            # Network commands
            'ping', 'curl', 'wget', 'nslookup', 'ifconfig', 'ip', 'traceroute',
            
            # Process management
            'kill', 'killall', 'bg', 'fg',
            
            # Package management
            'pip',
            
            # Utility commands
            'history', 'clear', 'date', 'cal', 'alias', 'exit', 'quit', 'help'
        }
        
        # Patterns for natural language detection
        self.natural_language_patterns = [
            r'^(create|make|build)\s+',
            r'^(show|display|list)\s+',
            r'^(copy|move|delete|remove)\s+',
            r'^(find|search|locate)\s+',
            r'^(how|what|where|when|why)\s+',
            r'^(can you|could you|please)\s+',
            r'\s+(please|for me|help)\s*$'
        ]
    
    def parse(self, user_input: str) -> Dict[str, Any]:
        """
        Parse user input and return structured command information.
        
        Args:
            user_input (str): Raw user input
            
        Returns:
            Dict containing parsed command information
        """
        user_input = user_input.strip()
        
        if not user_input:
            return {
                'type': 'empty',
                'command': '',
                'args': [],
                'original': user_input
            }
        
        # Check if it's a direct terminal command
        if self._is_terminal_command(user_input):
            return self._parse_terminal_command(user_input)
        
        # Check if it's natural language
        if self._is_natural_language(user_input):
            return {
                'type': 'natural_language',
                'command': user_input,
                'args': [],
                'original': user_input
            }
        
        # Default: treat as potential terminal command
        return self._parse_terminal_command(user_input)
    
    def _is_terminal_command(self, user_input: str) -> bool:
        """
        Check if the input starts with a known terminal command.
        
        Args:
            user_input (str): User input to check
            
        Returns:
            bool: True if it's a terminal command
        """
        try:
            # Split the input into tokens
            tokens = shlex.split(user_input)
            if not tokens:
                return False
            
            # Check if the first token is a known command
            command = tokens[0].lower()
            return command in self.terminal_commands
        except ValueError:
            # Handle shell parsing errors (unmatched quotes, etc.)
            return False
    
    def _is_natural_language(self, user_input: str) -> bool:
        """
        Check if the input appears to be natural language.
        
        Args:
            user_input (str): User input to check
            
        Returns:
            bool: True if it appears to be natural language
        """
        user_input_lower = user_input.lower()
        
        # Check against natural language patterns
        for pattern in self.natural_language_patterns:
            if re.search(pattern, user_input_lower):
                return True
        
        # Check for question words
        question_words = ['how', 'what', 'where', 'when', 'why', 'which', 'who']
        if any(user_input_lower.startswith(word) for word in question_words):
            return True
        
        # Check for sentence-like structure (multiple words with spaces)
        words = user_input.split()
        if len(words) > 3 and not self._is_terminal_command(user_input):
            return True
        
        return False
    
    def _parse_terminal_command(self, user_input: str) -> Dict[str, Any]:
        """
        Parse a terminal command into command and arguments.
        
        Args:
            user_input (str): Terminal command input
            
        Returns:
            Dict containing parsed command information
        """
        try:
            # Use shlex to properly handle quoted arguments
            tokens = shlex.split(user_input)
            if not tokens:
                return {
                    'type': 'empty',
                    'command': '',
                    'args': [],
                    'original': user_input
                }
            
            command = tokens[0]
            args = tokens[1:] if len(tokens) > 1 else []
            
            return {
                'type': 'terminal_command',
                'command': command,
                'args': args,
                'original': user_input
            }
        
        except ValueError as e:
            # Handle shell parsing errors
            return {
                'type': 'parse_error',
                'command': user_input,
                'args': [],
                'original': user_input,
                'error': str(e)
            }
    
    def validate_command(self, command: str) -> Dict[str, Any]:
        """
        Validate a command for security and correctness.
        
        Args:
            command (str): Command to validate
            
        Returns:
            Dict containing validation results
        """
        validation_result = {
            'valid': True,
            'warnings': [],
            'errors': []
        }
        
        # Check for potentially dangerous commands
        dangerous_patterns = [
            r'rm\s+-rf\s+/',  # rm -rf /
            r'sudo\s+',       # sudo commands
            r'su\s+',         # su commands
            r'chmod\s+777',   # dangerous chmod
            r'>/dev/null',    # output redirection
            r'&\s*$',         # background processes
            r'\|\s*sh',       # piping to shell
            r'`.*`',          # command substitution
            r'\$\(',          # command substitution
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                validation_result['warnings'].append(
                    f"Potentially dangerous pattern detected: {pattern}"
                )
        
        # Check for path traversal attempts
        if '../' in command or '/..' in command:
            validation_result['warnings'].append(
                "Path traversal attempt detected"
            )
        
        # Check for network access attempts
        network_patterns = [r'curl\s+', r'wget\s+', r'nc\s+', r'netcat\s+']
        for pattern in network_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                validation_result['warnings'].append(
                    "Network access command detected"
                )
        
        return validation_result
    
    def get_command_help(self, command: str) -> str:
        """
        Get help text for a specific command.
        
        Args:
            command (str): Command to get help for
            
        Returns:
            str: Help text for the command
        """
        help_texts = {
            'help': 'Display available commands and usage information',
            'ls': 'List directory contents. Usage: ls [options] [directory]',
            'pwd': 'Print current working directory',
            'cd': 'Change directory. Usage: cd [directory]',
            'mkdir': 'Create directory. Usage: mkdir <directory_name>',
            'rm': 'Remove files or directories. Usage: rm [options] <file/directory>',
            'cp': 'Copy files or directories. Usage: cp <source> <destination>',
            'mv': 'Move/rename files or directories. Usage: mv <source> <destination>',
            'cat': 'Display file contents. Usage: cat <filename>',
            'echo': 'Display text. Usage: echo <text>',
            'system': 'Show system information including CPU, memory, and processes',
            'clear': 'Clear the terminal screen',
            'history': 'Show command history',
            'exit': 'Exit the terminal session',
            'quit': 'Exit the terminal session'
        }
        
        return help_texts.get(command.lower(), f'No help available for command: {command}')
    
    def get_all_commands(self) -> List[str]:
        """
        Get a list of all available commands.
        
        Returns:
            List[str]: List of available commands
        """
        return sorted(list(self.terminal_commands))