import asyncio
import importlib.util
import sys
import json
import csv
from pathlib import Path
from datetime import datetime

# Import module with hyphen in name
module_path = Path(__file__).parent / "computer-use.py"
spec = importlib.util.spec_from_file_location("computer_use", module_path)
computer_use = importlib.util.module_from_spec(spec)
sys.modules["computer_use"] = computer_use
spec.loader.exec_module(computer_use)

find_university_organigram = computer_use.find_university_organigram
OrganigramResults = computer_use.OrganigramResults

def parse_organigram_result(result):
    """
    Parse organigram result from agent output.
    Handles both Pydantic models and JSON strings.
    
    Args:
        result: Either a Pydantic OrganigramResults model or a JSON string
        
    Returns:
        list: List of dictionaries with organigram data
    """
    if not result:
        return []
    
    # Check if result is a Pydantic model
    if isinstance(result, OrganigramResults):
        # Convert Pydantic model to list of dicts
        return [item.model_dump() for item in result.results]
    
    # Handle string/JSON results (backward compatibility)
    if isinstance(result, str):
        try:
            # Try direct parsing first
            return json.loads(result)
        except json.JSONDecodeError:
            # Try to find JSON array in the text
            import re
            json_match = re.search(r'\[.*\]', result, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except json.JSONDecodeError:
                    pass
            
            print(f"⚠️ Could not parse JSON from result. Returning empty array.")
            return []
    
    # If it's already a list, return it
    if isinstance(result, list):
        return result
    
    print(f"⚠️ Unknown result type: {type(result)}. Returning empty array.")
    return []

def create_csv_report(all_results, output_dir=None):
    """
    Create CSV report from collected organigram data.
    
    Args:
        all_results (list): List of dictionaries containing organigram data
        output_dir (Path): Directory to save the CSV. If None, uses parent directory
    """
    if not all_results:
        print("\n⚠️ No data to create CSV report.")
        return None
    
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "outputs"
    
    if isinstance(output_dir, str):
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = output_dir / f"university_ai_divisions_{timestamp}.csv"
    
    # Define CSV columns
    fieldnames = ["university", "division_name", "chair_name", "chair_title", "url"]
    
    try:
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_results)
        
        print(f"\n✅ CSV report created: {csv_filename}")
        print(f"   Total entries: {len(all_results)}")
        return csv_filename
    except Exception as e:
        print(f"\n❌ Error creating CSV report: {e}")
        return None

async def main():    
    # List of universities to search
    universities = [
        "University of Indonesia",
        # Add more universities here as needed
    ]
    
    all_results = []
    
    # Search organigrams for each university
    for university in universities:
        print(f"\n{'='*80}")
        print(f"Processing: {university}")
        print(f"{'='*80}\n")
        
        result = await find_university_organigram(university)
        
        if result:
            # Parse result (handles both Pydantic models and JSON)
            parsed_data = parse_organigram_result(result)
            
            if parsed_data:
                print(f"\n✓ Successfully found AI division(s) for {university}")
                print(f"   Found {len(parsed_data)} division(s)")
                all_results.extend(parsed_data)
                
                # Display found data
                for item in parsed_data:
                    print(f"\n   Division: {item.get('division_name', 'N/A')}")
                    print(f"   Chair: {item.get('chair_name', 'N/A')}")
                    print(f"   Title: {item.get('chair_title', 'N/A')}")
                    print(f"   URL: {item.get('url', 'N/A')}")
            else:
                print(f"\n⚠️ No AI divisions found for {university}")
        else:
            print(f"\n⚠️ No organigram data found for {university}")
        
        print(f"\n{'='*80}\n")
    
    # Create CSV report from all collected data
    print("\n" + "="*80)
    print("Creating final CSV report...")
    print("="*80)
    
    csv_file = create_csv_report(all_results)
    
    if csv_file:
        print(f"\n🎉 Process completed successfully!")
        print(f"   Universities processed: {len(universities)}")
        print(f"   AI divisions found: {len(all_results)}")
        print(f"   Report saved to: {csv_file}")
    else:
        print(f"\n⚠️ No CSV report generated (no data collected)")


if __name__ == "__main__":
    asyncio.run(main())