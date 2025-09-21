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
        # Use persistent storage path in production, local sandbox in development
        if sandbox_dir:
            self.sandbox_dir = sandbox_dir
        elif os.environ.get('FLASK_ENV') == 'production':
            # Use mounted persistent storage in production
            self.sandbox_dir = '/app/sandbox'
        else:
            # Use local sandbox for development
            self.sandbox_dir = os.path.join(os.getcwd(), 'sandbox')
            
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
                'config.json',
                'file1.txt'
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
                        elif filename == 'file1.txt':
                            f.write("This is a sample file for testing file operations.\nYou can move, copy, or edit this file.")
            
            # Create some additional directories and files for testing
            test_files = ['kek']  # Create some additional files as shown in user's output
            for filename in test_files:
                filepath = os.path.join(self.sandbox_dir, filename)
                if not os.path.exists(filepath):
                    with open(filepath, 'w') as f:
                        f.write(f"Content of {filename}\n")
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
            
            # Handle multi-commands with && operator
            if command_type == 'ai_generated':
                if command == 'multi_command' and args:
                    # Full command passed as first argument
                    return self._execute_multi_command(args[0])
                else:
                    # Reconstruct full command from parts
                    full_command = command + (' ' + ' '.join(args) if args else '')
                    if '&&' in full_command:
                        return self._execute_multi_command(full_command)
                    else:
                        # Single AI-generated command, execute normally
                        if command in self.command_handlers:
                            return self.command_handlers[command](args)
                        else:
                            return {
                                'success': False,
                                'output': '',
                                'error': f'Unknown command: {command}. Type "help" for available commands.'
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
    
    def _execute_multi_command(self, full_command: str) -> Dict[str, Any]:
        """
        Execute multiple commands connected with && operator.
        
        Args:
            full_command (str): Full command string with && operators
            
        Returns:
            Dict containing execution results
        """
        try:
            # Split by && operator
            commands = [cmd.strip() for cmd in full_command.split('&&')]
            outputs = []
            
            for cmd in commands:
                if not cmd:
                    continue
                    
                # Parse individual command
                parts = cmd.split()
                if not parts:
                    continue
                    
                command_name = parts[0]
                command_args = parts[1:] if len(parts) > 1 else []
                
                # Execute individual command
                if command_name in self.command_handlers:
                    result = self.command_handlers[command_name](command_args)
                    if not result['success']:
                        # If any command fails, stop execution and return error
                        return {
                            'success': False,
                            'output': '\n'.join(outputs) + '\n' + (result['output'] or ''),
                            'error': result['error']
                        }
                    if result['output']:
                        outputs.append(result['output'])
                else:
                    return {
                        'success': False,
                        'output': '\n'.join(outputs),
                        'error': f'Unknown command: {command_name}'
                    }
            
            return {
                'success': True,
                'output': '\n'.join(outputs),
                'error': None
            }
            
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': f'Multi-command execution error: {str(e)}'
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
        """Handle cp (copy) command."""
        try:
            if len(args) < 2:
                return {
                    'success': False,
                    'output': '',
                    'error': 'cp: missing file operand. Usage: cp SOURCE DEST'
                }
            
            source_path = self._safe_path(args[0])
            dest_path = self._safe_path(args[1])
            
            # Check if source exists
            if not os.path.exists(source_path):
                return {
                    'success': False,
                    'output': '',
                    'error': f"cp: cannot stat '{args[0]}': No such file or directory"
                }
            
            # If destination is a directory, copy source into it
            if os.path.isdir(dest_path):
                dest_path = os.path.join(dest_path, os.path.basename(source_path))
            
            # Check if destination already exists
            if os.path.exists(dest_path):
                return {
                    'success': False,
                    'output': '',
                    'error': f"cp: cannot copy '{args[0]}' to '{args[1]}': File exists"
                }
            
            # Perform the copy
            if os.path.isfile(source_path):
                shutil.copy2(source_path, dest_path)
            elif os.path.isdir(source_path):
                shutil.copytree(source_path, dest_path)
            else:
                return {
                    'success': False,
                    'output': '',
                    'error': f"cp: '{args[0]}' is not a regular file or directory"
                }
            
            return {
                'success': True,
                'output': '',
                'error': None
            }
            
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': f'cp: {str(e)}'
            }
    
    def _handle_mv(self, args: List[str]) -> Dict[str, Any]:
        """Handle mv (move/rename) command."""
        try:
            if len(args) < 2:
                return {
                    'success': False,
                    'output': '',
                    'error': 'mv: missing file operand. Usage: mv SOURCE DEST'
                }
            
            source_path = self._safe_path(args[0])
            dest_path = self._safe_path(args[1])
            
            # Check if source exists
            if not os.path.exists(source_path):
                return {
                    'success': False,
                    'output': '',
                    'error': f"mv: cannot stat '{args[0]}': No such file or directory"
                }
            
            # If destination is a directory, move source into it
            if os.path.isdir(dest_path):
                dest_path = os.path.join(dest_path, os.path.basename(source_path))
            
            # Check if destination already exists
            if os.path.exists(dest_path):
                return {
                    'success': False,
                    'output': '',
                    'error': f"mv: cannot move '{args[0]}' to '{args[1]}': File exists"
                }
            
            # Perform the move
            shutil.move(source_path, dest_path)
            
            return {
                'success': True,
                'output': '',
                'error': None
            }
            
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': f'mv: {str(e)}'
            }
    
    def _handle_head(self, args: List[str]) -> Dict[str, Any]:
        """Handle head command - display first lines of a file."""
        try:
            lines = 10  # default
            file_path = None
            
            # Parse arguments
            i = 0
            while i < len(args):
                if args[i] == '-n' and i + 1 < len(args):
                    try:
                        lines = int(args[i + 1])
                        i += 2
                    except ValueError:
                        return {
                            'success': False,
                            'output': '',
                            'error': f'head: invalid number of lines: {args[i + 1]}'
                        }
                elif args[i].startswith('-') and args[i][1:].isdigit():
                    lines = int(args[i][1:])
                    i += 1
                else:
                    file_path = args[i]
                    i += 1
            
            if not file_path:
                return {
                    'success': False,
                    'output': '',
                    'error': 'head: missing file operand'
                }
            
            safe_path = self._safe_path(file_path)
            
            if not os.path.exists(safe_path):
                return {
                    'success': False,
                    'output': '',
                    'error': f'head: cannot open \'{file_path}\' for reading: No such file or directory'
                }
            
            if os.path.isdir(safe_path):
                return {
                    'success': False,
                    'output': '',
                    'error': f'head: error reading \'{file_path}\': Is a directory'
                }
            
            with open(safe_path, 'r', encoding='utf-8', errors='ignore') as f:
                result_lines = []
                for i, line in enumerate(f):
                    if i >= lines:
                        break
                    result_lines.append(line.rstrip())
            
            return {
                'success': True,
                'output': '\n'.join(result_lines),
                'error': None
            }
            
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': f'head: {str(e)}'
            }
    
    def _handle_tail(self, args: List[str]) -> Dict[str, Any]:
        """Handle tail command - display last lines of a file."""
        try:
            lines = 10  # default
            file_path = None
            
            # Parse arguments
            i = 0
            while i < len(args):
                if args[i] == '-n' and i + 1 < len(args):
                    try:
                        lines = int(args[i + 1])
                        i += 2
                    except ValueError:
                        return {
                            'success': False,
                            'output': '',
                            'error': f'tail: invalid number of lines: {args[i + 1]}'
                        }
                elif args[i].startswith('-') and args[i][1:].isdigit():
                    lines = int(args[i][1:])
                    i += 1
                else:
                    file_path = args[i]
                    i += 1
            
            if not file_path:
                return {
                    'success': False,
                    'output': '',
                    'error': 'tail: missing file operand'
                }
            
            safe_path = self._safe_path(file_path)
            
            if not os.path.exists(safe_path):
                return {
                    'success': False,
                    'output': '',
                    'error': f'tail: cannot open \'{file_path}\' for reading: No such file or directory'
                }
            
            if os.path.isdir(safe_path):
                return {
                    'success': False,
                    'output': '',
                    'error': f'tail: error reading \'{file_path}\': Is a directory'
                }
            
            with open(safe_path, 'r', encoding='utf-8', errors='ignore') as f:
                all_lines = f.readlines()
                
            # Get last 'lines' number of lines
            result_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
            result_lines = [line.rstrip() for line in result_lines]
            
            return {
                'success': True,
                'output': '\n'.join(result_lines),
                'error': None
            }
            
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': f'tail: {str(e)}'
            }
    
    def _handle_find(self, args: List[str]) -> Dict[str, Any]:
        """Handle find command - search for files and directories."""
        try:
            if not args:
                search_dir = self.current_dir
                pattern = '*'
            elif len(args) == 1:
                search_dir = self.current_dir
                pattern = args[0]
            else:
                search_dir = self._safe_path(args[0])
                pattern = args[1] if len(args) > 1 else '*'
            
            # Ensure search is within sandbox
            if not search_dir.startswith(self.sandbox_dir):
                search_dir = self.sandbox_dir
            
            results = []
            
            # Simple find implementation
            for root, dirs, files in os.walk(search_dir):
                # Search directories
                for dir_name in dirs:
                    if pattern == '*' or pattern in dir_name:
                        rel_path = os.path.relpath(os.path.join(root, dir_name), self.current_dir)
                        results.append(f'./{rel_path}')
                
                # Search files
                for file_name in files:
                    if pattern == '*' or pattern in file_name:
                        rel_path = os.path.relpath(os.path.join(root, file_name), self.current_dir)
                        results.append(f'./{rel_path}')
            
            if not results:
                return {
                    'success': True,
                    'output': f'find: no files or directories matching "{pattern}" found',
                    'error': None
                }
            
            return {
                'success': True,
                'output': '\n'.join(sorted(results)),
                'error': None
            }
            
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': f'find: {str(e)}'
            }
    
    def _handle_tree(self, args: List[str]) -> Dict[str, Any]:
        """Handle tree command - display directory tree structure."""
        try:
            # Default to current directory
            root_path = self.current_dir
            max_depth = None
            
            # Parse arguments
            i = 0
            while i < len(args):
                if args[i] == '-L' and i + 1 < len(args):
                    try:
                        max_depth = int(args[i + 1])
                        i += 2
                    except ValueError:
                        return {
                            'success': False,
                            'output': '',
                            'error': f'tree: invalid level: {args[i + 1]}'
                        }
                elif args[i].startswith('-L') and len(args[i]) > 2:
                    try:
                        max_depth = int(args[i][2:])
                        i += 1
                    except ValueError:
                        return {
                            'success': False,
                            'output': '',
                            'error': f'tree: invalid level: {args[i][2:]}'
                        }
                else:
                    root_path = self._safe_path(args[i])
                    i += 1
            
            if not os.path.exists(root_path):
                return {
                    'success': False,
                    'output': '',
                    'error': f'tree: {args[0] if args and not args[0].startswith("-") else root_path}: No such file or directory'
                }
            
            if not os.path.isdir(root_path):
                return {
                    'success': False,
                    'output': '',
                    'error': f'tree: {args[0] if args and not args[0].startswith("-") else root_path}: Not a directory'
                }
            
            # Generate tree structure
            def generate_tree(path, prefix="", depth=0):
                if max_depth is not None and depth >= max_depth:
                    return []
                
                items = []
                try:
                    entries = sorted(os.listdir(path))
                    dirs = [e for e in entries if os.path.isdir(os.path.join(path, e))]
                    files = [e for e in entries if os.path.isfile(os.path.join(path, e))]
                    all_entries = dirs + files
                    
                    for i, entry in enumerate(all_entries):
                        is_last = i == len(all_entries) - 1
                        current_prefix = "└── " if is_last else "├── "
                        items.append(f"{prefix}{current_prefix}{entry}")
                        
                        entry_path = os.path.join(path, entry)
                        if os.path.isdir(entry_path) and (max_depth is None or depth + 1 < max_depth):
                            extension = "    " if is_last else "│   "
                            items.extend(generate_tree(entry_path, prefix + extension, depth + 1))
                            
                except PermissionError:
                    items.append(f"{prefix}[error opening dir]")
                
                return items
            
            # Start with root directory name
            root_name = os.path.basename(root_path) or root_path
            result = [root_name]
            
            # Add tree structure
            tree_lines = generate_tree(root_path)
            result.extend(tree_lines)
            
            # Count directories and files
            dir_count = 0
            file_count = 0
            for root, dirs, files in os.walk(root_path):
                dir_count += len(dirs)
                file_count += len(files)
            
            result.append("")
            result.append(f"{dir_count} directories, {file_count} files")
            
            return {
                'success': True,
                'output': '\n'.join(result),
                'error': None
            }
            
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': f'tree: {str(e)}'
            }
    
    def _handle_stat(self, args: List[str]) -> Dict[str, Any]:
        """Handle stat command - display file or filesystem status."""
        try:
            if not args:
                return {
                    'success': False,
                    'output': '',
                    'error': 'stat: missing operand'
                }
            
            file_path = args[0]
            safe_path = self._safe_path(file_path)
            
            if not os.path.exists(safe_path):
                return {
                    'success': False,
                    'output': '',
                    'error': f'stat: cannot stat \'{file_path}\': No such file or directory'
                }
            
            import time
            import pwd
            import grp
            import stat as stat_module
            
            # Get file stats
            file_stat = os.stat(safe_path)
            
            # File type and permissions
            mode = file_stat.st_mode
            if stat_module.S_ISDIR(mode):
                file_type = "directory"
            elif stat_module.S_ISREG(mode):
                file_type = "regular file"
            elif stat_module.S_ISLNK(mode):
                file_type = "symbolic link"
            else:
                file_type = "special file"
            
            # Permissions
            perms = stat_module.filemode(mode)
            
            # Owner and group
            try:
                owner = pwd.getpwuid(file_stat.st_uid).pw_name
            except:
                owner = str(file_stat.st_uid)
            
            try:
                group = grp.getgrgid(file_stat.st_gid).gr_name
            except:
                group = str(file_stat.st_gid)
            
            # Times
            access_time = time.ctime(file_stat.st_atime)
            modify_time = time.ctime(file_stat.st_mtime)
            change_time = time.ctime(file_stat.st_ctime)
            
            # Build output
            output = f"  File: {file_path}\n"
            output += f"  Size: {file_stat.st_size:<10} Blocks: {file_stat.st_blocks:<10} IO Block: {file_stat.st_blksize} {file_type}\n"
            output += f"Device: {file_stat.st_dev:x}h/{file_stat.st_dev}d    Inode: {file_stat.st_ino:<10} Links: {file_stat.st_nlink}\n"
            output += f"Access: ({oct(stat_module.S_IMODE(mode))}/{perms})  Uid: ({file_stat.st_uid:>5}/{owner:<8}) Gid: ({file_stat.st_gid:>5}/{group:<8})\n"
            output += f"Access: {access_time}\n"
            output += f"Modify: {modify_time}\n"
            output += f"Change: {change_time}\n"
            output += f" Birth: -"
            
            return {
                'success': True,
                'output': output,
                'error': None
            }
            
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': f'stat: {str(e)}'
            }
    
    def _handle_grep(self, args: List[str]) -> Dict[str, Any]:
        """Handle grep command - search for text patterns in files."""
        try:
            if len(args) < 2:
                return {
                    'success': False,
                    'output': '',
                    'error': 'grep: usage: grep pattern file [file...]'
                }
            
            pattern = args[0]
            file_paths = args[1:]
            results = []
            
            for file_path in file_paths:
                safe_path = self._safe_path(file_path)
                
                if not os.path.exists(safe_path):
                    results.append(f'grep: {file_path}: No such file or directory')
                    continue
                
                if os.path.isdir(safe_path):
                    results.append(f'grep: {file_path}: Is a directory')
                    continue
                
                try:
                    with open(safe_path, 'r', encoding='utf-8', errors='ignore') as f:
                        line_num = 1
                        for line in f:
                            if pattern in line:
                                if len(file_paths) > 1:
                                    results.append(f'{file_path}:{line_num}:{line.rstrip()}')
                                else:
                                    results.append(f'{line_num}:{line.rstrip()}')
                            line_num += 1
                            
                except Exception as e:
                    results.append(f'grep: {file_path}: {str(e)}')
            
            return {
                'success': True,
                'output': '\n'.join(results) if results else '',
                'error': None
            }
            
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': f'grep: {str(e)}'
            }
    
    def _handle_wc(self, args: List[str]) -> Dict[str, Any]:
        """Handle wc command - word, line, character, and byte count."""
        try:
            if not args:
                return {
                    'success': False,
                    'output': '',
                    'error': 'wc: missing file operand'
                }
            
            show_lines = True
            show_words = True
            show_chars = True
            files = []
            
            # Parse arguments
            i = 0
            while i < len(args):
                if args[i] == '-l':
                    show_lines, show_words, show_chars = True, False, False
                    i += 1
                elif args[i] == '-w':
                    show_lines, show_words, show_chars = False, True, False
                    i += 1
                elif args[i] == '-c':
                    show_lines, show_words, show_chars = False, False, True
                    i += 1
                else:
                    files.append(args[i])
                    i += 1
            
            if not files:
                return {
                    'success': False,
                    'output': '',
                    'error': 'wc: missing file operand'
                }
            
            results = []
            total_lines = total_words = total_chars = 0
            
            for file_path in files:
                safe_path = self._safe_path(file_path)
                
                if not os.path.exists(safe_path):
                    results.append(f'wc: {file_path}: No such file or directory')
                    continue
                
                if os.path.isdir(safe_path):
                    results.append(f'wc: {file_path}: Is a directory')
                    continue
                
                try:
                    with open(safe_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                    lines = content.count('\n')
                    words = len(content.split())
                    chars = len(content)
                    
                    total_lines += lines
                    total_words += words
                    total_chars += chars
                    
                    counts = []
                    if show_lines:
                        counts.append(str(lines))
                    if show_words:
                        counts.append(str(words))
                    if show_chars:
                        counts.append(str(chars))
                    
                    results.append(f"{' '.join(counts)} {file_path}")
                    
                except Exception as e:
                    results.append(f'wc: {file_path}: {str(e)}')
            
            # Add total if multiple files
            if len(files) > 1:
                counts = []
                if show_lines:
                    counts.append(str(total_lines))
                if show_words:
                    counts.append(str(total_words))
                if show_chars:
                    counts.append(str(total_chars))
                results.append(f"{' '.join(counts)} total")
            
            return {
                'success': True,
                'output': '\n'.join(results),
                'error': None
            }
            
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': f'wc: {str(e)}'
            }
    
    def _handle_sort(self, args: List[str]) -> Dict[str, Any]:
        """Handle sort command - sort lines of text files."""
        try:
            if not args:
                return {
                    'success': False,
                    'output': '',
                    'error': 'sort: missing file operand'
                }
            
            reverse = False
            numeric = False
            files = []
            
            # Parse arguments
            i = 0
            while i < len(args):
                if args[i] == '-r':
                    reverse = True
                    i += 1
                elif args[i] == '-n':
                    numeric = True
                    i += 1
                else:
                    files.append(args[i])
                    i += 1
            
            if not files:
                return {
                    'success': False,
                    'output': '',
                    'error': 'sort: missing file operand'
                }
            
            all_lines = []
            
            for file_path in files:
                safe_path = self._safe_path(file_path)
                
                if not os.path.exists(safe_path):
                    return {
                        'success': False,
                        'output': '',
                        'error': f'sort: cannot read: {file_path}: No such file or directory'
                    }
                
                if os.path.isdir(safe_path):
                    return {
                        'success': False,
                        'output': '',
                        'error': f'sort: read failed: {file_path}: Is a directory'
                    }
                
                try:
                    with open(safe_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                        all_lines.extend([line.rstrip() for line in lines])
                        
                except Exception as e:
                    return {
                        'success': False,
                        'output': '',
                        'error': f'sort: {file_path}: {str(e)}'
                    }
            
            # Sort the lines
            if numeric:
                try:
                    all_lines.sort(key=lambda x: float(x) if x.replace('.', '').replace('-', '').isdigit() else float('inf'), reverse=reverse)
                except:
                    all_lines.sort(reverse=reverse)
            else:
                all_lines.sort(reverse=reverse)
            
            return {
                'success': True,
                'output': '\n'.join(all_lines),
                'error': None
            }
            
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': f'sort: {str(e)}'
            }
    
    def _handle_ps(self, args: List[str]) -> Dict[str, Any]:
        """Handle ps command - show running processes."""
        try:
            import psutil
            processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Sort by PID
            processes.sort(key=lambda x: x['pid'])
            
            # Format output
            output_lines = ['  PID  %CPU %MEM COMMAND']
            for proc in processes[:20]:  # Show first 20 processes
                pid = proc['pid']
                name = proc['name'][:15]  # Truncate long names
                cpu = proc['cpu_percent'] or 0
                mem = proc['memory_percent'] or 0
                output_lines.append(f'{pid:5d} {cpu:4.1f} {mem:4.1f} {name}')
            
            return {
                'success': True,
                'output': '\n'.join(output_lines),
                'error': None
            }
            
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': f'ps: {str(e)}'
            }
    
    def _handle_uptime(self, args: List[str]) -> Dict[str, Any]:
        """Handle uptime command - show system uptime."""
        try:
            import time
            import os
            
            # Get system uptime
            try:
                with open('/proc/uptime', 'r') as f:
                    uptime_seconds = float(f.readline().split()[0])
            except:
                # Fallback for systems without /proc/uptime
                uptime_seconds = time.time() - os.path.getctime('/proc')
            
            # Convert to human readable format
            days = int(uptime_seconds // 86400)
            hours = int((uptime_seconds % 86400) // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            
            # Format uptime string
            uptime_str = ""
            if days > 0:
                uptime_str += f"{days} day{'s' if days != 1 else ''}, "
            if hours > 0:
                uptime_str += f"{hours}:{minutes:02d}, "
            else:
                uptime_str += f"{minutes} min, "
            
            # Get current time
            current_time = time.strftime("%H:%M:%S")
            
            # Get load average (if available)
            try:
                with open('/proc/loadavg', 'r') as f:
                    load_avg = f.readline().split()[:3]
                    load_str = f"load average: {', '.join(load_avg)}"
            except:
                load_str = "load average: N/A"
            
            # Get number of users (simplified)
            try:
                import subprocess
                result = subprocess.run(['who'], capture_output=True, text=True, timeout=5)
                user_count = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
            except:
                user_count = 1  # assume at least current user
            
            output = f" {current_time} up {uptime_str}{user_count} user{'s' if user_count != 1 else ''}, {load_str}"
            
            return {
                'success': True,
                'output': output,
                'error': None
            }
            
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': f'uptime: {str(e)}'
            }
    
    def _handle_disk(self, args: List[str]) -> Dict[str, Any]:
        """Handle disk command - show disk usage information."""
        try:
            import shutil
            
            # Default to current directory
            path = self.current_dir
            if args:
                path = self._safe_path(args[0])
            
            if not os.path.exists(path):
                return {
                    'success': False,
                    'output': '',
                    'error': f'disk: {args[0] if args else path}: No such file or directory'
                }
            
            # Get disk usage
            total, used, free = shutil.disk_usage(path)
            
            # Convert bytes to human readable format
            def format_bytes(bytes_val):
                for unit in ['B', 'K', 'M', 'G', 'T']:
                    if bytes_val < 1024.0:
                        return f"{bytes_val:.1f}{unit}"
                    bytes_val /= 1024.0
                return f"{bytes_val:.1f}P"
            
            total_str = format_bytes(total)
            used_str = format_bytes(used)
            free_str = format_bytes(free)
            
            # Calculate percentage
            percent_used = (used / total * 100) if total > 0 else 0
            
            # Format output similar to df command
            output = f"Filesystem     Size  Used Avail Use% Mounted on\n"
            output += f"{path:<14} {total_str:>4} {used_str:>4} {free_str:>5} {percent_used:>3.0f}% {path}"
            
            return {
                'success': True,
                'output': output,
                'error': None
            }
            
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': f'disk: {str(e)}'
            }
    
    def _handle_env(self, args: List[str]) -> Dict[str, Any]:
        """Handle env command - show environment variables."""
        try:
            env_vars = []
            
            # Show some common environment variables (filtered for security)
            safe_vars = ['PATH', 'HOME', 'USER', 'SHELL', 'TERM', 'PWD', 'LANG', 'LC_ALL']
            
            for var in safe_vars:
                value = os.environ.get(var, '')
                if value:
                    env_vars.append(f'{var}={value}')
            
            # Add some custom variables
            env_vars.extend([
                'TERMINAL_TYPE=web_terminal',
                'SANDBOX_MODE=enabled',
                f'CURRENT_DIR={self.current_dir}'
            ])
            
            return {
                'success': True,
                'output': '\n'.join(env_vars),
                'error': None
            }
            
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': f'env: {str(e)}'
            }