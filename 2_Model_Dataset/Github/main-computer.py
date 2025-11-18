import asyncio
import importlib.util
import sys
from pathlib import Path

# Import module with hyphen in name
module_path = Path(__file__).parent / "computer-use.py"
spec = importlib.util.spec_from_file_location("computer_use", module_path)
computer_use = importlib.util.module_from_spec(spec)
sys.modules["computer_use"] = computer_use
spec.loader.exec_module(computer_use)

find_university_policy = computer_use.find_university_policy

async def main():    
    # List of universities to search
    universities = [
        "Harvard University",
        # Add more universities here as needed
    ]
    
    # Search models and dataset for each university
    for university in universities:
        
        result = await find_university_policy(university)
        
        if result:
            print(f"\n✓ Successfully found models and datasets for {university}")
        else:
            print(f"\n⚠️ No models and datasets found for {university}")
        
        print(f"\n{'='*80}\n")


if __name__ == "__main__":
    asyncio.run(main())