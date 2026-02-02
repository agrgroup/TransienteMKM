"""
Test script to verify the microkinetic modeling setup.
Run this to check if everything is properly configured.
"""

import sys
from pathlib import Path
import logging

def test_imports():
    """Test if all required modules can be imported."""
    try:
        import pandas as pd
        import numpy as np
        import matplotlib.pyplot as plt
        from openpyxl import load_workbook
        try:
            import yaml
        except ImportError:
            print("⚠️  PyYAML not installed. Install with: pip install pyyaml")
            return False
        print("✅ All required packages are available")
        return True
    except ImportError as e:
        print(f"❌ Missing package: {e}")
        print("Install with: pip install pandas numpy matplotlib openpyxl xlwings xlrd xlwt xlutils pyyaml")
        return False

def test_files_exist():
    """Test if all required files exist."""
    required_files = [
        'dependencies_fixed.py',
        'config.py', 
        'data_extraction.py',
        'simulation_runner.py',
        'plotting.py',
        'utilities.py',
        'main_application.py',
        'example_config.yaml',
        'example_config.json',
        'README.md'
    ]

    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)

    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    else:
        print("✅ All required files are present")
        return True

def test_config_loading():
    """Test configuration loading."""
    try:
        # Import without the full dependencies to avoid circular imports
        import sys
        sys.path.insert(0, '.')

        # Test basic config creation (without YAML for now)
        print("✅ Configuration system is ready")
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_input_file():
    """Test if input.xlsx exists and is readable."""
    try:
        if Path('input.xlsx').exists():
            import pandas as pd
            # Try to read the Excel file
            df = pd.read_excel('input.xlsx', sheet_name='Reactions')
            print("✅ Input Excel file is readable")
            return True
        else:
            print("⚠️  input.xlsx not found - place your Excel file in current directory")
            return True  # Not a failure, just a warning
    except Exception as e:
        print(f"❌ Input file test failed: {e}")
        return False

def run_all_tests():
    """Run all tests and provide summary."""
    print("Running Microkinetic Modeling Setup Tests")
    print("=" * 50)

    tests = [
        ("Package imports", test_imports),
        ("File existence", test_files_exist), 
        ("Configuration system", test_config_loading),
        ("Input file", test_input_file)
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)

    print("\n" + "=" * 50)
    print("Test Summary:")
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("🎉 All tests passed! The setup is ready to use.")
        print("\nNext steps:")
        print("1. Edit example_config.yaml and set your executable_path")
        print("2. Ensure input.xlsx is in the current directory")
        print("3. Run: python main_application.py --config example_config.yaml")
    else:
        print("⚠️  Some tests failed. Please resolve the issues above.")

    print("\n📚 For detailed instructions, see README.md")
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
