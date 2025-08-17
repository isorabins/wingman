#!/usr/bin/env python3
"""
Task 1 Environment Verification Runner

Simple script to run Task 1 verification and display results in a user-friendly format.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add the task verification directory to the path
sys.path.append(str(Path(__file__).parent))

from task_01_environment import verify_task_01_environment


def print_verification_results(results):
    """Print verification results in a user-friendly format"""
    
    print("\n" + "="*80)
    print(f"🔍 TASK 1 VERIFICATION RESULTS")
    print("="*80)
    
    print(f"\nTask: {results['task_name']}")
    print(f"Overall Status: {results['overall_status'].upper()}")
    print(f"Verification Time: {results['verification_time']:.2f} seconds")
    print(f"Timestamp: {results['timestamp']}")
    
    # Categorize checks
    passed_checks = []
    failed_checks = []
    error_checks = []
    
    for check_name, check_data in results['checks'].items():
        if check_data['status'] == 'pass':
            passed_checks.append((check_name, check_data))
        elif check_data['status'] == 'fail':
            failed_checks.append((check_name, check_data))
        else:
            error_checks.append((check_name, check_data))
    
    # Print passed checks
    if passed_checks:
        print(f"\n✅ PASSED CHECKS ({len(passed_checks)}):")
        print("-" * 40)
        for name, data in passed_checks:
            print(f"  ✅ {name}: {data['description']}")
            if data.get('details'):
                print(f"     → {data['details']}")
    
    # Print failed checks
    if failed_checks:
        print(f"\n❌ FAILED CHECKS ({len(failed_checks)}):")
        print("-" * 40)
        for name, data in failed_checks:
            print(f"  ❌ {name}: {data['description']}")
            print(f"     → Error: {data.get('error', 'Unknown error')}")
    
    # Print error checks
    if error_checks:
        print(f"\n🔥 ERROR CHECKS ({len(error_checks)}):")
        print("-" * 40)
        for name, data in error_checks:
            print(f"  🔥 {name}: {data['description']}")
            print(f"     → Error: {data.get('error', 'Unknown error')}")
    
    # Print action items
    if results.get('action_items'):
        print(f"\n📋 ACTION ITEMS ({len(results['action_items'])}):")
        print("-" * 40)
        for i, item in enumerate(results['action_items'], 1):
            print(f"  {i}. {item}")
    
    # Print summary
    print("\n" + "="*80)
    total_checks = len(results['checks'])
    passed_count = len(passed_checks)
    failed_count = len(failed_checks)
    error_count = len(error_checks)
    
    print(f"📊 SUMMARY: {passed_count}/{total_checks} checks passed")
    
    if results['overall_status'] == 'pass':
        print("🎉 All critical requirements met! Environment ready for development.")
    elif results['overall_status'] == 'fail':
        print("⚠️  Some requirements not met. Please address the action items above.")
    else:
        print("🔧 Environment partially configured. Check failed items above.")
    
    print("="*80)


async def main():
    """Main function to run verification and display results"""
    try:
        print("🚀 Running Task 1 Environment Setup & Dependencies Verification...")
        results = await verify_task_01_environment()
        print_verification_results(results)
        
        # Return appropriate exit code
        if results['overall_status'] in ['pass', 'partial']:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Verification failed with error: {str(e)}")
        print("Please check your environment setup and try again.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())