#!/usr/bin/env python3
"""Test diagram generation with a real repository."""

import json
import requests
import time

API_URL = "http://127.0.0.1:8001"

print("=" * 70)
print("TESTING DIAGRAM GENERATION FEATURE")
print("=" * 70)

# Test the analyze endpoint with diagram generation enabled
print("\n1. Testing /api/analyze endpoint with diagram generation...")
print("-" * 70)

analyze_request = {
    "repo_url": "https://github.com/pallets/flask",
    "include_diagrams": True
}

print(f"\nRequest: POST /api/analyze")
print(f"Payload: {json.dumps(analyze_request, indent=2)}")

try:
    response = requests.post(
        f"{API_URL}/api/analyze",
        json=analyze_request,
        timeout=120
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✓ Analysis successful (Status: {response.status_code})")
        
        # Display response structure
        print(f"\nResponse structure:")
        print(f"  - status: {data.get('status')}")
        print(f"  - message: {data.get('message')}")
        
        metadata = data.get('metadata', {})
        print(f"\nMetadata summary:")
        print(f"  - repository_name: {metadata.get('repository_name')}")
        print(f"  - primary_language: {metadata.get('primary_language')}")
        frameworks_list = metadata.get('frameworks', [])
        if isinstance(frameworks_list, list):
            frameworks_str = ', '.join(frameworks_list[:5])
        else:
            frameworks_str = str(frameworks_list)[:100]
        print(f"  - frameworks: {frameworks_str}")
        
        # Check for diagrams
        diagrams = data.get('diagrams', {})
        if diagrams:
            print(f"\n✓ DIAGRAMS GENERATED:")
            for format_type in ['mermaid', 'graphviz', 'json']:
                if format_type in diagrams:
                    diagram_content = diagrams[format_type]
                    if isinstance(diagram_content, str):
                        preview = diagram_content[:200] + "..." if len(diagram_content) > 200 else diagram_content
                    else:
                        preview = str(diagram_content)[:200] + "..."
                    print(f"  ✓ {format_type.upper()}: {len(str(diagram_content))} chars")
                    print(f"    Preview: {preview}")
        else:
            print(f"\n✗ No diagrams generated in response")
            
        analysis = data.get('analysis', {})
        if analysis:
            print(f"\n✓ AI Analysis available:")
            print(f"  - Status: {analysis.get('status')}")
            
    else:
        print(f"✗ API returned status {response.status_code}")
        print(f"Response: {response.text}")
        
except requests.RequestException as e:
    print(f"✗ Request failed: {e}")
    
print("\n" + "=" * 70)
print("DIAGRAM GENERATION TEST COMPLETE")
print("=" * 70)
