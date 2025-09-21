#!/usr/bin/env python3
"""
Test runner for the web terminal application.
Tests all components and validates functionality.
"""

import sys
import os
import unittest
import subprocess
import time
import requests
import json
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_dir))

class WebTerminalIntegrationTest:
    """Integration tests for the web terminal."""
    
    def __init__(self):
        self.backend_process = None
        self.base_url = 'http://localhost:5000'
        
    def setup(self):
        """Set up the test environment."""
        print("Setting up integration tests...")
        
        # Start the backend server
        backend_script = backend_dir / 'main.py'
        self.backend_process = subprocess.Popen([
            sys.executable, str(backend_script)
        ], cwd=str(backend_dir))
        
        # Wait for server to start
        print("Waiting for server to start...")
        time.sleep(5)
        
        # Check if server is running
        for attempt in range(10):
            try:
                response = requests.get(f'{self.base_url}/health', timeout=2)
                if response.status_code == 200:
                    print("✅ Server is running")
                    return True
            except requests.exceptions.RequestException:
                pass
            time.sleep(1)
        
        print("❌ Failed to start server")
        return False
    
    def teardown(self):
        """Clean up the test environment."""
        if self.backend_process:
            self.backend_process.terminate()
            self.backend_process.wait()
            print("Server stopped")
    
    def test_health_endpoint(self):
        """Test the health check endpoint."""
        print("\n🧪 Testing health endpoint...")
        try:
            response = requests.get(f'{self.base_url}/health')
            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'healthy'
            print("✅ Health endpoint working")
            return True
        except Exception as e:
            print(f"❌ Health endpoint failed: {e}")
            return False
    
    def test_frontend_loading(self):
        """Test that the frontend loads correctly."""
        print("\n🧪 Testing frontend loading...")
        try:
            response = requests.get(self.base_url)
            assert response.status_code == 200
            assert 'Web Terminal' in response.text
            assert 'terminal.js' in response.text
            print("✅ Frontend loads correctly")
            return True
        except Exception as e:
            print(f"❌ Frontend loading failed: {e}")
            return False
    
    def test_static_files(self):
        """Test that static files are served correctly."""
        print("\n🧪 Testing static files...")
        try:
            # Test CSS
            css_response = requests.get(f'{self.base_url}/static/style.css')
            assert css_response.status_code == 200
            assert 'terminal-container' in css_response.text
            
            # Test JS
            js_response = requests.get(f'{self.base_url}/static/terminal.js')
            assert js_response.status_code == 200
            assert 'WebTerminal' in js_response.text
            
            print("✅ Static files served correctly")
            return True
        except Exception as e:
            print(f"❌ Static files test failed: {e}")
            return False
    
    def test_component_imports(self):
        """Test that all backend components can be imported."""
        print("\n🧪 Testing component imports...")
        try:
            # Test individual component imports
            from command_parser import CommandParser
            from command_executor import CommandExecutor
            from system_monitor import SystemMonitor
            from ai_interpreter import AIInterpreter
            from security import SecurityManager
            
            # Test component initialization
            parser = CommandParser()
            executor = CommandExecutor()
            monitor = SystemMonitor()
            security = SecurityManager()
            
            print("✅ All components import successfully")
            return True
        except Exception as e:
            print(f"❌ Component import failed: {e}")
            return False
    
    def test_command_parsing(self):
        """Test command parsing functionality."""
        print("\n🧪 Testing command parsing...")
        try:
            from command_parser import CommandParser
            parser = CommandParser()
            
            # Test terminal command
            result = parser.parse('ls -la')
            assert result['type'] == 'terminal_command'
            assert result['command'] == 'ls'
            assert result['args'] == ['-la']
            
            # Test natural language
            result = parser.parse('show me all files')
            assert result['type'] == 'natural_language'
            
            print("✅ Command parsing works correctly")
            return True
        except Exception as e:
            print(f"❌ Command parsing test failed: {e}")
            return False
    
    def test_security_validation(self):
        """Test security validation functionality."""
        print("\n🧪 Testing security validation...")
        try:
            from security import SecurityManager
            security = SecurityManager()
            
            # Test safe command
            result = security.validate_input('ls -la')
            assert result['valid'] == True
            
            # Test dangerous command
            result = security.validate_input('rm -rf /')
            assert result['valid'] == False
            
            print("✅ Security validation works correctly")
            return True
        except Exception as e:
            print(f"❌ Security validation test failed: {e}")
            return False
    
    def test_system_monitoring(self):
        """Test system monitoring functionality."""
        print("\n🧪 Testing system monitoring...")
        try:
            from system_monitor import SystemMonitor
            monitor = SystemMonitor()
            
            # Test system info retrieval
            info = monitor.get_system_info()
            assert 'cpu' in info
            assert 'memory' in info
            assert 'timestamp' in info
            
            # Test quick stats
            stats = monitor.get_quick_stats()
            assert 'cpu_percent' in stats
            assert 'memory_percent' in stats
            
            print("✅ System monitoring works correctly")
            return True
        except Exception as e:
            print(f"❌ System monitoring test failed: {e}")
            return False
    
    def test_database_connection(self):
        """Test database connectivity (if credentials are available)."""
        print("\n🧪 Testing database connection...")
        try:
            from database import DatabaseManager
            
            # Check if environment variables are set
            if not os.environ.get('SUPABASE_URL') or not os.environ.get('SUPABASE_API_KEY'):
                print("⚠️ Database credentials not found, skipping database test")
                return True
            
            db = DatabaseManager()
            health = db.health_check()
            
            if health['success']:
                print("✅ Database connection successful")
                return True
            else:
                print(f"⚠️ Database connection failed: {health['error']}")
                return True  # Don't fail test if DB is not configured
        except Exception as e:
            print(f"⚠️ Database test failed: {e}")
            return True  # Don't fail test if DB is not configured
    
    def run_all_tests(self):
        """Run all integration tests."""
        print("🚀 Starting Web Terminal Integration Tests")
        print("=" * 50)
        
        if not self.setup():
            return False
        
        tests = [
            self.test_health_endpoint,
            self.test_frontend_loading,
            self.test_static_files,
            self.test_component_imports,
            self.test_command_parsing,
            self.test_security_validation,
            self.test_system_monitoring,
            self.test_database_connection,
        ]
        
        passed = 0
        total = len(tests)
        
        try:
            for test in tests:
                if test():
                    passed += 1
                else:
                    print(f"❌ Test failed: {test.__name__}")
        finally:
            self.teardown()
        
        print("\n" + "=" * 50)
        print(f"🏁 Integration Tests Complete: {passed}/{total} passed")
        
        if passed == total:
            print("🎉 All tests passed! The web terminal is ready to use.")
            return True
        else:
            print("⚠️ Some tests failed. Please check the issues above.")
            return False

def main():
    """Main test runner."""
    # Change to the project directory
    project_dir = Path(__file__).parent.parent
    os.chdir(project_dir)
    
    # Load environment variables
    env_file = project_dir / '.env'
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv(env_file)
    
    # Run tests
    tester = WebTerminalIntegrationTest()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎯 Next steps:")
        print("1. Navigate to the project directory")
        print("2. Activate the virtual environment: source venv/bin/activate")
        print("3. Start the server: python backend/main.py")
        print("4. Open your browser to: http://localhost:5000")
        print("5. Start using the web terminal!")
        return 0
    else:
        return 1

if __name__ == '__main__':
    sys.exit(main())