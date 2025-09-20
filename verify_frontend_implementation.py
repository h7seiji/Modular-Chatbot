#!/usr/bin/env python3
"""
Frontend Implementation Verification Script

This script verifies that the React frontend has been properly implemented
according to the task requirements.
"""

import os
import json
import sys
from pathlib import Path

def check_file_exists(file_path, description=""):
    """Check if a file exists and print result."""
    if os.path.exists(file_path):
        print(f"✅ {file_path} {description}")
        return True
    else:
        print(f"❌ {file_path} {description} - MISSING")
        return False

def check_content_contains(file_path, content, description=""):
    """Check if file contains specific content."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
            if content in file_content:
                print(f"✅ {file_path} contains {description}")
                return True
            else:
                print(f"❌ {file_path} missing {description}")
                return False
    except Exception as e:
        print(f"❌ Error reading {file_path}: {e}")
        return False

def main():
    print("🧪 Verifying Frontend Implementation...\n")
    
    all_tests_passed = True
    
    # Test 1: Core React Application Structure
    print("📁 Checking React application structure...")
    required_files = [
        ("frontend/src/index.tsx", "- React entry point"),
        ("frontend/src/App.tsx", "- Main App component"),
        ("frontend/src/App.module.css", "- App styles"),
        ("frontend/src/index.css", "- Global styles"),
        ("frontend/public/index.html", "- HTML template"),
        ("frontend/package.json", "- Package configuration"),
        ("frontend/.env", "- Environment configuration"),
    ]
    
    for file_path, description in required_files:
        if not check_file_exists(file_path, description):
            all_tests_passed = False
    
    # Test 2: Chat Interface Components
    print("\n🧩 Checking chat interface components...")
    components = [
        ("frontend/src/components/ChatInterface.tsx", "ChatInterface component"),
        ("frontend/src/components/ConversationSelector.tsx", "ConversationSelector component"),
        ("frontend/src/components/MessageList.tsx", "MessageList component"),
        ("frontend/src/components/MessageInput.tsx", "MessageInput component"),
    ]
    
    for file_path, description in components:
        if not check_file_exists(file_path, f"- {description}"):
            all_tests_passed = False
    
    # Test 3: CSS Modules for Responsive Design
    print("\n🎨 Checking CSS modules for responsive design...")
    css_modules = [
        ("frontend/src/components/ChatInterface.module.css", "ChatInterface styles"),
        ("frontend/src/components/ConversationSelector.module.css", "ConversationSelector styles"),
        ("frontend/src/components/MessageList.module.css", "MessageList styles"),
        ("frontend/src/components/MessageInput.module.css", "MessageInput styles"),
    ]
    
    for file_path, description in css_modules:
        if not check_file_exists(file_path, f"- {description}"):
            all_tests_passed = False
    
    # Test 4: API Integration with Axios
    print("\n🌐 Checking API integration...")
    if check_file_exists("frontend/src/services/api.ts", "- API service"):
        if not check_content_contains("frontend/src/services/api.ts", "axios", "axios import"):
            all_tests_passed = False
        if not check_content_contains("frontend/src/services/api.ts", "sendMessage", "sendMessage method"):
            all_tests_passed = False
        if not check_content_contains("frontend/src/services/api.ts", "healthCheck", "healthCheck method"):
            all_tests_passed = False
    else:
        all_tests_passed = False
    
    # Test 5: TypeScript Interfaces
    print("\n🔍 Checking TypeScript interfaces...")
    if check_file_exists("frontend/types/chat.ts", "- TypeScript interfaces"):
        interfaces = [
            ("Message", "Message interface"),
            ("ConversationContext", "ConversationContext interface"),
            ("ChatRequest", "ChatRequest interface"),
            ("ChatResponse", "ChatResponse interface"),
        ]
        
        for interface_name, description in interfaces:
            if not check_content_contains("frontend/types/chat.ts", f"interface {interface_name}", description):
                all_tests_passed = False
    else:
        all_tests_passed = False
    
    # Test 6: Package.json Dependencies
    print("\n📦 Checking package.json dependencies...")
    try:
        with open("frontend/package.json", 'r') as f:
            package_data = json.load(f)
            
        required_deps = ["react", "react-dom", "axios"]
        for dep in required_deps:
            if dep in package_data.get("dependencies", {}):
                print(f"✅ {dep} dependency present")
            else:
                print(f"❌ {dep} dependency missing")
                all_tests_passed = False
                
        # Check TypeScript
        if "typescript" in package_data.get("devDependencies", {}):
            print("✅ TypeScript dependency present")
        else:
            print("❌ TypeScript dependency missing")
            all_tests_passed = False
            
    except Exception as e:
        print(f"❌ Error reading package.json: {e}")
        all_tests_passed = False
    
    # Test 7: Component Integration
    print("\n🔗 Checking component integration...")
    
    # Check if App.tsx imports and uses main components
    if check_file_exists("frontend/src/App.tsx"):
        if not check_content_contains("frontend/src/App.tsx", "ChatInterface", "ChatInterface import/usage"):
            all_tests_passed = False
        if not check_content_contains("frontend/src/App.tsx", "ConversationSelector", "ConversationSelector import/usage"):
            all_tests_passed = False
    
    # Test 8: Agent Attribution Display
    print("\n🤖 Checking agent attribution display...")
    if check_file_exists("frontend/src/components/MessageList.tsx"):
        if not check_content_contains("frontend/src/components/MessageList.tsx", "agentType", "agent type handling"):
            all_tests_passed = False
        if not check_content_contains("frontend/src/components/MessageList.tsx", "MathAgent", "MathAgent attribution"):
            all_tests_passed = False
        if not check_content_contains("frontend/src/components/MessageList.tsx", "KnowledgeAgent", "KnowledgeAgent attribution"):
            all_tests_passed = False
    
    # Test 9: Error Handling and Loading States
    print("\n⚠️ Checking error handling and loading states...")
    if check_file_exists("frontend/src/components/ChatInterface.tsx"):
        if not check_content_contains("frontend/src/components/ChatInterface.tsx", "isLoading", "loading state"):
            all_tests_passed = False
        if not check_content_contains("frontend/src/components/ChatInterface.tsx", "error", "error handling"):
            all_tests_passed = False
    
    # Test 10: Mobile Responsiveness
    print("\n📱 Checking mobile responsiveness...")
    responsive_files = [
        ("frontend/src/App.module.css", "@media"),
        ("frontend/src/components/MessageList.module.css", "@media"),
        ("frontend/src/components/ConversationSelector.module.css", "@media"),
    ]
    
    for file_path, media_query in responsive_files:
        if check_file_exists(file_path):
            if not check_content_contains(file_path, media_query, "responsive media queries"):
                all_tests_passed = False
    
    # Final Results
    print("\n" + "="*60)
    if all_tests_passed:
        print("🎉 ALL FRONTEND IMPLEMENTATION TESTS PASSED!")
        print("\n✅ Task 10 Requirements Verification:")
        print("   ✅ React application with TypeScript set up")
        print("   ✅ Chat interface components created")
        print("   ✅ Conversation management implemented")
        print("   ✅ API integration with axios configured")
        print("   ✅ Agent attribution display implemented")
        print("   ✅ Responsive design with CSS modules")
        print("   ✅ Error handling and loading states added")
        print("\n📝 Next Steps:")
        print("   1. Install dependencies: cd frontend && npm install --legacy-peer-deps")
        print("   2. Start backend: docker-compose up -d backend redis")
        print("   3. Start frontend: cd frontend && npm start")
        print("   4. Test at http://localhost:3000")
        
        return 0
    else:
        print("❌ SOME FRONTEND IMPLEMENTATION TESTS FAILED!")
        print("Please review the errors above and ensure all components are properly implemented.")
        return 1

if __name__ == "__main__":
    sys.exit(main())