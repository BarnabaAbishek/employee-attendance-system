#!/usr/bin/env python3
"""
Setup script for Employee Attendance System
Run: python setup.py
"""

import os
import sys
import subprocess

def print_color(text, color='green'):
    """Print colored text"""
    colors = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'end': '\033[0m'
    }
    print(f"{colors.get(color, '')}{text}{colors['end']}")

def check_prerequisites():
    """Check if Python and pip are installed"""
    print_color("🔍 Checking prerequisites...", 'blue')
    
    # Check Python version
    try:
        python_version = subprocess.check_output(
            [sys.executable, '--version'], 
            stderr=subprocess.STDOUT
        ).decode().strip()
        print_color(f"✓ {python_version}", 'green')
    except:
        print_color("✗ Python not found! Install Python 3.8+", 'red')
        sys.exit(1)
    
    # Check pip
    try:
        pip_version = subprocess.check_output(
            ['pip', '--version'], 
            stderr=subprocess.STDOUT
        ).decode().strip().split('\n')[0]
        print_color(f"✓ {pip_version}", 'green')
    except:
        print_color("✗ pip not found! Install pip", 'red')
        sys.exit(1)

def create_virtual_environment():
    """Create virtual environment"""
    print_color("\n🐍 Creating virtual environment...", 'blue')
    
    if not os.path.exists('venv'):
        try:
            subprocess.run([sys.executable, '-m', 'venv', 'venv'], check=True)
            print_color("✓ Virtual environment created", 'green')
        except:
            print_color("✗ Failed to create virtual environment", 'red')
    else:
        print_color("✓ Virtual environment already exists", 'yellow')

def install_dependencies():
    """Install Python dependencies"""
    print_color("\n📦 Installing dependencies...", 'blue')
    
    # Determine pip command based on OS
    pip_cmd = 'venv/Scripts/pip' if os.name == 'nt' else 'venv/bin/pip'
    
    try:
        subprocess.run([pip_cmd, 'install', '-r', 'requirements.txt'], check=True)
        print_color("✓ Dependencies installed successfully", 'green')
    except:
        print_color("✗ Failed to install dependencies", 'red')

def setup_firebase():
    """Setup Firebase instructions"""
    print_color("\n🔥 Firebase Setup Instructions:", 'blue')
    print("=" * 50)
    print("1. Go to Firebase Console: https://console.firebase.google.com/")
    print("2. Create a new project: 'employee-attendance-system'")
    print("3. Enable Firestore Database")
    print("4. Enable Authentication (Email/Password)")
    print("5. Go to Project Settings > Service Accounts")
    print("6. Generate new private key")
    print("7. Save as 'serviceAccountKey.json' in project root")
    print("8. Copy your Firebase config for web app")
    print("=" * 50)

def create_env_file():
    """Create .env file template"""
    print_color("\n🔧 Creating environment file...", 'blue')
    
    env_content = """# Flask Configuration
SECRET_KEY=your-secret-key-here-change-in-production
FLASK_ENV=development

# Firebase Configuration (for production)
# FIREBASE_CONFIG='{"type": "service_account", ...}'
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print_color("✓ .env file created", 'green')
    print("⚠️  Remember to add your actual Firebase config in production")

def run_application():
    """Run the Flask application"""
    print_color("\n🚀 Starting application...", 'blue')
    
    # Determine Python command based on OS
    python_cmd = 'venv/Scripts/python' if os.name == 'nt' else 'venv/bin/python'
    
    print("\nTo run the application:")
    print(f"1. Activate virtual environment:")
    print(f"   Windows: venv\\Scripts\\activate")
    print(f"   Mac/Linux: source venv/bin/activate")
    print(f"2. Run: {python_cmd} app.py")
    print(f"3. Open: http://localhost:5000")
    
    print_color("\n🎉 Setup completed successfully!", 'green')

def main():
    """Main setup function"""
    print_color("=" * 60, 'yellow')
    print_color("   EMPLOYEE ATTENDANCE SYSTEM - SETUP", 'yellow')
    print_color("=" * 60, 'yellow')
    
    check_prerequisites()
    create_virtual_environment()
    install_dependencies()
    setup_firebase()
    create_env_file()
    run_application()

if __name__ == '__main__':
    main()