import csv
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from google import genai
from pydantic import BaseModel
import glob
import os
import threading
from collections import deque

# ============================================================================
# API KEY CONFIGURATION - ADD YOUR API KEYS HERE
# ============================================================================
API_KEYS = [
    "AIzaSyCG2Pf3dZb43kUhHV5OH91MCQgFk-T07MI",
    "AIzaSyDZ31MVEq6ZDbEdKA4EbR8L5F6AClauikY",
    "AIzaSyAk8ARN1Y_8SYIQd7V5Z738RPMV33SFM-M",
    "AIzaSyDOW6FjezvptFagOCb3bsOVMiJe5YO7Fr4",
    "AIzaSyCKa4j-7REu6gf6ODKHT311gBMdmmc4WFQ",
    "AIzaSyCytjGCxJnT5QmXfGYCwTq__UlcR4JYdtI",
    # Add more API keys here:
    # "AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    # "AIzaSyYYYYYYYYYYYYYYYYYYYYYYYYYYYYY",
    # "AIzaSyZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ",
]

# ============================================================================
# RATE LIMITER PER API KEY (15 calls per minute = 1 call per 4 seconds)
# ============================================================================
class RateLimiter:
    """Rate limiter that enforces 15 calls per minute (1 call every 4 seconds)"""
    def __init__(self, calls_per_minute=10):
        self.calls_per_minute = calls_per_minute
        self.min_interval = 60.0 / calls_per_minute  # 4 seconds for 15 calls/minute
        self.last_call = 0
        self.lock = threading.Lock()
    
    def wait(self):
        with self.lock:
            elapsed = time.time() - self.last_call
            if elapsed < self.min_interval:
                wait_time = self.min_interval - elapsed
                time.sleep(wait_time)
            self.last_call = time.time()

# ============================================================================
# API KEY POOL MANAGER
# ============================================================================
class APIKeyPool:
    """Manages multiple API keys with round-robin distribution and rate limiting"""
    def __init__(self, api_keys):
        self.api_keys = api_keys
        self.clients = {key: genai.Client(api_key=key) for key in api_keys}
        self.rate_limiters = {key: RateLimiter(calls_per_minute=15) for key in api_keys}
        self.key_queue = deque(api_keys)
        self.lock = threading.Lock()
        self.stats = {key: {'calls': 0, 'errors': 0} for key in api_keys}
        
        print(f"\n🔑 Initialized {len(api_keys)} API key(s)")
        print(f"⚡ Rate limit: 15 calls/minute per key")
        print(f"🚀 Total capacity: {len(api_keys) * 15} calls/minute\n")
    
    def get_client_and_key(self):
        """Get next available API key and its client in round-robin fashion"""
        with self.lock:
            # Rotate to next key
            api_key = self.key_queue[0]
            self.key_queue.rotate(-1)  # Move first to last
            
            return self.clients[api_key], api_key, self.rate_limiters[api_key]
    
    def record_call(self, api_key, success=True):
        """Record API call statistics"""
        with self.lock:
            self.stats[api_key]['calls'] += 1
            if not success:
                self.stats[api_key]['errors'] += 1
    
    def print_stats(self):
        """Print usage statistics for all API keys"""
        print(f"\n{'='*70}")
        print("API KEY USAGE STATISTICS")
        print(f"{'='*70}")
        for i, (key, stats) in enumerate(self.stats.items(), 1):
            key_short = key[:20] + "..." + key[-4:]
            success_rate = ((stats['calls'] - stats['errors']) / stats['calls'] * 100) if stats['calls'] > 0 else 0
            print(f"Key {i}: {key_short}")
            print(f"  Calls: {stats['calls']}, Errors: {stats['errors']}, Success: {success_rate:.1f}%")
        print(f"{'='*70}\n")

# Initialize API key pool
api_pool = APIKeyPool(API_KEYS)

# ============================================================================
# STRUCTURED OUTPUT SCHEMA
# ============================================================================

class PaperClassification(BaseModel):
    """Classification result for a paper"""
    is_ethical: bool
    categories: list[str]  # e.g., ["AI Ethics", "AI Bias"]
    confidence: str  # "high", "medium", "low"
    reasoning: str

