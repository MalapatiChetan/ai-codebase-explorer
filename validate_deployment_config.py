#!/usr/bin/env python
"""Validate cloud deployment configuration files."""

import yaml
import json
import os
from pathlib import Path

print('\n' + '='*70)
print('CLOUD DEPLOYMENT CONFIGURATION VALIDATION')
print('='*70 + '\n')

files_to_check = [
    ('docker-compose.yml', 'yaml'),
    ('render.yaml', 'yaml'),
    ('frontend/vercel.json', 'json'),
    ('Dockerfile', 'text'),
    ('.env.render', 'text'),
    ('.env.vercel', 'text'),
    ('frontend/.env.local.example', 'text'),
]

valid_count = 0
issues = []

for filepath, file_type in files_to_check:
    full_path = Path(filepath)
    
    if not full_path.exists():
        issues.append(f"✗ {filepath}: FILE NOT FOUND")
        continue
    
    try:
        if file_type == 'yaml':
            with open(filepath, 'r') as f:
                config = yaml.safe_load(f)
                if config is None:
                    issues.append(f"✗ {filepath}: Empty YAML")
                else:
                    print(f"✓ {filepath}: Valid YAML")
                    valid_count += 1
                    
                    # Show some details
                    if 'services' in config:
                        print(f"  └─ Services: {list(config['services'].keys())}")
                    elif 'buildCommand' in str(config):
                        print(f"  └─ Configuration loaded successfully")
        
        elif file_type == 'json':
            with open(filepath, 'r') as f:
                config = json.load(f)
                print(f"✓ {filepath}: Valid JSON")
                valid_count += 1
                if 'buildCommand' in config:
                    print(f"  └─ Build Command: {config['buildCommand']}")
        
        elif file_type == 'text':
            with open(filepath, 'r') as f:
                content = f.read()
                if len(content) > 0:
                    print(f"✓ {filepath}: Valid file ({len(content)} bytes)")
                    valid_count += 1
                else:
                    issues.append(f"✗ {filepath}: Empty file")
    
    except Exception as e:
        issues.append(f"✗ {filepath}: {type(e).__name__}: {str(e)[:50]}")

print(f"\n{'='*70}")
print(f"VALIDATION RESULTS: {valid_count}/{len(files_to_check)} files valid")
print(f"{'='*70}\n")

if issues:
    print("⚠ Issues found:")
    for issue in issues:
        print(f"  {issue}")
else:
    print("✓ All configuration files are valid!")

print(f"\n{'='*70}\n")
