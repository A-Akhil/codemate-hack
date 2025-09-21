"""
Database Manager Module
Handles Supabase database operations for user management, command history, and sessions.
"""

import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DatabaseManager:
    """
    Manages all database operations with Supabase.
    """
    
    def __init__(self):
        # Initialize Supabase client
        self.supabase_url = os.environ.get('SUPABASE_URL')
        self.supabase_key = os.environ.get('SUPABASE_API_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_API_KEY must be set in environment variables")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
    
    def initialize_tables(self):
        """
        Initialize database tables if they don't exist.
        This method checks if tables exist and creates them if needed.
        """
        try:
            # Check if tables exist by trying to query them
            self._check_and_create_users_table()
            self._check_and_create_sessions_table()
            self._check_and_create_command_history_table()
            self._check_and_create_logs_table()
            
            print("Database tables initialized successfully")
            
        except Exception as e:
            print(f"Database initialization error: {e}")
            # Note: In a real implementation, you'd use Supabase migrations
            # For now, we'll assume tables are created via SQL or Supabase dashboard
    
    def _check_and_create_users_table(self):
        """Check and create users table."""
        try:
            # Try to select from users table
            result = self.supabase.table('users').select('id').limit(1).execute()
        except Exception:
            # Table doesn't exist, log this for manual creation
            print("Users table not found. Please create it manually in Supabase with:")
            print("""
            CREATE TABLE users (
                id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                last_login TIMESTAMP WITH TIME ZONE,
                is_active BOOLEAN DEFAULT TRUE,
                preferences JSONB DEFAULT '{}'
            );
            """)
    
    def _check_and_create_sessions_table(self):
        """Check and create sessions table."""
        try:
            result = self.supabase.table('sessions').select('id').limit(1).execute()
        except Exception:
            print("Sessions table not found. Please create it manually in Supabase with:")
            print("""
            CREATE TABLE sessions (
                id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
                user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                session_id VARCHAR(100) UNIQUE NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                is_active BOOLEAN DEFAULT TRUE,
                metadata JSONB DEFAULT '{}'
            );
            """)
    
    def _check_and_create_command_history_table(self):
        """Check and create command_history table."""
        try:
            result = self.supabase.table('command_history').select('id').limit(1).execute()
        except Exception:
            print("Command history table not found. Please create it manually in Supabase with:")
            print("""
            CREATE TABLE command_history (
                id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
                user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                session_id VARCHAR(100) NOT NULL,
                command TEXT NOT NULL,
                output TEXT,
                success BOOLEAN DEFAULT TRUE,
                execution_time_ms INTEGER,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                command_type VARCHAR(50) DEFAULT 'terminal',
                metadata JSONB DEFAULT '{}'
            );
            
            CREATE INDEX idx_command_history_user_id ON command_history(user_id);
            CREATE INDEX idx_command_history_session_id ON command_history(session_id);
            CREATE INDEX idx_command_history_created_at ON command_history(created_at);
            """)
    
    def _check_and_create_logs_table(self):
        """Check and create logs table."""
        try:
            result = self.supabase.table('logs').select('id').limit(1).execute()
        except Exception:
            print("Logs table not found. Please create it manually in Supabase with:")
            print("""
            CREATE TABLE logs (
                id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
                user_id UUID REFERENCES users(id) ON DELETE SET NULL,
                session_id VARCHAR(100),
                level VARCHAR(20) NOT NULL CHECK (level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')),
                message TEXT NOT NULL,
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            
            CREATE INDEX idx_logs_level ON logs(level);
            CREATE INDEX idx_logs_created_at ON logs(created_at);
            """)
    
    # User Management
    def create_user(self, username: str, email: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new user.
        
        Args:
            username (str): Username
            email (Optional[str]): Email address
            
        Returns:
            Dict containing user information or error
        """
        try:
            user_data = {
                'username': username,
                'email': email,
                'created_at': datetime.now().isoformat(),
                'is_active': True
            }
            
            result = self.supabase.table('users').insert(user_data).execute()
            
            if result.data:
                return {
                    'success': True,
                    'user': result.data[0]
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to create user'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_user(self, user_id: str = None, username: str = None) -> Dict[str, Any]:
        """
        Get user by ID or username.
        
        Args:
            user_id (str): User ID
            username (str): Username
            
        Returns:
            Dict containing user information or error
        """
        try:
            if user_id:
                result = self.supabase.table('users').select('*').eq('id', user_id).execute()
            elif username:
                result = self.supabase.table('users').select('*').eq('username', username).execute()
            else:
                return {'success': False, 'error': 'Either user_id or username must be provided'}
            
            if result.data:
                return {
                    'success': True,
                    'user': result.data[0]
                }
            else:
                return {
                    'success': False,
                    'error': 'User not found'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_user_last_login(self, user_id: str) -> Dict[str, Any]:
        """
        Update user's last login timestamp.
        
        Args:
            user_id (str): User ID
            
        Returns:
            Dict containing success status
        """
        try:
            result = self.supabase.table('users').update({
                'last_login': datetime.now().isoformat()
            }).eq('id', user_id).execute()
            
            return {
                'success': True,
                'updated': len(result.data) > 0
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    # Session Management
    def create_session(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """
        Create a new session.
        
        Args:
            user_id (str): User ID
            session_id (str): Session ID
            
        Returns:
            Dict containing session information or error
        """
        try:
            session_data = {
                'user_id': user_id,
                'session_id': session_id,
                'created_at': datetime.now().isoformat(),
                'last_activity': datetime.now().isoformat(),
                'is_active': True
            }
            
            result = self.supabase.table('sessions').insert(session_data).execute()
            
            if result.data:
                return {
                    'success': True,
                    'session': result.data[0]
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to create session'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_session_activity(self, session_id: str) -> Dict[str, Any]:
        """
        Update session's last activity timestamp.
        
        Args:
            session_id (str): Session ID
            
        Returns:
            Dict containing success status
        """
        try:
            result = self.supabase.table('sessions').update({
                'last_activity': datetime.now().isoformat()
            }).eq('session_id', session_id).execute()
            
            return {
                'success': True,
                'updated': len(result.data) > 0
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def close_session(self, session_id: str) -> Dict[str, Any]:
        """
        Close a session by marking it as inactive.
        
        Args:
            session_id (str): Session ID
            
        Returns:
            Dict containing success status
        """
        try:
            result = self.supabase.table('sessions').update({
                'is_active': False
            }).eq('session_id', session_id).execute()
            
            return {
                'success': True,
                'closed': len(result.data) > 0
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    # Command History Management
    def save_command_history(self, user_id: str, session_id: str, command: str, 
                           output: str, success: bool = True, 
                           execution_time_ms: Optional[int] = None,
                           command_type: str = 'terminal') -> Dict[str, Any]:
        """
        Save command execution to history.
        
        Args:
            user_id (str): User ID
            session_id (str): Session ID
            command (str): Executed command
            output (str): Command output
            success (bool): Whether command succeeded
            execution_time_ms (Optional[int]): Execution time in milliseconds
            command_type (str): Type of command (terminal, natural_language, etc.)
            
        Returns:
            Dict containing success status
        """
        try:
            # For anonymous users, use a special user ID
            if user_id == 'anonymous':
                # Try to get or create anonymous user
                anon_user = self.get_user(username='anonymous')
                if not anon_user['success']:
                    # Create anonymous user
                    create_result = self.create_user('anonymous', 'anonymous@localhost')
                    if create_result['success']:
                        user_id = create_result['user']['id']
                    else:
                        # Skip database save for true anonymous users
                        return {'success': True, 'message': 'Command executed but not saved (anonymous user)'}
                else:
                    user_id = anon_user['user']['id']
            
            history_data = {
                'user_id': user_id,
                'session_id': session_id,
                'command': command,
                'output': output[:10000] if output else '',  # Limit output size
                'success': success,
                'execution_time_ms': execution_time_ms,
                'command_type': command_type,
                'created_at': datetime.now().isoformat()
            }
            
            result = self.supabase.table('command_history').insert(history_data).execute()
            
            return {
                'success': True,
                'saved': len(result.data) > 0
            }
            
        except Exception as e:
            # Don't fail the command execution if history saving fails
            print(f"Warning: Failed to save command history: {e}")
            return {
                'success': True,
                'error': str(e),
                'message': 'Command executed but history not saved'
            }
    
    def get_command_history(self, user_id: str = None, session_id: str = None, 
                          limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get command history for a user or session.
        
        Args:
            user_id (str): User ID
            session_id (str): Session ID
            limit (int): Maximum number of records to return
            
        Returns:
            List of command history records
        """
        try:
            query = self.supabase.table('command_history').select('*')
            
            if user_id and user_id != 'anonymous':
                query = query.eq('user_id', user_id)
            elif session_id:
                query = query.eq('session_id', session_id)
            
            result = query.order('created_at', desc=True).limit(limit).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            print(f"Error getting command history: {e}")
            return []
    
    def delete_old_history(self, days_old: int = 30) -> Dict[str, Any]:
        """
        Delete command history older than specified days.
        
        Args:
            days_old (int): Number of days after which to delete history
            
        Returns:
            Dict containing deletion results
        """
        try:
            cutoff_date = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
            cutoff_iso = datetime.fromtimestamp(cutoff_date).isoformat()
            
            result = self.supabase.table('command_history').delete().lt('created_at', cutoff_iso).execute()
            
            return {
                'success': True,
                'deleted_count': len(result.data) if result.data else 0
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    # Logging
    def log_event(self, level: str, message: str, user_id: Optional[str] = None,
                  session_id: Optional[str] = None, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Log an event to the logs table.
        
        Args:
            level (str): Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message (str): Log message
            user_id (Optional[str]): User ID
            session_id (Optional[str]): Session ID
            metadata (Optional[Dict]): Additional metadata
            
        Returns:
            Dict containing success status
        """
        try:
            log_data = {
                'level': level.upper(),
                'message': message,
                'user_id': user_id,
                'session_id': session_id,
                'metadata': metadata or {},
                'created_at': datetime.now().isoformat()
            }
            
            result = self.supabase.table('logs').insert(log_data).execute()
            
            return {
                'success': True,
                'logged': len(result.data) > 0
            }
            
        except Exception as e:
            print(f"Warning: Failed to log event: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_recent_logs(self, level: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent log entries.
        
        Args:
            level (Optional[str]): Filter by log level
            limit (int): Maximum number of records to return
            
        Returns:
            List of log records
        """
        try:
            query = self.supabase.table('logs').select('*')
            
            if level:
                query = query.eq('level', level.upper())
            
            result = query.order('created_at', desc=True).limit(limit).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            print(f"Error getting logs: {e}")
            return []
    
    # Health Check
    def health_check(self) -> Dict[str, Any]:
        """
        Check database connectivity and health.
        
        Returns:
            Dict containing health status
        """
        try:
            # Try a simple query to check connectivity
            result = self.supabase.table('users').select('id').limit(1).execute()
            
            return {
                'success': True,
                'message': 'Database connection healthy',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }