"""
Command Executor Module
Handles safe execution of terminal commands with sandboxing and security measures.
"""

import os
import subprocess
import shutil
import glob
import time
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

class CommandExecutor:
    """
    Executes terminal commands safely with proper sandboxing and validation.
    """
    
    def __init__(self, sandbox_dir: str = None):
        # Set up sandbox directory for safe operations
        self.sandbox_dir = sandbox_dir or os.path.join(os.getcwd(), 'sandbox')
        self.current_dir = self.sandbox_dir
        self.max_file_size = 10 * 1024 * 1024  # 10MB max file size
        self.max_output_length = 10000  # Max output length
        
        # Create sandbox if it doesn't exist
        self._setup_sandbox()
        
        # Define command handlers
        self.command_handlers = {
            # File operations
            'ls': self._handle_ls,
            'pwd': self._handle_pwd,
            'cd': self._handle_cd,
            'mkdir': self._handle_mkdir,
            'rmdir': self._handle_rmdir,
            'rm': self._handle_rm,
            'cp': self._handle_cp,
            'mv': self._handle_mv,
            'touch': self._handle_touch,
            'cat': self._handle_cat,
            'head': self._handle_head,
            'tail': self._handle_tail,
            'find': self._handle_find,
            'tree': self._handle_tree,
            'stat': self._handle_stat,
            
            # Text operations
            'echo': self._handle_echo,
            'grep': self._handle_grep,
            'wc': self._handle_wc,
            'sort': self._handle_sort,
            
            # System commands
            'system': self._handle_system,
            'ps': self._handle_ps,
            'uptime': self._handle_uptime,
            'disk': self._handle_disk,
            'env': self._handle_env,
            'date': self._handle_date,
            
            # Utility commands
            'help': self._handle_help,
            'clear': self._handle_clear,
            'history': self._handle_history,
        }
    
    def _setup_sandbox(self):
        """Set up the sandbox directory for safe operations."""
        try:
            os.makedirs(self.sandbox_dir, exist_ok=True)
            # Create some sample files for testing
            sample_files = [
                'readme.txt',
                'sample.log',
                'config.json'
            ]
            for filename in sample_files:
                filepath = os.path.join(self.sandbox_dir, filename)
                if not os.path.exists(filepath):
                    with open(filepath, 'w') as f:
                        if filename == 'readme.txt':
                            f.write("Welcome to the web terminal sandbox!\nThis is a safe environment for file operations.")
                        elif filename == 'sample.log':
                            f.write("2024-01-01 10:00:00 INFO Application started\n2024-01-01 10:01:00 INFO User connected")
                        elif filename == 'config.json':
                            f.write('{"app_name": "web_terminal", "version": "1.0.0", "debug": false}')
        except Exception as e:
            print(f"Warning: Could not set up sandbox: {e}")
    
    def execute(self, command: str, args: List[str], command_type: str) -> Dict[str, Any]:
        """
        Execute a command safely.
        
        Args:
            command (str): Command to execute
            args (List[str]): Command arguments
            command_type (str): Type of command (terminal_command, natural_language, etc.)
            
        Returns:
            Dict containing execution results
        """
        try:
            if command_type == 'empty':
                return {
                    'success': True,
                    'output': '',
                    'error': None
                }
            
            if command_type == 'parse_error':
                return {
                    'success': False,
                    'output': '',
                    'error': 'Command parsing error'
                }
            
            # Handle terminal commands
            if command in self.command_handlers:
                return self.command_handlers[command](args)
            else:
                return {
                    'success': False,
                    'output': '',
                    'error': f'Unknown command: {command}. Type "help" for available commands.'
                }
                
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': f'Execution error: {str(e)}'
            }
    
    def _safe_path(self, path: str) -> str:
        """
        Ensure path is within sandbox directory.
        
        Args:
            path (str): Path to validate
            
        Returns:
            str: Safe absolute path within sandbox
        """
        if not path or path == '.':
            return self.current_dir
        
        if path == '..':
            parent = os.path.dirname(self.current_dir)
            if parent.startswith(self.sandbox_dir):
                return parent
            return self.sandbox_dir
        
        if os.path.isabs(path):
            # Convert absolute path to relative within sandbox
            path = path.lstrip('/')
        
        if path.startswith('../'):
            # Handle relative paths with ..
            full_path = os.path.abspath(os.path.join(self.current_dir, path))
        else:
            full_path = os.path.abspath(os.path.join(self.current_dir, path))
        
        # Ensure path is within sandbox
        if not full_path.startswith(self.sandbox_dir):
            return os.path.join(self.sandbox_dir, os.path.basename(path))
        
        return full_path
    
    # File operation handlers
    def _handle_ls(self, args: List[str]) -> Dict[str, Any]:
        """Handle ls command."""
        try:
            target_dir = self.current_dir
            show_hidden = False
            long_format = False
            
            # Parse arguments
            for arg in args:
                if arg.startswith('-'):
                    if 'a' in arg:
                        show_hidden = True
                    if 'l' in arg:
                        long_format = True
                else:
                    target_dir = self._safe_path(arg)
            
            if not os.path.exists(target_dir):
                return {'success': False, 'output': '', 'error': f'Directory not found: {target_dir}'}
            
            if not os.path.isdir(target_dir):
                return {'success': False, 'output': '', 'error': f'Not a directory: {target_dir}'}
            
            items = []
            for item in os.listdir(target_dir):
                if not show_hidden and item.startswith('.'):
                    continue
                
                item_path = os.path.join(target_dir, item)
                
                if long_format:
                    stat = os.stat(item_path)
                    size = stat.st_size
                    mtime = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M')
                    is_dir = os.path.isdir(item_path)
                    permissions = 'drwxr-xr-x' if is_dir else '-rw-r--r--'
                    items.append(f'{permissions} {size:>8} {mtime} {item}')
                else:
                    items.append(item)
            
            output = '\n'.join(sorted(items)) if items else ''
            return {'success': True, 'output': output, 'error': None}
            
        except Exception as e:
            return {'success': False, 'output': '', 'error': str(e)}
    
    def _handle_pwd(self, args: List[str]) -> Dict[str, Any]:
        """Handle pwd command."""
        # Return relative path within sandbox
        rel_path = os.path.relpath(self.current_dir, self.sandbox_dir)
        display_path = '/' if rel_path == '.' else f'/{rel_path}'
        return {'success': True, 'output': display_path, 'error': None}
    
    def _handle_cd(self, args: List[str]) -> Dict[str, Any]:
        """Handle cd command."""
        try:
            if not args:
                self.current_dir = self.sandbox_dir
                return {'success': True, 'output': '', 'error': None}
            
            target_dir = self._safe_path(args[0])
            
            if not os.path.exists(target_dir):
                return {'success': False, 'output': '', 'error': f'Directory not found: {args[0]}'}
            
            if not os.path.isdir(target_dir):
                return {'success': False, 'output': '', 'error': f'Not a directory: {args[0]}'}
            
            self.current_dir = target_dir
            return {'success': True, 'output': '', 'error': None}
            
        except Exception as e:
            return {'success': False, 'output': '', 'error': str(e)}
    
    def _handle_mkdir(self, args: List[str]) -> Dict[str, Any]:
        """Handle mkdir command."""
        try:
            if not args:
                return {'success': False, 'output': '', 'error': 'mkdir: missing directory name'}
            
            for dirname in args:
                dir_path = self._safe_path(dirname)
                os.makedirs(dir_path, exist_ok=True)
            
            return {'success': True, 'output': '', 'error': None}
            
        except Exception as e:
            return {'success': False, 'output': '', 'error': str(e)}
    
    def _handle_rm(self, args: List[str]) -> Dict[str, Any]:
        """Handle rm command."""
        try:
            if not args:
                return {'success': False, 'output': '', 'error': 'rm: missing file/directory name'}
            
            recursive = False
            force = False
            files_to_remove = []
            
            for arg in args:
                if arg.startswith('-'):
                    if 'r' in arg or 'R' in arg:
                        recursive = True
                    if 'f' in arg:
                        force = True
                else:
                    files_to_remove.append(arg)
            
            for filename in files_to_remove:
                file_path = self._safe_path(filename)
                
                if not os.path.exists(file_path):
                    if not force:
                        return {'success': False, 'output': '', 'error': f'File not found: {filename}'}
                    continue
                
                if os.path.isdir(file_path):
                    if recursive:
                        shutil.rmtree(file_path)
                    else:
                        return {'success': False, 'output': '', 'error': f'Cannot remove directory without -r flag: {filename}'}
                else:
                    os.remove(file_path)
            
            return {'success': True, 'output': '', 'error': None}
            
        except Exception as e:
            return {'success': False, 'output': '', 'error': str(e)}
    
    def _handle_cat(self, args: List[str]) -> Dict[str, Any]:
        """Handle cat command."""
        try:
            if not args:
                return {'success': False, 'output': '', 'error': 'cat: missing filename'}
            
            output_lines = []
            
            for filename in args:
                file_path = self._safe_path(filename)
                
                if not os.path.exists(file_path):
                    return {'success': False, 'output': '', 'error': f'File not found: {filename}'}
                
                if os.path.isdir(file_path):
                    return {'success': False, 'output': '', 'error': f'Is a directory: {filename}'}
                
                # Check file size
                if os.path.getsize(file_path) > self.max_file_size:
                    return {'success': False, 'output': '', 'error': f'File too large: {filename}'}
                
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                    if len(content) > self.max_output_length:
                        content = content[:self.max_output_length] + '\n... (output truncated)'
                    output_lines.append(content)
            
            return {'success': True, 'output': '\n'.join(output_lines), 'error': None}
            
        except Exception as e:
            return {'success': False, 'output': '', 'error': str(e)}
    
    def _handle_echo(self, args: List[str]) -> Dict[str, Any]:
        """Handle echo command."""
        output = ' '.join(args)
        return {'success': True, 'output': output, 'error': None}
    
    def _handle_touch(self, args: List[str]) -> Dict[str, Any]:
        """Handle touch command."""
        try:
            if not args:
                return {'success': False, 'output': '', 'error': 'touch: missing filename'}
            
            for filename in args:
                file_path = self._safe_path(filename)
                Path(file_path).touch()
            
            return {'success': True, 'output': '', 'error': None}
            
        except Exception as e:
            return {'success': False, 'output': '', 'error': str(e)}
    
    def _handle_system(self, args: List[str]) -> Dict[str, Any]:
        """Handle system info command."""
        try:
            import psutil
            
            # Get system information
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            output = f"""System Information:
CPU Usage: {cpu_percent}%
Memory: {memory.percent}% used ({memory.used // (1024**3):.1f}GB / {memory.total // (1024**3):.1f}GB)
Disk: {disk.percent}% used ({disk.used // (1024**3):.1f}GB / {disk.total // (1024**3):.1f}GB)
Processes: {len(psutil.pids())}"""
            
            return {'success': True, 'output': output, 'error': None}
            
        except Exception as e:
            return {'success': False, 'output': '', 'error': str(e)}
    
    def _handle_help(self, args: List[str]) -> Dict[str, Any]:
        """Handle help command."""
        help_text = """Available Commands:

File Operations:
  ls [options] [dir]  - List directory contents
  pwd                 - Print current directory
  cd [dir]            - Change directory
  mkdir <dir>         - Create directory
  rm [options] <file> - Remove files/directories
  cp <src> <dest>     - Copy files/directories
  mv <src> <dest>     - Move/rename files/directories
  touch <file>        - Create empty file
  cat <file>          - Display file contents

Text Operations:
  echo <text>         - Display text
  grep <pattern> <file> - Search text patterns
  wc <file>           - Count words, lines, characters

System Info:
  system              - Show system information
  ps                  - List processes
  uptime              - Show system uptime
  date                - Show current date/time

Utility:
  help                - Show this help
  clear               - Clear screen
  history             - Show command history

Natural Language:
You can also use natural language commands like:
"create a folder called test"
"show me all files in the current directory"
"copy file1.txt to backup.txt"
"""
        return {'success': True, 'output': help_text, 'error': None}
    
    def _handle_clear(self, args: List[str]) -> Dict[str, Any]:
        """Handle clear command."""
        return {'success': True, 'output': '\033[2J\033[H', 'error': None}
    
    def _handle_history(self, args: List[str]) -> Dict[str, Any]:
        """Handle history command - placeholder for database integration."""
        return {'success': True, 'output': 'Command history will be displayed here', 'error': None}
    
    def _handle_date(self, args: List[str]) -> Dict[str, Any]:
        """Handle date command."""
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z')
        return {'success': True, 'output': current_time, 'error': None}
    
    # Placeholder handlers for other commands
    def _handle_rmdir(self, args: List[str]) -> Dict[str, Any]:
        """Handle rmdir command."""
        return self._handle_rm(args + ['-r'])
    
    def _handle_cp(self, args: List[str]) -> Dict[str, Any]:
        """Handle cp command."""
        return {'success': False, 'output': '', 'error': 'cp command not yet implemented'}
    
    def _handle_mv(self, args: List[str]) -> Dict[str, Any]:
        """Handle mv command."""
        return {'success': False, 'output': '', 'error': 'mv command not yet implemented'}
    
    def _handle_head(self, args: List[str]) -> Dict[str, Any]:
        """Handle head command."""
        return {'success': False, 'output': '', 'error': 'head command not yet implemented'}
    
    def _handle_tail(self, args: List[str]) -> Dict[str, Any]:
        """Handle tail command."""
        return {'success': False, 'output': '', 'error': 'tail command not yet implemented'}
    
    def _handle_find(self, args: List[str]) -> Dict[str, Any]:
        """Handle find command."""
        return {'success': False, 'output': '', 'error': 'find command not yet implemented'}
    
    def _handle_tree(self, args: List[str]) -> Dict[str, Any]:
        """Handle tree command."""
        return {'success': False, 'output': '', 'error': 'tree command not yet implemented'}
    
    def _handle_stat(self, args: List[str]) -> Dict[str, Any]:
        """Handle stat command."""
        return {'success': False, 'output': '', 'error': 'stat command not yet implemented'}
    
    def _handle_grep(self, args: List[str]) -> Dict[str, Any]:
        """Handle grep command."""
        return {'success': False, 'output': '', 'error': 'grep command not yet implemented'}
    
    def _handle_wc(self, args: List[str]) -> Dict[str, Any]:
        """Handle wc command."""
        return {'success': False, 'output': '', 'error': 'wc command not yet implemented'}
    
    def _handle_sort(self, args: List[str]) -> Dict[str, Any]:
        """Handle sort command."""
        return {'success': False, 'output': '', 'error': 'sort command not yet implemented'}
    
    def _handle_ps(self, args: List[str]) -> Dict[str, Any]:
        """Handle ps command."""
        return {'success': False, 'output': '', 'error': 'ps command not yet implemented'}
    
    def _handle_uptime(self, args: List[str]) -> Dict[str, Any]:
        """Handle uptime command."""
        return {'success': False, 'output': '', 'error': 'uptime command not yet implemented'}
    
    def _handle_disk(self, args: List[str]) -> Dict[str, Any]:
        """Handle disk command."""
        return {'success': False, 'output': '', 'error': 'disk command not yet implemented'}
    
    def _handle_env(self, args: List[str]) -> Dict[str, Any]:
        """Handle env command."""
        return {'success': False, 'output': '', 'error': 'env command not yet implemented'}