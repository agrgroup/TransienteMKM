# Let me create a zip file or show you how to access all the rewritten files
import os
from pathlib import Path

print("📁 REWRITTEN CODE FILES CREATED:")
print("=" * 50)

# List all the files that were created in our previous conversation
created_files = [
    'dependencies_fixed.py',
    'config.py',
    'data_extraction.py', 
    'simulation_runner.py',
    'plotting.py',
    'utilities.py',
    'main_application.py',
    'example_config.yaml',
    'example_config.json',
    'README.md',
    'test_setup.py'
]

# Check which files exist and show their status
for filename in created_files:
    if Path(filename).exists():
        size = Path(filename).stat().st_size
        print(f"✅ {filename:<25} ({size:,} bytes)")
    else:
        print(f"❌ {filename:<25} (missing)")

print(f"\nTotal files created: {len([f for f in created_files if Path(f).exists()])}")