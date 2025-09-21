# Web Terminal with AI Integration

A sophisticated web-based terminal interface with AI-powered natural language command interpretation, built with Flask, SocketIO, and Google Gemini AI.

## Features

🖥️ **Web-Based Terminal Interface**
- Real-time terminal emulation in your browser
- Command history and auto-completion
- Modern terminal aesthetics with syntax highlighting

🤖 **AI-Powered Command Interpretation**
- Natural language to terminal command translation
- Google Gemini AI integration
- Smart command suggestions and help

🔒 **Enterprise-Grade Security**
- Input validation and sanitization
- Rate limiting and abuse prevention
- Dangerous command detection and blocking

📊 **System Monitoring**
- Real-time CPU, memory, and disk usage
- Process monitoring and management
- System information dashboard

💾 **Database Integration**
- Supabase PostgreSQL for data persistence
- User session management
- Command history tracking

## Prerequisites

- Python 3.8 or higher
- A Supabase account (for database)
- A Google AI Studio account (for Gemini API)

## Quick Start

1. **Clone or download the project**

2. **Set up environment variables**
   Create a `.env` file in the project root:
   ```env
   SUPABASE_URL=your_supabase_project_url
   SUPABASE_API_KEY=your_supabase_anon_key
   GEMINI_API_KEY=your_gemini_api_key
   ```

3. **Run the startup script**
   ```bash
   ./start.sh
   ```

4. **Open your browser**
   Navigate to `http://localhost:5000`

## Manual Setup (Alternative)

If you prefer to set up manually:

1. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the server**
   ```bash
   cd backend
   python main.py
   ```

## Usage

### Terminal Commands
Use standard Linux/Unix commands:
```bash
ls -la              # List files
pwd                 # Show current directory
mkdir test          # Create directory
echo "Hello"        # Print text
cat filename        # View file contents
```

### Natural Language Commands
Ask questions in plain English:
```
"show me all files in this directory"
"what is my current location"
"create a new folder called projects"
"display system information"
```

### System Monitoring
Access the system info panel to view:
- CPU usage and load averages
- Memory usage statistics
- Disk space information
- Running processes

## Project Structure

```
shakthi-hack/
├── backend/
│   ├── main.py              # Flask application entry point
│   ├── command_parser.py    # Command parsing logic
│   ├── command_executor.py  # Safe command execution
│   ├── system_monitor.py    # System monitoring
│   ├── database.py          # Supabase integration
│   ├── ai_interpreter.py    # Gemini AI integration
│   └── security.py          # Security validation
├── frontend/
│   ├── index.html           # Main web interface
│   └── static/
│       ├── style.css        # Terminal styling
│       └── terminal.js      # WebSocket client
├── tests/
│   └── integration_test.py  # Integration tests
├── requirements.txt         # Python dependencies
├── start.sh                 # Startup script
└── .env                     # Environment variables
```

## API Endpoints

- `GET /` - Main terminal interface
- `GET /health` - Health check endpoint
- `GET /system-info` - System information API
- `WebSocket /` - Real-time terminal communication

## Security Features

- Input validation and sanitization
- Command blacklist for dangerous operations
- Rate limiting (100 requests per minute)
- IP-based abuse detection
- Secure environment isolation

## Database Schema

The application uses the following Supabase tables:
- `users` - User management
- `command_history` - Command execution history
- `sessions` - User session tracking
- `security_logs` - Security event logging

## Configuration

Key configuration options in the backend modules:
- Rate limiting: 100 requests per minute per IP
- Command timeout: 30 seconds
- Max output size: 10KB per command
- AI confidence threshold: 0.7

## Troubleshooting

**Server won't start:**
- Check that all environment variables are set
- Ensure Python 3.8+ is installed
- Verify all dependencies are installed

**Database connection issues:**
- Verify Supabase URL and API key
- Check network connectivity
- Ensure Supabase project is active

**AI commands not working:**
- Verify Gemini API key is valid
- Check API quota and billing
- Ensure network connectivity to Google AI

## Development

To run tests:
```bash
python tests/integration_test.py
```

To run in development mode:
```bash
export FLASK_ENV=development
export FLASK_DEBUG=1
cd backend
python main.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

For support or questions, please check the project documentation or create an issue in the repository.

---

**Built with ❤️ using Flask, SocketIO, and Google Gemini AI**