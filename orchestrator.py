"""
Main Orchestrator for University AI Research Analysis
This script orchestrates all 4 processing steps:
1. Publication Analysis (OpenAlex)
2. Model & Dataset Analysis (HuggingFace)
3. Policy Analysis
4. Organigram Analysis

All results are stored in outputs/[university-name]/ folder
"""

import asyncio
import sys
import importlib.util
from pathlib import Path
from datetime import datetime
import json


def make_safe_foldername(university_name: str) -> str:
    """Convert university name to a safe folder name."""
    import re
    # Replace special characters with underscores
    safe_name = re.sub(r'[<>:"/\\|?*\n\r\t]+', '_', university_name)
    # Replace spaces with underscores
    safe_name = safe_name.replace(' ', '_')
    # Remove leading/trailing underscores and dots
    safe_name = safe_name.strip('._')
    # Convert to lowercase for consistency
    safe_name = safe_name.lower()
    return safe_name or "university"


def create_output_directory(university_name: str) -> Path:
    """Create output directory for the university."""
    base_dir = Path(__file__).parent / "outputs"
    safe_name = make_safe_foldername(university_name)
    output_dir = base_dir / safe_name
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def load_module(module_path: Path, module_name: str):
    """Dynamically load a Python module."""
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


async def run_publication_analysis(university_name: str, output_dir: Path):
    """Step 1: Run OpenAlex publication analysis."""
    print("\n" + "="*80)
    print("STEP 1: PUBLICATION ANALYSIS (OpenAlex)")
    print("="*80)
    
    try:
        # Import openAlex module
        module_path = Path(__file__).parent / "1_Publication" / "openAlex.py"
        openalex = load_module(module_path, "openalex_module")
        
        # Search for institution
        institution_id = openalex.search_institution(university_name)
        
        if not institution_id:
            print("⚠️ Could not find institution in OpenAlex")
            return False
        
        # Fetch papers
        papers = openalex.fetch_all_ui_ai_papers(institution_id)
        
        if not papers:
            print("⚠️ No publications found")
            return False
        
        # Save to CSV in university folder
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = output_dir / f"publications_{timestamp}.csv"
        openalex.save_to_csv(papers, str(csv_filename))
        
        # Print summary
        openalex.print_summary(papers)
        
        print(f"\n✅ Publications saved to: {csv_filename}")
        return True
        
    except Exception as e:
        print(f"\n❌ Error in publication analysis: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_model_dataset_analysis(university_name: str, output_dir: Path):
    """Step 2: Run HuggingFace model and dataset analysis."""
    print("\n" + "="*80)
    print("STEP 2: MODEL & DATASET ANALYSIS (HuggingFace)")
    print("="*80)
    
    try:
        # Import huggingface module
        module_path = Path(__file__).parent / "2_Model_Dataset" / "HuggingFace" / "huggingface.py"
        hf = load_module(module_path, "hf_module")
        
        # Clean university name
        uni_clean = hf.sanitize_university_input(university_name)
        print(f"Searching HuggingFace Hub for: {uni_clean}")
        
        # Search HuggingFace
        results = hf.search_huggingface_hub(uni_clean, limit=100)
        
        # Save JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_filename = output_dir / f"huggingface_{timestamp}.json"
        hf.write_results_json(results, json_filename)
        
        # Save CSV
        csv_filename = output_dir / f"huggingface_{timestamp}.csv"
        hf.write_results_csv(results, csv_filename)
        
        total_items = len(results.get('models', [])) + len(results.get('datasets', []))
        print(f"\n✅ Found {total_items} items ({len(results.get('models', []))} models, {len(results.get('datasets', []))} datasets)")
        print(f"✅ Results saved to:")
        print(f"   - {json_filename}")
        print(f"   - {csv_filename}")
        
        return True
        
    except ImportError as e:
        print(f"\n⚠️ HuggingFace Hub not installed: {e}")
        print("   Install with: pip install huggingface_hub")
        return False
    except Exception as e:
        print(f"\n❌ Error in model/dataset analysis: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_policy_analysis(university_name: str, output_dir: Path):
    """Step 3: Run AI Policy analysis."""
    print("\n" + "="*80)
    print("STEP 3: AI POLICY ANALYSIS")
    print("="*80)
    
    try:
        # Import policy module
        module_path = Path(__file__).parent / "3_Policy" / "computer-use.py"
        policy = load_module(module_path, "policy_module")
        
        # Run policy search
        result = await policy.find_university_policy(university_name)
        
        if result:
            # Parse result
            parsed_data = []
            if isinstance(result, policy.PolicyResults):
                parsed_data = [item.model_dump() for item in result.results]
            
            if parsed_data:
                # Save to CSV
                import csv
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                csv_filename = output_dir / f"policies_{timestamp}.csv"
                
                fieldnames = ["university", "policy_title", "url", "document_type", "publishing_date", "department"]
                
                with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(parsed_data)
                
                print(f"\n✅ Found {len(parsed_data)} policy document(s)")
                print(f"✅ Policies saved to: {csv_filename}")
                return True
            else:
                print("\n⚠️ No policies found")
                return False
        else:
            print("\n⚠️ No policy data returned")
            return False
            
    except Exception as e:
        print(f"\n❌ Error in policy analysis: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_organigram_analysis(university_name: str, output_dir: Path):
    """Step 4: Run Organigram and AI Division analysis."""
    print("\n" + "="*80)
    print("STEP 4: ORGANIGRAM & AI DIVISION ANALYSIS")
    print("="*80)
    
    try:
        # Import organigram module
        module_path = Path(__file__).parent / "4_Organigram" / "computer-use.py"
        org = load_module(module_path, "organigram_module")
        
        # Run organigram search
        result = await org.find_university_organigram(university_name)
        
        if result:
            # Parse result
            parsed_data = []
            if isinstance(result, org.OrganigramResults):
                parsed_data = [item.model_dump() for item in result.results]
            
            if parsed_data:
                # Save to CSV
                import csv
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                csv_filename = output_dir / f"organigram_{timestamp}.csv"
                
                fieldnames = ["university", "division_name", "chair_name", "chair_title", "url"]
                
                with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(parsed_data)
                
                print(f"\n✅ Found {len(parsed_data)} AI division(s)")
                print(f"✅ Organigram data saved to: {csv_filename}")
                return True
            else:
                print("\n⚠️ No AI divisions found")
                return False
        else:
            print("\n⚠️ No organigram data returned")
            return False
            
    except Exception as e:
        print(f"\n❌ Error in organigram analysis: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main orchestrator function."""
    print("\n" + "█"*80)
    print(" "*20 + "UNIVERSITY AI RESEARCH ANALYSIS ORCHESTRATOR")
    print("█"*80)
    print("\nThis tool will run all 4 analysis steps:")
    print("  1. Publication Analysis (OpenAlex)")
    print("  2. Model & Dataset Analysis (HuggingFace)")
    print("  3. AI Policy Analysis")
    print("  4. Organigram & AI Division Analysis")
    print("\n" + "="*80 + "\n")
    
    # Get university name from user
    if len(sys.argv) > 1:
        university_name = " ".join(sys.argv[1:])
    else:
        university_name = input("📝 Enter university name: ").strip()
    
    if not university_name:
        print("❌ No university name provided!")
        sys.exit(1)
    
    print(f"\n🎯 Processing: {university_name}")
    
    # Create output directory
    output_dir = create_output_directory(university_name)
    print(f"📁 Output directory: {output_dir}")
    
    # Track results
    results = {
        "university": university_name,
        "timestamp": datetime.now().isoformat(),
        "output_directory": str(output_dir),
        "steps": {}
    }
    
    start_time = datetime.now()
    
    # Run all steps
    results["steps"]["1_publications"] = await run_publication_analysis(university_name, output_dir)
    results["steps"]["2_models_datasets"] = await run_model_dataset_analysis(university_name, output_dir)
    results["steps"]["3_policies"] = await run_policy_analysis(university_name, output_dir)
    results["steps"]["4_organigram"] = await run_organigram_analysis(university_name, output_dir)
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # Save summary
    summary_file = output_dir / "analysis_summary.json"
    results["duration_seconds"] = duration
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Print final summary
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)
    print(f"\n📊 Summary:")
    print(f"   University: {university_name}")
    print(f"   Duration: {duration:.1f} seconds")
    print(f"   Output Directory: {output_dir}")
    print(f"\n📈 Results:")
    for step, success in results["steps"].items():
        status = "✅ Success" if success else "⚠️ Failed/No data"
        print(f"   {step}: {status}")
    
    print(f"\n💾 Summary saved to: {summary_file}")
    print("\n" + "="*80)
    print("🎉 All processing complete!")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
