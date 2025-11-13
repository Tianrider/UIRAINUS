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
    "AIzaSyAs3boAtdcE4Rj6r_c3rkG030KnY-_yqEo",
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

def classify_paper_with_gemini(title: str, abstract: str, paper_id: str):
    """
    Use Gemini to classify if paper discusses AI Ethics, Hallucination, or Bias
    Uses API key pool with rate limiting
    Retries indefinitely with exponential backoff on API errors
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
    
    attempt = 0
    max_attempt = 500  # Virtual unlimited with very high number
    
    while attempt < max_attempt:
        # Get a client from the pool
        client, api_key, rate_limiter = api_pool.get_client_and_key()
        
        # Wait for rate limit
        rate_limiter.wait()
        
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash-lite",  # Lightest/fastest model
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
            
            # Exponential backoff: 5s, 10s, 20s, 40s, 80s, 160s, 300s (capped at 5 min)
            wait_time = min(5 * (2 ** attempt), 300)
            
            attempt += 1
            print(f"  ⚠️  Error for {paper_id[-12:]}, retry {attempt} in {wait_time}s... ({str(e)[:40]})")
            time.sleep(wait_time)
    
    # This should never happen unless we hit the virtual limit
    print(f"  ❌ Exceeded maximum retry attempts: {paper_id[-12:]}")
    return {
        'paper_id': paper_id,
        'is_ethical': False,
        'categories': '',
        'confidence': 'error',
        'reasoning': f'Exceeded maximum retries',
        'success': False,
        'error': 'Max retries exceeded',
        'api_key_used': 'error'
    }

# ============================================================================
# LIVE CHECKPOINT WRITER
# ============================================================================

class LiveCheckpointWriter:
    """Thread-safe writer for live checkpointing of processed papers"""
    def __init__(self, filename, resume_mode=False):
        self.filename = filename
        self.lock = threading.Lock()
        self.fieldnames = None
        self.file_initialized = False
        self.resume_mode = resume_mode
        
        # If resuming, check if file exists and load its fieldnames
        if resume_mode and os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    self.fieldnames = reader.fieldnames
                    self.file_initialized = True
                print(f"   ✓ Appending to existing checkpoint file")
            except Exception as e:
                print(f"   ⚠️  Could not read existing checkpoint: {e}")
                self.resume_mode = False
    
    def write_row(self, row_dict):
        """Write a single row to the CSV file"""
        with self.lock:
            # Initialize file on first write (only for new files)
            if not self.file_initialized:
                self.fieldnames = list(row_dict.keys())
                with open(self.filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames)
                    writer.writeheader()
                self.file_initialized = True
            
            # Append row
            with open(self.filename, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames)
                writer.writerow(row_dict)



def process_papers_parallel(papers, checkpoint_writer=None):
    """
    Process papers in parallel with Gemini API
    Uses all available API keys with proper rate limiting
    Writes results live to checkpoint CSV if writer provided
    """
    results = []
    total = len(papers)
    
    # Dynamic worker count: 3 workers per API key (since we have 15 calls/min per key)
    max_workers = len(API_KEYS) * 3
    
    print(f"\n{'='*70}")
    print(f"Processing {total} papers")
    print(f"Workers: {max_workers} ({len(API_KEYS)} API key(s) × 3 workers each)")
    print(f"Estimated time: ~{(total * 4) / (len(API_KEYS) * 60):.1f} minutes")
    if checkpoint_writer:
        print(f"📊 Live checkpoint: {checkpoint_writer.filename}")
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
                
                # Write to checkpoint immediately
                if checkpoint_writer:
                    checkpoint_writer.write_row(result)
                
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
                error_result = {
                    **paper,
                    'is_ethical': False,
                    'categories': '',
                    'confidence': 'error',
                    'reasoning': f'Exception: {str(e)}',
                    'success': False,
                    'error': str(e)
                }
                results.append(error_result)
                
                # Write error result to checkpoint
                if checkpoint_writer:
                    checkpoint_writer.write_row(error_result)
    
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
    csv_files = glob.glob("./ui_ai_publications_*.csv")
    if not csv_files:
        raise FileNotFoundError("No ui_ai_publications_*.csv file found in current directory")
    
    # Get the most recent file
    latest_file = max(csv_files, key=os.path.getctime)
    return latest_file

def find_latest_checkpoint():
    """
    Find the most recent checkpoint CSV file
    """
    checkpoint_files = glob.glob("./ui_ai_papers_checkpoint_*.csv")
    if not checkpoint_files:
        return None
    
    # Get the most recent checkpoint file
    latest_checkpoint = max(checkpoint_files, key=os.path.getctime)
    return latest_checkpoint

def get_processed_paper_ids(checkpoint_file):
    """
    Extract paper IDs that have already been processed from checkpoint file
    """
    processed_ids = set()
    try:
        with open(checkpoint_file, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if 'openalex_id' in row:
                    processed_ids.add(row['openalex_id'])
    except Exception as e:
        print(f"⚠️  Error reading checkpoint file: {e}")
        return set()
    
    return processed_ids

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
    
    # Check for existing checkpoint
    existing_checkpoint = find_latest_checkpoint()
    processed_ids = set()
    resume_mode = False
    checkpoint_file = None
    
    if existing_checkpoint:
        print(f"\n🔍 Found existing checkpoint: {existing_checkpoint}")
        processed_ids = get_processed_paper_ids(existing_checkpoint)
        
        if processed_ids:
            remaining_papers = [p for p in papers if p.get('openalex_id') not in processed_ids]
            print(f"✓ Already processed: {len(processed_ids)} papers")
            print(f"⏳ Remaining to process: {len(remaining_papers)} papers")
            
            if len(remaining_papers) > 0:
                # Ask user if they want to resume
                print(f"\n📋 Resume from checkpoint?")
                print(f"   YES: Continue from where you left off ({len(remaining_papers)} papers)")
                print(f"   NO:  Start fresh with all {len(papers)} papers")
                
                user_input = input("\nResume? (Y/n): ").strip().lower()
                
                if user_input == '' or user_input == 'y' or user_input == 'yes':
                    resume_mode = True
                    papers = remaining_papers
                    checkpoint_file = existing_checkpoint
                    print(f"\n✅ Resuming from checkpoint!")
                    print(f"   Using existing checkpoint: {checkpoint_file}\n")
                else:
                    print(f"\n🔄 Starting fresh...")
            else:
                print(f"\n✅ All papers already processed in checkpoint!")
                print(f"   Loading results from: {existing_checkpoint}\n")
                # Load and display results from checkpoint
                classified_papers = read_csv(existing_checkpoint)
                ethical_papers = [p for p in classified_papers if p.get('is_ethical', '').lower() == 'true']
                
                # Print summary and exit
                print(f"\n{'='*70}")
                print("SUMMARY (from checkpoint)")
                print(f"{'='*70}")
                print(f"Total papers processed: {len(classified_papers)}")
                print(f"Ethical papers found: {len(ethical_papers)} ({len(ethical_papers)/len(classified_papers)*100:.1f}%)")
                print(f"\n📊 Checkpoint file (all results): {existing_checkpoint}")
                print(f"{'='*70}\n")
                return
    
    # Create checkpoint file (new or resume existing)
    if not resume_mode:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        checkpoint_file = f"ui_ai_papers_checkpoint_{timestamp}.csv"
        print(f"📊 Checkpoint file: {checkpoint_file}")
        print(f"   (Results will be saved live as they complete)\n")
    
    checkpoint_writer = LiveCheckpointWriter(checkpoint_file, resume_mode=resume_mode)
    
    # Process papers in parallel with live checkpointing
    start_time = time.time()
    classified_papers = process_papers_parallel(papers, checkpoint_writer)
    elapsed_time = time.time() - start_time
    
    # Print API key statistics
    api_pool.print_stats()
    
    # Load all results from checkpoint for complete summary
    print(f"\n📊 Loading complete results from checkpoint...")
    all_classified_papers = read_csv(checkpoint_file)
    
    # Convert string 'True'/'False' to boolean for filtering
    ethical_papers = [p for p in all_classified_papers if str(p.get('is_ethical', '')).lower() == 'true']
    total_processed = len(all_classified_papers)
    
    # Save only ethical papers (final summary file)
    if ethical_papers:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ethical_only_file = f"ui_ai_papers_ethical_only_{timestamp}.csv"
        save_filtered_csv(ethical_papers, ethical_only_file)
    else:
        print("\n⚠️  No ethical papers found!")
    
    # Print summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    if resume_mode:
        print(f"Total papers processed (all): {total_processed}")
        print(f"Papers processed this session: {len(classified_papers)}")
    else:
        print(f"Total papers processed: {total_processed}")
    print(f"Ethical papers found: {len(ethical_papers)} ({len(ethical_papers)/total_processed*100:.1f}%)")
    print(f"Processing time: {elapsed_time:.1f} seconds")
    if len(classified_papers) > 0:
        print(f"Average time per paper: {elapsed_time/len(classified_papers):.2f} seconds")
    print(f"\n📊 Checkpoint file (all results): {checkpoint_file}")
    if ethical_papers:
        print(f"✓ Ethical papers file: {ethical_only_file}")
    
    # Category breakdown
    if ethical_papers:
        print(f"\n📊 Category breakdown:")
        category_counts = {}
        for paper in ethical_papers:
            categories = paper.get('categories', '').split(', ')
            for cat in categories:
                if cat and cat.strip():
                    category_counts[cat.strip()] = category_counts.get(cat.strip(), 0) + 1
        
        for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"   {category}: {count} papers")
        
        # Show top ethical papers
        print(f"\n🌟 Top 5 ethical papers by citations:")
        ethical_sorted = sorted(ethical_papers, 
                               key=lambda x: int(x.get('cited_by_count', 0) if x.get('cited_by_count', 0) else 0), 
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
