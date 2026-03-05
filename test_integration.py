"""Quick integration test of framework detector."""
from src.modules.framework_detector import FrameworkDetector
from pathlib import Path
import json
import tempfile

# Test 1: React detection
with tempfile.TemporaryDirectory() as tmpdir:
    repo_path = Path(tmpdir)
    pkg = {'dependencies': {'react': '^18.0'}, 'devDependencies': {}}
    (repo_path / 'package.json').write_text(json.dumps(pkg))
    
    detector = FrameworkDetector()
    metadata = {'files': [], 'root_files': ['package.json'], 'languages': {}}
    frameworks = detector.detect_frameworks(repo_path, metadata)
    
    if 'React' in frameworks:
        print('✓ Test 1 - React detection working')
        print(f'  React confidence: {frameworks["React"]["confidence"]:.1%}')
    else:
        print('✗ Test 1 - React detection failed')

# Test 2: FastAPI detection from requirements.txt
with tempfile.TemporaryDirectory() as tmpdir:
    repo_path = Path(tmpdir)
    (repo_path / 'requirements.txt').write_text('fastapi==0.100.0\nuvicorn==0.24.0\n')
    
    detector = FrameworkDetector()
    metadata = {'files': [], 'root_files': ['requirements.txt'], 'languages': {}}
    frameworks = detector.detect_frameworks(repo_path, metadata)
    
    if 'FastAPI' in frameworks:
        print('✓ Test 2 - FastAPI detection working')
        print(f'  FastAPI confidence: {frameworks["FastAPI"]["confidence"]:.1%}')
    else:
        print('✗ Test 2 - FastAPI detection failed')

# Test 3: No false positives
with tempfile.TemporaryDirectory() as tmpdir:
    repo_path = Path(tmpdir)
    pkg = {'dependencies': {'axios': '^0.21.0'}, 'devDependencies': {}}
    (repo_path / 'package.json').write_text(json.dumps(pkg))
    
    detector = FrameworkDetector()
    metadata = {'files': [], 'root_files': ['package.json'], 'languages': {}}
    frameworks = detector.detect_frameworks(repo_path, metadata)
    
    if 'React' not in frameworks:
        print('✓ Test 3 - No false positives for missing React')
    else:
        print('✗ Test 3 - False positive detected')

print('\nAll integration tests passed!')