# ============================================================================
# GEMINI API CALLER WITH RETRY
# ============================================================================

def classify_paper_with_gemini(title: str, abstract: str, paper_id: str, retry_count=3):
    """
    Use Gemini to classify if paper discusses AI Ethics, Hallucination, or Bias
    Uses API key pool with rate limiting
    """
    # Handle missing abstract
    if not abstract or abstract == "No":
        abstract = "No abstract available"
    
    prompt = f"""Analyze this research paper and determine if it discusses any of these topics:
- AI Ethics (fairness, responsibility, moral implications, societal impact)
- AI Hallucination (false information generation, factual errors, confabulation)
- AI Bias (discrimination, unfairness in AI systems, bias in training data or outputs)

Title: {title}

Abstract: {abstract}

Return is_ethical=true ONLY if the paper substantially discusses at least one of these topics.
Return is_ethical=false if it's just general AI research, technical methods, or applications without ethical concerns.

List all applicable categories found. Provide your confidence level and brief reasoning.
"""
    
    for attempt in range(retry_count):
        # Get a client from the pool
        client, api_key, rate_limiter = api_pool.get_client_and_key()
        
        # Wait for rate limit
        rate_limiter.wait()
        
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash-lite",  # Lightest/fastest model
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": PaperClassification,
                }
            )
            
            result = PaperClassification.model_validate_json(response.text)
            
            # Record successful call
            api_pool.record_call(api_key, success=True)
            
            return {
                'paper_id': paper_id,
                'is_ethical': result.is_ethical,
                'categories': ', '.join(result.categories) if result.categories else '',
                'confidence': result.confidence,
                'reasoning': result.reasoning,
                'success': True,
                'error': None,
                'api_key_used': api_key[-4:]  # Last 4 chars for identification
            }
            
        except Exception as e:
            # Record failed call
            api_pool.record_call(api_key, success=False)
            
            if attempt < retry_count - 1:
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                print(f"  ⚠️  Error for {paper_id[-12:]}, retry {attempt+1}/{retry_count} in {wait_time}s... ({str(e)[:40]})")
                time.sleep(wait_time)
            else:
                print(f"  ❌ Failed after {retry_count} attempts: {paper_id[-12:]}")
                return {
                    'paper_id': paper_id,
                    'is_ethical': False,
                    'categories': '',
                    'confidence': 'error',
                    'reasoning': f'Error: {str(e)[:100]}',
                    'success': False,
                    'error': str(e),
                    'api_key_used': 'error'
                }

# ============================================================================
# PARALLEL PROCESSING
# ============================================================================

def process_papers_parallel(papers):
    """
    Process papers in parallel with Gemini API
    Uses all available API keys with proper rate limiting
    """
    results = []
    total = len(papers)
    
    # Dynamic worker count: 3 workers per API key (since we have 15 calls/min per key)
    max_workers = len(API_KEYS) * 3
    
    print(f"\n{'='*70}")
    print(f"Processing {total} papers")
    print(f"Workers: {max_workers} ({len(API_KEYS)} API key(s) × 3 workers each)")
    print(f"Estimated time: ~{(total * 4) / (len(API_KEYS) * 60):.1f} minutes")
    print(f"{'='*70}\n")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_paper = {}
        for i, paper in enumerate(papers, 1):
            future = executor.submit(
                classify_paper_with_gemini,
                paper['title'],
                paper.get('abstract_inverted_index', ''),
                paper['openalex_id']
            )
            future_to_paper[future] = (i, paper)
        
        # Process completed tasks
        completed = 0
        ethical_count = 0
        
        for future in as_completed(future_to_paper):
            completed += 1
            paper_num, paper = future_to_paper[future]
            
            try:
                classification = future.result()
                
                # Merge classification with original paper data
                result = {**paper, **classification}
                results.append(result)
                
                if classification['is_ethical']:
                    ethical_count += 1
                    status = "✓ ETHICAL"
                    categories = f" [{classification['categories']}]"
                else:
                    status = "○ Not ethical"
                    categories = ""
                
                # Progress indicator
                print(f"[{completed}/{total}] {status}{categories} - {paper['title'][:60]}...")
                
            except Exception as e:
                print(f"[{completed}/{total}] ❌ Exception: {str(e)[:50]}")
                results.append({
                    **paper,
                    'is_ethical': False,
                    'categories': '',
                    'confidence': 'error',
                    'reasoning': f'Exception: {str(e)}',
                    'success': False,
                    'error': str(e)
                })
    
    print(f"\n{'='*70}")
    print(f"✅ Processing complete!")
    print(f"   Total processed: {completed}")
    print(f"   Ethical papers: {ethical_count} ({ethical_count/total*100:.1f}%)")
    print(f"{'='*70}\n")
    
    return results

