#!/usr/bin/env python3
# convert_env_to_yaml.py - Convert .env to .env.yaml

import os
import sys

def convert_env_to_yaml():
    """Convert .env file to .env.yaml format"""
    
    if not os.path.exists('.env'):
        print("❌ Error: .env file not found!")
        sys.exit(1)
    
    env_vars = {}
    
    # Read .env file
    with open('.env', 'r') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if line and not line.startswith('#'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    # Remove quotes if present
                    value = value.strip('"').strip("'")
                    env_vars[key.strip()] = value.strip()
    
    # Write .env.yaml file
    with open('.env.yaml', 'w') as f:
        f.write("# Environment variables for Firebase Functions\n")
        f.write("# Auto-generated from .env file\n\n")
        
        for key, value in env_vars.items():
            # Escape special characters in YAML
            if any(char in value for char in [':', '#', '@', '|', '>', '-']):
                f.write(f'{key}: "{value}"\n')
            else:
                f.write(f'{key}: "{value}"\n')
    
    print("✅ Created .env.yaml file")
    print("\nFound and converted these variables:")
    for key in env_vars:
        if 'TOKEN' in key or 'SECRET' in key or 'PASSWORD' in key:
            print(f"  - {key}: ***hidden***")
        else:
            print(f"  - {key}: {env_vars[key][:20]}..." if len(env_vars[key]) > 20 else f"  - {key}: {env_vars[key]}")

if __name__ == "__main__":
    convert_env_to_yaml()
    print("\n📝 Now run: firebase deploy --only functions")