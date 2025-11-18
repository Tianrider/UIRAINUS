from browser_use import Agent, ChatGoogle, BrowserSession
from dotenv import load_dotenv
from steel import Steel
import asyncio
import os
import argparse
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
import re

load_dotenv()


def build_google_dork(university_name: str) -> str:
    return f'"{university_name}" site:huggingface.co'


def sanitize_university_input(s: str) -> str:
    if not s:
        return s
    s = s.strip()
    s = s.strip('"').strip("'")
    s = s.replace('\\', '')
    s = re.sub(r'\s--\S.*$', '', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def make_safe_filename(s: str) -> str:
    if not s:
        s = "university"
    s2 = re.sub(r'[<>:\\"/\\|?*\n\r\t]+', '_', s)
    s2 = s2.strip().strip('.')
    if not s2:
        s2 = "university"
    return s2.replace(' ', '_')


def search_huggingface_hub(university_name: str, limit: int = 100) -> Dict[str, List[Dict[str, Any]]]:
    try:
        from huggingface_hub import HfApi
    except Exception as e:
        raise ImportError("Please install the Hugging Face Hub library: pip install huggingface_hub") from e

    api = HfApi()
    q = (university_name or "").lower()
    results: Dict[str, List[Dict[str, Any]]] = {"models": [], "datasets": []}

    try:
        for m in api.list_models(limit=limit):
            mid = getattr(m, "modelId", None) or getattr(m, "model_id", None) or str(m)
            tags = []
            try:
                tags = list(m.tags or [])
            except Exception:
                pass
            author = getattr(m, "author", None)
            hay = " ".join(filter(None, [mid, ",".join(tags), str(author)])).lower()
            if q and q in hay:
                results["models"].append({
                    "id": mid,
                    "tags": tags,
                    "author": author,
                    "pipeline_tag": getattr(m, "pipeline_tag", None),
                    "cardData": getattr(m, "cardData", None),
                })
    except Exception as e:
        print(f"Error listing models: {e}")

    try:
        if hasattr(api, "list_datasets"):
            for d in api.list_datasets(limit=limit):
                did = getattr(d, "id", None) or getattr(d, "datasetId", None) or str(d)
                tags = []
                try:
                    tags = list(d.tags or [])
                except Exception:
                    pass
                author = getattr(d, "author", None)
                hay = " ".join(filter(None, [did, ",".join(tags), str(author)])).lower()
                if q and q in hay:
                    results["datasets"].append({
                        "id": did,
                        "tags": tags,
                        "author": author,
                        "cardData": getattr(d, "cardData", None),
                    })
        else:
            print("Hugging Face Hub client does not expose list_datasets on this version; skipping datasets.")
    except Exception as e:
        print(f"Error listing datasets: {e}")

    return results


def run_google_dork_serpapi(university_name: str, api_key: str = None, num: int = 10) -> List[str]:
    """Run a Google dork via SerpApi and return huggingface.co URLs found.

    Reads `api_key` if provided; otherwise expects `SERPAPI_API_KEY` in environment.
    Returns a deduplicated list of URLs.
    """
    if not api_key:
        api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        raise RuntimeError("SERPAPI_API_KEY not set in environment; provide api_key or set env var.")

    try:
        from serpapi import GoogleSearch
    except Exception as e:
        raise ImportError("Please install serpapi client: pip install google-search-results") from e

    dork = build_google_dork(university_name)
    params = {"q": dork, "engine": "google", "api_key": api_key, "num": num}
    search = GoogleSearch(params)
    data = search.get_dict()

    urls = []
    for res in data.get("organic_results", []) + data.get("top_results", []):
        link = res.get("link") or res.get("url")
        if link and "huggingface.co" in link:
            urls.append(link.split("?")[0])

    # dedupe while preserving order
    seen = set()
    out = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def extract_hf_id_from_url(url: str) -> Tuple[str, str]:
    """Try to extract (type, id) from a huggingface.co URL.

    Returns tuple: (kind, id) where kind is 'model' or 'dataset' or 'unknown'.
    id is the path-like id used by HfApi (e.g., 'username/model-name' or 'dataset_namespace/dataset-name').
    """
    from urllib.parse import urlparse
    p = urlparse(url)
    path = p.path.strip('/')
    parts = path.split('/')
    # handle /models/<id> and /datasets/<id>
    if len(parts) >= 2 and parts[0] in ("models", "datasets"):
        kind = "model" if parts[0] == "models" else "dataset"
        id = '/'.join(parts[1:])
        return kind, id

    # handle /<user>/<repo> (models)
    if len(parts) >= 2:
        # could be model page
        return "model", f"{parts[0]}/{parts[1]}"

    return "unknown", path


def fetch_metadata_for_hf_id(kind: str, hf_id: str) -> Dict[str, Any]:
    """Fetch metadata for a model or dataset id using HfApi. Returns dict or minimal info on error."""
    try:
        from huggingface_hub import HfApi
    except Exception:
        raise ImportError("Please install huggingface_hub: pip install huggingface_hub")

    api = HfApi()
    try:
        if kind == "model":
            info = api.model_info(hf_id)
            return {"id": getattr(info, 'modelId', None) or getattr(info, 'model_id', None) or hf_id,
                    "cardData": getattr(info, 'cardData', None),
                    "pipeline_tag": getattr(info, 'pipeline_tag', None)}
        elif kind == "dataset":
            # some versions have dataset_info
            if hasattr(api, 'dataset_info'):
                info = api.dataset_info(hf_id)
                return {"id": getattr(info, 'id', None) or hf_id, "cardData": getattr(info, 'cardData', None)}
            else:
                return {"id": hf_id}
    except Exception as e:
        return {"id": hf_id, "error": str(e)}



async def find_university_policy(university_name: str):
    client = Steel(steel_api_key=os.getenv("STEEL_API_KEY"))
    print("Creating Steel session...")
    session = client.sessions.create()
    print(f"Session created at {session.session_viewer_url}")
    cdp_url = f"wss://connect.steel.dev?apiKey={os.getenv('STEEL_API_KEY')}&sessionId={session.id}"
    llm = ChatGoogle(model="gemini-flash-latest")

    task = f"""
    Find all official policy documents from {university_name}:

    STEP 1 - SEARCH FOR OFFICIAL POLICIES:
    1. Search Google for \"{university_name} policy\" OR \"{university_name} official policy\"
    2. Look for official university domains (e.g., *.edu, *.ac.id, or other official institutional domains)
    3. IMPORTANT: Only consider documents from official university domains to ensure legitimacy

    STEP 2 - VERIFY LEGITIMACY:
    - Check that the URL is from the official university domain
    - Verify it's from an official university department or administrative unit
    - Look for policy documents, regulations, or official announcements
    - Acceptable document types: PDF, official web pages with policy content

    STEP 3 - COLLECT POLICY FILES:
    - Create a list of all policy document URLs found
    - For each document, note:
      * Document title
      * Full URL
      * Document type (PDF, webpage, etc.)
      * Publishing date if available
      * Department/unit that published it

    STEP 4 - FINAL OUTPUT:
    Provide a structured summary with:

     FOUND POLICIES:
    - Policy 1 Name: [title]
      URL: [full URL]
      Type: [PDF/webpage]
      Date: [if available]
      Department: [issuing unit]

     If NO official policies are found:
    - State clearly that no official AI policies were found
    - List what searches were attempted
    - Suggest the university may not have published AI-specific policies yet

    IMPORTANT INSTRUCTIONS:
    - Be thorough but verify URLs are from official university domains
    - If a PDF cannot be opened, note it and try alternative methods
    - Extract the EXACT text, do not paraphrase
    - Use extract action to get the quote from the document
    - Keep quotes in their original language

    !FINISH JOB AFTER 1 POLICY IS FOUND!

    """

    agent = Agent(
        task=task,
        llm=llm,
        use_vision=True,
    )

    try:
        print(f" Starting {university_name} AI Policy Search...\n")
        history = await agent.run()
        final_result = history.final_result()
        if final_result:
            print(final_result)
            return final_result
        else:
            print("No final result extracted. Check the agent's actions above.")
            return None
    except Exception as e:
        print(f"\n Error occurred: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        await agent.close()
        print("\n Browser closed")


async def main():
    university_name = "Harvard University"
    await find_university_policy(university_name)


def write_results_json(results: Dict[str, Any], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)


def write_results_csv(results: Dict[str, Any], out_path: Path) -> None:
    import csv
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Flatten results: write separate sections for models and datasets
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["type", "id", "author", "tags", "extra"]) 
        for m in results.get("models", []):
            writer.writerow(["model", m.get("id"), m.get("author"), ",".join(m.get("tags") or []), json.dumps({"pipeline_tag": m.get("pipeline_tag"), "cardData": m.get("cardData")})])
        for d in results.get("datasets", []):
            writer.writerow(["dataset", d.get("id"), d.get("author"), ",".join(d.get("tags") or []), json.dumps({"cardData": d.get("cardData")})])


def cli_entry():
    parser = argparse.ArgumentParser(description="Hugging Face + Policy finder CLI")
    parser.add_argument("--university", "-u", type=str, default=None, help="University name to search for")
    parser.add_argument("--hf-search", action="store_true", help="Search Hugging Face Hub for models/datasets related to the university")
    parser.add_argument("--use-serpapi", action="store_true", help="Use SerpApi to run Google dork and collect huggingface.co URLs")
    parser.add_argument("--serp-num", type=int, default=20, help="Number of SerpApi results to retrieve for the dork")
    parser.add_argument("--policy", action="store_true", help="Run the policy finder agent (original behavior)")
    parser.add_argument("--limit", type=int, default=100, help="Max results per type when searching HF Hub")
    parser.add_argument("--csv", action="store_true", help="Also write results as CSV in addition to JSON")

    args = parser.parse_args()

    if not args.hf_search and not args.policy:
        # default: run HF search only (more commonly used for this script)
        args.hf_search = True

    if args.hf_search:
        if not args.university:
            print("Please provide --university when using --hf-search")
        else:
            uni_clean = sanitize_university_input(args.university)
            dork = build_google_dork(uni_clean)
            print(f"Google dork to try: {dork}")
            # If user requested SerpApi dorking, run that first and map URLs to HF ids
            results: Dict[str, Any] = {"models": [], "datasets": [], "urls": []}
            if args.use_serpapi:
                try:
                    urls = run_google_dork_serpapi(uni_clean, num=args.serp_num)
                except Exception as e:
                    print(f"SerpApi error: {e}")
                    return
                print(f"Found {len(urls)} huggingface.co URLs via SerpApi")
                results["urls"] = urls
                # For each URL, try to extract HF id and fetch metadata
                for u in urls:
                    kind, hfid = extract_hf_id_from_url(u)
                    meta = fetch_metadata_for_hf_id(kind, hfid)
                    if kind == "model":
                        results["models"].append({"id": hfid, "meta": meta, "url": u})
                    elif kind == "dataset":
                        results["datasets"].append({"id": hfid, "meta": meta, "url": u})
                    else:
                        # unknown -> just include under urls
                        pass
            else:
                try:
                    results = search_huggingface_hub(uni_clean, limit=args.limit)
                except ImportError as e:
                    print(str(e))
                    return

            out_dir = Path("outputs")
            safe_name = make_safe_filename(uni_clean)
            json_path = out_dir / f"{safe_name}_huggingface_results.json"
            write_results_json(results, json_path)
            print(f"Results saved to {json_path.resolve()}")
            if args.csv:
                csv_path = out_dir / f"{safe_name}_huggingface_results.csv"
                write_results_csv(results, csv_path)
                print(f"CSV saved to {csv_path.resolve()}")

    if args.policy:
        if not args.university:
            print("Please provide --university when using --policy")
        else:
            asyncio.run(find_university_policy(args.university))


if __name__ == "__main__":
    cli_entry()
 