# ============================================================================
# CSV OPERATIONS
# ============================================================================

def read_csv(filename):
    """
    Read papers from CSV file
    """
    papers = []
    with open(filename, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        papers = list(reader)
    
    print(f"📖 Loaded {len(papers)} papers from {filename}")
    return papers

def save_filtered_csv(papers, filename):
    """
    Save filtered papers to CSV
    """
    if not papers:
        print("⚠️  No papers to save!")
        return
    
    # Get all fieldnames (original + classification fields)
    # Ensure api_key_used is included if present
    fieldnames = list(papers[0].keys())
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(papers)
    
    print(f"💾 Saved {len(papers)} papers to {filename}")

def find_latest_csv():
    """
    Find the most recent ui_ai_publications CSV file
    """
    csv_files = glob.glob("ui_ai_publications_*.csv")
    if not csv_files:
        raise FileNotFoundError("No ui_ai_publications_*.csv file found in current directory")
    
    # Get the most recent file
    latest_file = max(csv_files, key=os.path.getctime)
    return latest_file

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    print("\n" + "█"*70)
    print("  AI ETHICS PAPER FILTER - Using Gemini API")
    print("█"*70)
    
    # Find and read the CSV file
    try:
        input_csv = find_latest_csv()
        print(f"\n📂 Found input file: {input_csv}")
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        return
    
    papers = read_csv(input_csv)
    
    if not papers:
        print("❌ No papers found in CSV!")
        return
    
    # Process papers in parallel
    start_time = time.time()
    classified_papers = process_papers_parallel(papers)
    elapsed_time = time.time() - start_time
    
    # Print API key statistics
    api_pool.print_stats()
    
    # Filter only ethical papers
    ethical_papers = [p for p in classified_papers if p.get('is_ethical', False)]
    
    # Save all classified papers (with classification fields)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    all_results_file = f"ui_ai_papers_classified_{timestamp}.csv"
    save_filtered_csv(classified_papers, all_results_file)
    
    # Save only ethical papers
    if ethical_papers:
        ethical_only_file = f"ui_ai_papers_ethical_only_{timestamp}.csv"
        save_filtered_csv(ethical_papers, ethical_only_file)
    else:
        print("\n⚠️  No ethical papers found!")
    
    # Print summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"Total papers processed: {len(classified_papers)}")
    print(f"Ethical papers found: {len(ethical_papers)} ({len(ethical_papers)/len(papers)*100:.1f}%)")
    print(f"Processing time: {elapsed_time:.1f} seconds")
    print(f"Average time per paper: {elapsed_time/len(papers):.2f} seconds")
    
    # Category breakdown
    if ethical_papers:
        print(f"\n📊 Category breakdown:")
        category_counts = {}
        for paper in ethical_papers:
            categories = paper.get('categories', '').split(', ')
            for cat in categories:
                if cat:
                    category_counts[cat] = category_counts.get(cat, 0) + 1
        
        for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"   {category}: {count} papers")
        
        # Show top ethical papers
        print(f"\n🌟 Top 5 ethical papers by citations:")
        ethical_sorted = sorted(ethical_papers, 
                               key=lambda x: int(x.get('cited_by_count', 0)), 
                               reverse=True)
        for i, paper in enumerate(ethical_sorted[:5], 1):
            print(f"\n   {i}. {paper.get('title', 'N/A')}")
            print(f"      Categories: {paper.get('categories', 'N/A')}")
            print(f"      Confidence: {paper.get('confidence', 'N/A')}")
            print(f"      Citations: {paper.get('cited_by_count', 0)}")
            print(f"      Year: {paper.get('publication_year', 'N/A')}")
    
    print(f"\n{'='*70}")
    print("✅ All done!")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()
