import argparse
import asyncio
import importlib.util
import sys
import json
from pathlib import Path

# Import module with hyphen in name (policy finder)
module_path = Path(__file__).parent / "computer-use.py"
spec = importlib.util.spec_from_file_location("computer_use", module_path)
computer_use = importlib.util.module_from_spec(spec)
sys.modules["computer_use"] = computer_use
spec.loader.exec_module(computer_use)

find_university_policy = computer_use.find_university_policy

# Import HF search function directly from huggingface module
try:
    from huggingface import search_huggingface_hub, sanitize_university_input, make_safe_filename
except Exception:
    # try relative import if running as package
    from .huggingface import search_huggingface_hub, sanitize_university_input, make_safe_filename


async def run_policy_for_universities(universities):
    for university in universities:
        result = await find_university_policy(university)
        if result:
            print(f"\n✓ Successfully found policies for {university}")
        else:
            print(f"\n⚠️ No policies found for {university}")
        print(f"\n{'='*80}\n")


def run_hf_search_for_universities(universities, limit=100, write_json=True):
    for university in universities:
        uni_clean = sanitize_university_input(university)
        print(f"Searching HF Hub for: {uni_clean}")
        try:
            results = search_huggingface_hub(uni_clean, limit=limit)
        except ImportError as e:
            print(str(e))
            return

        if write_json:
            out_dir = Path(__file__).parent.parent / "outputs"
            safe_name = make_safe_filename(uni_clean)
            out_path = out_dir / f"{safe_name}_huggingface_results.json"
            out_dir.mkdir(parents=True, exist_ok=True)
            with out_path.open("w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"Saved results to {out_path.resolve()}")


def parse_universities_arg(s: str):
    """Parse a comma-separated string of university names into a list."""
    if not s:
        return []
    # split on comma and strip whitespace
    return [p.strip() for p in s.split(',') if p.strip()]


async def main():
    parser = argparse.ArgumentParser(description="Run university policy finder and/or Hugging Face searches for a list of universities")
    parser.add_argument("--universities", "-U", type=str, default=None,
                        help="Comma-separated list of universities to process (overrides built-in list)")
    parser.add_argument("--file", "-f", type=str, default=None, help="Path to a text file with one university per line")
    parser.add_argument("--hf-search", action="store_true", help="Run Hugging Face Hub search for each university")
    parser.add_argument("--policy", action="store_true", help="Run policy finder agent for each university")
    parser.add_argument("--limit", type=int, default=100, help="Limit for HF Hub results per run")

    args = parser.parse_args()

    # default list (can be overridden)
    universities = [
        "University of Indonesia",
    ]

    if args.universities:
        universities = parse_universities_arg(args.universities)
    elif args.file:
        p = Path(args.file)
        if p.exists():
            universities = [line.strip() for line in p.read_text(encoding='utf-8').splitlines() if line.strip()]
        else:
            print(f"Universities file not found: {p}. Using default list.")

    if not args.hf_search and not args.policy:
        # if no flags provided, run both
        args.hf_search = True
        args.policy = True

    # Run HF searches synchronously (subprocess) if requested
    if args.hf_search:
        run_hf_search_for_universities(universities, limit=args.limit)

    # Run policy finder (async) if requested
    if args.policy:
        await run_policy_for_universities(universities)


if __name__ == "__main__":
    asyncio.run(main())