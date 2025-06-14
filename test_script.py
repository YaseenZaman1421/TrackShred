#!/usr/bin/env python3
"""
Basic test script for TrackShred
Creates test files and runs TrackShred operations on them
"""

import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

class TrackShredTester:
    def __init__(self):
        self.test_dir = None
        self.trackshred_path = None
        self.results = []
    
    def setup(self):
        """Setup test environment"""
        print("🧪 Setting up test environment...")
        
        # Find trackshred executable
        self.trackshred_path = shutil.which('trackshred')
        if not self.trackshred_path:
            # Try local installation
            local_path = Path.home() / '.local' / 'bin' / 'trackshred'
            if local_path.exists():
                self.trackshred_path = str(local_path)
            else:
                # Try current directory
                current_path = Path('./trackshred.py')
                if current_path.exists():
                    self.trackshred_path = str(current_path)
                else:
                    raise FileNotFoundError("TrackShred executable not found")
        
        print(f"Using TrackShred at: {self.trackshred_path}")
        
        # Create temporary test directory
        self.test_dir = Path(tempfile.mkdtemp(prefix='trackshred_test_'))
        print(f"Test directory: {self.test_dir}")
    
    def create_test_files(self):
        """Create test files with various content"""
        print("📝 Creating test files...")
        
        test_files = {
            'text_file.txt': "This is sensitive text content\nLine 2\nLine 3",
            'binary_file.bin': bytes(range(256)),
            'script_file.sh': "#!/bin/bash\necho 'secret command'\n",
            'config_file.json': '{"secret": "value", "password": "123456"}',
        }
        
        for filename, content in test_files.items():
            file_path = self.test_dir / filename
            if isinstance(content, str):
                file_path.write_text(content)
            else:
                file_path.write_bytes(content)
            print(f"Created: {filename}")
        
        # Create a subdirectory with files
        subdir = self.test_dir / 'subdir'
        subdir.mkdir()
        (subdir / 'nested_file.txt').write_text("Nested sensitive content")
        print("Created: subdir/nested_file.txt")
    
    def run_test(self, test_name, command_args, expect_success=True):
        """Run a single test"""
        print(f"\n🔍 Running test: {test_name}")
        print(f"Command: python3 {self.trackshred_path} {' '.join(command_args)}")
        
        try:
            # Run the command
            cmd = ['python3', self.trackshred_path] + command_args
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            success = (result.returncode == 0) == expect_success
            
            if success:
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
                print(f"Exit code: {result.returncode}")
                print(f"STDOUT:\n{result.stdout}")
                print(f"STDERR:\n{result.stderr}")
            
            self.results.append({
                'test': test_name,
                'success': success,
                'exit_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            })
            
            return success
            
        except subprocess.TimeoutExpired:
            print(f"❌ {test_name}: TIMEOUT")
            self.results.append({
                'test': test_name,
                'success': False,
                'error': 'timeout'
            })
            return False
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            self.results.append({
                'test': test_name,
                'success': False,
                'error': str(e)
            })
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("\n🚀 Running TrackShred tests...")
        
        # Test 1: Version check
        self.run_test("Version Check", ["--version"])
        
        # Test 2: Help output
        self.run_test("Help Output", ["--help"])
        
        # Test 3: Dry run on single file
        test_file = str(self.test_dir / 'text_file.txt')
        self.run_test("Dry Run Single File", ["--target", test_file, "--dry-run"])
        
        # Test 4: Metadata-only mode
        self.run_test("Metadata Only Mode", ["--target", test_file, "--metadata-only", "--dry-run"])
        
        # Test 5: Directory dry run
        self.run_test("Directory Dry Run", ["--target", str(self.test_dir), "--dry-run"])
        
        # Test 6: Deep clean dry run
        self.run_test("Deep Clean Dry Run", ["--deep", "--dry-run"])
        
        # Test 7: Combined operations dry run
        self.run_test("Combined Operations Dry Run", ["--target", test_file, "--deep", "--dry-run"])
        
        # Test 8: Custom shred passes
        self.run_test("Custom Shred Passes", ["--target", test_file, "--shred-passes", "5", "--dry-run"])
        
        # Test 9: Invalid target (should fail)
        self.run_test("Invalid Target", ["--target", "/nonexistent/file"], expect_success=False)
        
        # Test 10: No arguments (should fail)
        self.run_test("No Arguments", [], expect_success=False)
        
        # Test 11: Actual file shredding (create a disposable file)
        disposable_file = self.test_dir / 'disposable.txt'
        disposable_file.write_text("This file will be shredded")
        self.run_test("Actual File Shredding", ["--target", str(disposable_file)])
        
        # Verify the file was actually deleted
        if not disposable_file.exists():
            print("✅ File was successfully deleted")
        else:
            print("❌ File still exists after shredding")
    
    def generate_report(self):
        """Generate test report"""
        print("\n📊 Test Report")
        print("=" * 50)
        
        passed = sum(1 for r in self.results if r['success'])
        total = len(self.results)
        
        print(f"Tests passed: {passed}/{total}")
        print(f"Success rate: {passed/total*100:.1f}%")
        
        print("\nDetailed Results:")
        for result in self.results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"  {status} - {result['test']}")
            if not result['success'] and 'error' in result:
                print(f"    Error: {result['error']}")
        
        return passed == total
    
    def cleanup(self):
        """Clean up test environment"""
        if self.test_dir and self.test_dir.exists():
            print(f"\n🧹 Cleaning up test directory: {self.test_dir}")
            shutil.rmtree(self.test_dir)
    
    def run(self):
        """Run the complete test suite"""
        try:
            self.setup()
            self.create_test_files()
            self.run_all_tests()
            success = self.generate_report()
            return success
        finally:
            self.cleanup()


def main():
    """Main test function"""
    print("🔐 TrackShred Test Suite")
    print("=" * 30)
    
    tester = TrackShredTester()
    
    try:
        success = tester.run()
        if success:
            print("\n🎉 All tests passed!")
            exit(0)
        else:
            print("\n⚠️  Some tests failed!")
            exit(1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
        tester.cleanup()
        exit(130)
    except Exception as e:
        print(f"\n💥 Test suite error: {e}")
        tester.cleanup()
        exit(1)


if __name__ == "__main__":
    main()
