#!/usr/bin/env python3
"""
Task 11 Chat Verification Runner

Executes the Task 11 verification module and generates a comprehensive report
of the buddy chat implementation status.
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.task_verification.task_11_chat import verify_task_11_chat

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_verification_report(results: dict):
    """Print a formatted verification report"""
    
    print("=" * 80)
    print(f"🎯 TASK 11 VERIFICATION REPORT - {results['task_name']}")
    print("=" * 80)
    print(f"Overall Status: {results['overall_status'].upper()}")
    print(f"Verification Time: {results.get('verification_time', 0):.2f} seconds")
    print(f"Timestamp: {results['timestamp']}")
    print()
    
    # Check summary
    total_checks = len(results.get('checks', {}))
    passed_checks = sum(1 for check in results.get('checks', {}).values() if check['status'] == 'pass')
    failed_checks = sum(1 for check in results.get('checks', {}).values() if check['status'] == 'fail')
    error_checks = sum(1 for check in results.get('checks', {}).values() if check['status'] == 'error')
    
    print(f"📊 CHECK SUMMARY:")
    print(f"   Total Checks: {total_checks}")
    print(f"   ✅ Passed: {passed_checks}")
    print(f"   ❌ Failed: {failed_checks}")
    print(f"   🔥 Errors: {error_checks}")
    print()
    
    # Group checks by category
    categories = {
        'Database': ['chat_messages_table', 'chat_read_timestamps_table', 'database_indexes', 'rls_policies'],
        'API Endpoints': ['get_messages_endpoint', 'send_message_endpoint', 'api_authentication', 'message_validation', 'rate_limiting'],
        'Frontend': ['chat_page_exists', 'chat_page_structure', 'typescript_interfaces', 'ui_components'],
        'Venue Suggestions': ['venue_suggestions_panel', 'venue_categories'],
        'Features': ['polling_mechanism', 'scroll_management', 'character_counter', 'error_handling'],
        'Security': ['participant_access', 'message_sanitization']
    }
    
    for category, check_names in categories.items():
        print(f"📋 {category.upper()} CHECKS:")
        category_checks = {name: results['checks'].get(name) for name in check_names if name in results.get('checks', {})}
        
        for check_name, check_data in category_checks.items():
            if not check_data:
                continue
                
            status = check_data['status']
            if status == 'pass':
                status_icon = "✅"
            elif status == 'fail':
                status_icon = "❌"
            else:
                status_icon = "🔥"
            
            print(f"   {status_icon} {check_name}: {status.upper()}")
            if check_data.get('details'):
                print(f"      └─ {check_data['details']}")
            if check_data.get('error'):
                print(f"      └─ Error: {check_data['error']}")
        print()
    
    # Action items
    if results.get('action_items'):
        print("🔧 ACTION ITEMS:")
        for i, action in enumerate(results['action_items'], 1):
            print(f"   {i}. {action}")
        print()
    
    # Overall assessment
    if results['overall_status'] == 'pass':
        print("🎉 TASK 11 VERIFICATION: COMPLETE")
        print("   All buddy chat implementation requirements verified successfully!")
    elif results['overall_status'] == 'partial':
        print("⚠️  TASK 11 VERIFICATION: PARTIAL")
        print("   Most requirements met, but some issues need attention.")
    elif results['overall_status'] == 'fail':
        print("❌ TASK 11 VERIFICATION: FAILED")
        print("   Critical requirements missing or broken.")
    else:
        print("🔥 TASK 11 VERIFICATION: ERROR")
        print("   Verification encountered errors.")
    
    print("=" * 80)


def save_verification_results(results: dict):
    """Save verification results to file"""
    output_dir = Path(__file__).parent.parent.parent / "verification_reports"
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"task_11_verification_{timestamp}.json"
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"📄 Verification results saved to: {output_file}")


async def main():
    """Main verification runner"""
    print("🔍 Starting Task 11 Buddy Chat Implementation Verification...")
    print()
    
    try:
        # Run verification
        results = await verify_task_11_chat()
        
        # Print report
        print_verification_report(results)
        
        # Save results
        save_verification_results(results)
        
        # Exit with appropriate code
        if results['overall_status'] in ['pass', 'partial']:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Verification interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Verification failed with exception: {str(e)}")
        print(f"\n🔥 VERIFICATION ERROR: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())