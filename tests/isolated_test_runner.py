#!/usr/bin/env python3
"""
Isolated test runner for Earthworm.

Runs each test file in a separate subprocess to identify
which test causes segmentation faults in the full suite.
"""

import subprocess
import sys
import os
import signal
import time
import json
from pathlib import Path
from typing import List, Dict, Tuple

os.environ['QT_QPA_PLATFORM'] = 'offscreen'

class IsolatedTestRunner:
    """Run tests in isolation to identify segfaults."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.test_dir = self.project_root / 'tests'
        self.results = {}
        self.segfault_tests = []
        
    def find_test_files(self) -> List[Path]:
        """Find all Python test files."""
        test_files = []
        exclude_files = {
            'conftest.py',
            'test_core_logic.py',  # Known import error
            'test_ui_smoke.py',    # Skipped
            'test_visual_regression.py',  # Not implemented
            'test_pilot_wrapper.py',  # Our new wrapper
            'isolated_test_runner.py',  # This file
        }
        
        for test_file in self.test_dir.glob('test_*.py'):
            if test_file.name not in exclude_files:
                test_files.append(test_file)
        
        # Also check subdirectories
        for subdir in self.test_dir.iterdir():
            if subdir.is_dir():
                for test_file in subdir.glob('test_*.py'):
                    if test_file.name not in exclude_files:
                        test_files.append(test_file)
        
        return sorted(test_files)
    
    def run_test_isolated(self, test_file: Path) -> Dict:
        """Run a single test file in isolated subprocess."""
        print(f"\n{'='*80}")
        print(f"🧪 Running: {test_file.relative_to(self.project_root)}")
        print(f"{'='*80}")
        
        cmd = [
            sys.executable, '-m', 'pytest',
            str(test_file),
            '-x',  # Stop on first failure
            '--tb=short',
            '-q'
        ]
        
        start_time = time.time()
        segfault = False
        timeout = False
        
        try:
            # Run with timeout
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60  # 60 second timeout per test
            )
            
            elapsed = time.time() - start_time
            
            # Check for segfault
            if result.returncode == -signal.SIGSEGV:
                segfault = True
            elif "segmentation fault" in result.stderr.lower():
                segfault = True
            elif "Segmentation fault" in result.stderr:
                segfault = True
            elif result.returncode < 0:
                segfault = True
            
            # Parse results
            output_lines = result.stdout.split('\n')
            passed = sum('passed' in line.lower() for line in output_lines)
            failed = sum('failed' in line.lower() for line in output_lines)
            errors = sum('error' in line.lower() for line in output_lines)
            
            result_data = {
                'file': str(test_file.relative_to(self.project_root)),
                'segfault': segfault,
                'timeout': timeout,
                'elapsed': elapsed,
                'exit_code': result.returncode,
                'passed': passed,
                'failed': failed,
                'errors': errors,
                'stderr_snippet': result.stderr[-500:] if result.stderr else '',
            }
            
            if segfault:
                print(f"❌ SEGFAULT detected in {test_file.name}")
                self.segfault_tests.append(str(test_file))
                print(f"Stderr (last 200 chars):\n{result.stderr[-200:]}")
            elif failed > 0 or errors > 0:
                print(f"⚠️  Test failures/errors: {failed} failed, {errors} errors")
            else:
                print(f"✅ PASSED: {passed} tests in {elapsed:.1f}s")
            
            return result_data
            
        except subprocess.TimeoutExpired:
            elapsed = time.time() - start_time
            print(f"⏰ TIMEOUT after {elapsed:.1f}s")
            return {
                'file': str(test_file.relative_to(self.project_root)),
                'segfault': False,
                'timeout': True,
                'elapsed': elapsed,
                'exit_code': None,
                'passed': 0,
                'failed': 0,
                'errors': 0,
                'stderr_snippet': 'TIMEOUT',
            }
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ EXCEPTION: {e}")
            return {
                'file': str(test_file.relative_to(self.project_root)),
                'segfault': False,
                'timeout': False,
                'elapsed': elapsed,
                'exit_code': None,
                'passed': 0,
                'failed': 0,
                'errors': 0,
                'stderr_snippet': str(e),
            }
    
    def run_all_tests_isolated(self):
        """Run all tests in isolation."""
        test_files = self.find_test_files()
        
        print(f"Found {len(test_files)} test files to run in isolation")
        print("Excluding: conftest.py, test_core_logic.py, test_ui_smoke.py, test_visual_regression.py")
        
        for i, test_file in enumerate(test_files, 1):
            print(f"\n[{i}/{len(test_files)}] ", end='')
            result = self.run_test_isolated(test_file)
            self.results[result['file']] = result
            
            # Brief pause between tests
            if i < len(test_files):
                time.sleep(0.5)
    
    def generate_report(self):
        """Generate comprehensive report."""
        print(f"\n{'='*80}")
        print("📊 ISOLATED TEST RUNNER - FINAL REPORT")
        print(f"{'='*80}")
        
        total_tests = len(self.results)
        segfault_tests = [f for f, r in self.results.items() if r['segfault']]
        timeout_tests = [f for f, r in self.results.items() if r['timeout']]
        failing_tests = [f for f, r in self.results.items() if r['failed'] > 0 or r['errors'] > 0]
        passing_tests = [f for f, r in self.results.items() if not r['segfault'] and not r['timeout'] and r['failed'] == 0 and r['errors'] == 0]
        
        print(f"\n📈 Summary:")
        print(f"  Total test files: {total_tests}")
        print(f"  ✅ Passing: {len(passing_tests)}")
        print(f"  ❌ Segfaults: {len(segfault_tests)}")
        print(f"  ⏰ Timeouts: {len(timeout_tests)}")
        print(f"  ⚠️  Failing (non-segfault): {len(failing_tests)}")
        
        if segfault_tests:
            print(f"\n🔴 SEGFAULT DETECTED IN:")
            for test_file in segfault_tests:
                result = self.results[test_file]
                print(f"  • {test_file}")
                print(f"    Exit code: {result['exit_code']}, Elapsed: {result['elapsed']:.1f}s")
                if result['stderr_snippet']:
                    print(f"    Error: {result['stderr_snippet'][:100]}...")
        
        if timeout_tests:
            print(f"\n⏰ TIMEOUTS:")
            for test_file in timeout_tests:
                result = self.results[test_file]
                print(f"  • {test_file} ({result['elapsed']:.1f}s)")
        
        if failing_tests and not segfault_tests:
            print(f"\n⚠️  NON-SEGFAULT FAILURES:")
            for test_file in failing_tests:
                result = self.results[test_file]
                print(f"  • {test_file}: {result['failed']} failed, {result['errors']} errors")
        
        # Save detailed results
        report_file = self.project_root / 'test_isolation_report.json'
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        if segfault_tests:
            print(f"\n❌ SEGFAULTS IDENTIFIED - Test suite interaction issue confirmed")
            print(f"   Files causing segfaults: {', '.join(segfault_tests)}")
            return False
        else:
            print(f"\n✅ NO SEGFAULTS in isolated runs - issue is test suite interaction")
            return True


def main():
    """Main entry point."""
    runner = IsolatedTestRunner()
    
    try:
        runner.run_all_tests_isolated()
        success = runner.generate_report()
        
        if success:
            print("\n✅ Isolated test run completed without segfaults")
            print("   Issue appears to be test suite interaction, not individual tests")
            sys.exit(0)
        else:
            print("\n❌ Segfaults detected in isolated tests")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()