"""
Main Flask application for the web-based Python terminal.
This file handles the main application setup, routes, and WebSocket connections.
"""

import os
import sys
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from dotenv import load_dotenv

# Import custom modules
from command_parser import CommandParser
from command_executor import CommandExecutor
from system_monitor import SystemMonitor
from database import DatabaseManager
from ai_interpreter import AIInterpreter
from security import SecurityManager

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, template_folder='../frontend', static_folder='../frontend/static')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Enable CORS for cross-origin requests
CORS(app)

# Initialize SocketIO for real-time communication with gevent async mode
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

# Initialize components
command_parser = CommandParser()
command_executor = CommandExecutor()
system_monitor = SystemMonitor()
database_manager = DatabaseManager()
ai_interpreter = AIInterpreter()
security_manager = SecurityManager()

@app.route('/')
def index():
    """Serve the main terminal interface."""
    return render_template('index.html')

@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'message': 'Web terminal is running'
    })

@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    print('Client connected')
    emit('response', {
        'type': 'system',
        'message': 'Connected to web terminal. Type "help" for available commands.',
        'timestamp': system_monitor.get_current_time()
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    print('Client disconnected')

@socketio.on('command')
def handle_command(data):
    """
    Handle incoming commands from the client.
    This is the main command processing pipeline.
    """
    try:
        user_input = data.get('command', '').strip()
        session_id = data.get('session_id', 'default')
        user_id = data.get('user_id', 'anonymous')
        client_ip = request.environ.get('REMOTE_ADDR', '127.0.0.1')
        
        if not user_input:
            emit('response', {
                'type': 'error',
                'message': 'Empty command received',
                'timestamp': system_monitor.get_current_time()
            })
            return
        
        # Security validation
        validation_result = security_manager.validate_input(user_input, client_ip)
        if not validation_result['valid']:
            emit('response', {
                'type': 'error',
                'message': 'Security validation failed: ' + '; '.join(validation_result['errors']),
                'timestamp': system_monitor.get_current_time()
            })
            return
        
        # Use sanitized input
        sanitized_input = validation_result.get('sanitized_input', user_input)
        
        # Parse command to determine if it's natural language or direct command
        parsed_result = command_parser.parse(sanitized_input)
        
        # If it's natural language, use AI to interpret
        if parsed_result['type'] == 'natural_language':
            ai_result = ai_interpreter.interpret(sanitized_input)
            if ai_result['success']:
                ai_command = ai_result['command']
                emit('response', {
                    'type': 'ai_interpretation',
                    'message': f"AI interpreted: {ai_command}",
                    'timestamp': system_monitor.get_current_time()
                })
                
                # Check if it's a multi-command with &&
                if '&&' in ai_command:
                    # Handle as multi-command directly - pass the full command
                    execution_result = command_executor.execute(
                        'multi_command',  # Special command type
                        [ai_command],     # Pass full command as single argument
                        'ai_generated'
                    )
                else:
                    # Re-parse the AI-generated command for single commands
                    parsed_result = command_parser.parse(ai_command)
                    execution_result = command_executor.execute(
                        parsed_result['command'],
                        parsed_result['args'],
                        parsed_result['type']
                    )
            else:
                emit('response', {
                    'type': 'error',
                    'message': f"AI interpretation failed: {ai_result['error']}",
                    'timestamp': system_monitor.get_current_time()
                })
                return
        else:
            # Execute the direct command
            execution_result = command_executor.execute(
                parsed_result['command'],
                parsed_result['args'],
                parsed_result['type']
            )
        
        # Save command to database
        database_manager.save_command_history(
            user_id=user_id,
            session_id=session_id,
            command=user_input,
            output=execution_result['output'],
            success=execution_result['success']
        )
        
        # Send response to client
        emit('response', {
            'type': 'command_result',
            'success': execution_result['success'],
            'output': execution_result['output'],
            'error': execution_result.get('error'),
            'timestamp': system_monitor.get_current_time()
        })
        
    except Exception as e:
        emit('response', {
            'type': 'error',
            'message': f'Internal server error: {str(e)}',
            'timestamp': system_monitor.get_current_time()
        })

@socketio.on('get_system_info')
def handle_system_info():
    """Handle system information requests."""
    try:
        system_info = system_monitor.get_system_info()
        emit('response', {
            'type': 'system_info',
            'data': system_info,
            'timestamp': system_monitor.get_current_time()
        })
    except Exception as e:
        emit('response', {
            'type': 'error',
            'message': f'Failed to get system info: {str(e)}',
            'timestamp': system_monitor.get_current_time()
        })

@socketio.on('get_command_history')
def handle_command_history(data):
    """Handle command history requests."""
    try:
        user_id = data.get('user_id', 'anonymous')
        session_id = data.get('session_id', 'default')
        limit = data.get('limit', 50)
        
        history = database_manager.get_command_history(
            user_id=user_id,
            session_id=session_id,
            limit=limit
        )
        
        emit('response', {
            'type': 'command_history',
            'data': history,
            'timestamp': system_monitor.get_current_time()
        })
    except Exception as e:
        emit('response', {
            'type': 'error',
            'message': f'Failed to get command history: {str(e)}',
            'timestamp': system_monitor.get_current_time()
        })

if __name__ == '__main__':
    # Initialize database tables
    try:
        database_manager.initialize_tables()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Database initialization failed: {e}")
        # Don't exit on database failure in production - continue without DB
        print("Continuing without database functionality...")
    
    # Start the application
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'development') != 'production'
    host = '0.0.0.0' if os.environ.get('FLASK_ENV') == 'production' else '127.0.0.1'
    
    print(f"Starting web terminal on {host}:{port}")
    print(f"Debug mode: {debug}")
    print(f"Environment: {os.environ.get('FLASK_ENV', 'development')}")
    
    socketio.run(app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)