#!/usr/bin/env python3
"""
Test script for multi-command functionality
"""

import sys
import os
sys.path.append('backend')

from ai_interpreter import AIInterpreter
from command_executor import CommandExecutor
from command_parser import CommandParser
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env')

def test_multi_command():
    """Test the full multi-command pipeline"""
    print("🧪 Testing Multi-Command Functionality")
    print("=" * 50)
    
    # Initialize components
    ai_interpreter = AIInterpreter()
    command_executor = CommandExecutor()
    command_parser = CommandParser()
    
    # Reset environment
    print("🔄 Resetting test environment...")
    command_executor.execute('rm', ['-f', 'test1'], 'terminal_command')
    
    # Test input
    user_input = "create a new folder called test1 and move file1.txt into it"
    print(f"📝 User input: '{user_input}'")
    
    # Step 1: Parse command
    print("\n🔍 Step 1: Parsing command...")
    parsed_result = command_parser.parse(user_input)
    print(f"   Parse result: {parsed_result}")
    
    # Step 2: AI interpretation (if natural language)
    if parsed_result['type'] == 'natural_language':
        print("\n🤖 Step 2: AI interpretation...")
        ai_result = ai_interpreter.interpret(user_input)
        print(f"   AI result: {ai_result}")
        
        if ai_result['success']:
            ai_command = ai_result['command']
            print(f"   ✅ AI generated: '{ai_command}'")
            
            # Step 3: Execute multi-command
            print("\n⚡ Step 3: Executing multi-command...")
            if '&&' in ai_command:
                execution_result = command_executor.execute(
                    ai_command.split()[0],
                    ai_command.split()[1:],
                    'ai_generated'
                )
            else:
                parsed_ai = command_parser.parse(ai_command)
                execution_result = command_executor.execute(
                    parsed_ai['command'],
                    parsed_ai['args'],
                    parsed_ai['type']
                )
            
            print(f"   Execution result: {execution_result}")
            
            # Step 4: Verify results
            print("\n🔍 Step 4: Verifying results...")
            ls_result = command_executor.execute('ls', [], 'terminal_command')
            print(f"   Files: {ls_result['output']}")
            
            if 'test1' in ls_result['output']:
                ls_test1 = command_executor.execute('ls', ['test1'], 'terminal_command')
                print(f"   Files in test1: {ls_test1['output']}")
                
                if 'file1.txt' in ls_test1['output']:
                    print("   ✅ SUCCESS: file1.txt moved to test1/")
                else:
                    print("   ❌ FAILED: file1.txt not found in test1/")
            else:
                print("   ❌ FAILED: test1 directory not created")
        else:
            print(f"   ❌ AI interpretation failed: {ai_result['error']}")
    else:
        print(f"   ❌ Command was not recognized as natural language: {parsed_result}")

if __name__ == "__main__":
    try:
        test_multi_command()
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()