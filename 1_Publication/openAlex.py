import requests
import csv
import time
from datetime import datetime

WORKS_URL = "https://api.openalex.org/works"
INSTITUTIONS_URL = "https://api.openalex.org/institutions"
EMAIL = "hadiwijayachristian7@gmail.com"  # Add your email for polite pool (10x faster)

def search_institution(institution_name):
    """
    Search for institution by name and return matching results
    """
    print(f"\n🔍 Searching for institution: '{institution_name}'...")
    
    params = {
        "search": institution_name,
        "per-page": 10,
        "mailto": EMAIL
    }
    
    try:
        response = requests.get(INSTITUTIONS_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        results = data.get("results", [])
        
        if not results:
            print("❌ No institutions found!")
            return None
        
        print(f"\n✅ Found {len(results)} institution(s)")
        print("=" * 90)
        
        # Automatically use the first result
        selected = results[0]
        display_name = selected.get('display_name', 'N/A')
        country = selected.get('country_code', 'N/A')
        inst_type = selected.get('type', 'N/A')
        works_count = selected.get('works_count', 0)
        inst_id = selected.get('id', '')
        
        print(f"\n✅ Automatically selected first result:")
        print(f"   Name: {display_name}")
        print(f"   ID: {inst_id}")
        print(f"   Country: {country} | Type: {inst_type} | Works: {works_count:,}")
        print("=" * 90)
        
        return inst_id
                
    except requests.exceptions.RequestException as e:
        print(f"❌ Error searching for institution: {e}")
        return None

def fetch_all_ui_ai_papers(institution_id):
    """
    Fetch ALL publications from specified institution about AI or Artificial Intelligence
    Uses pagination to get complete results
    """
    all_results = []
    page = 1
    total_results = None
    
    print("=" * 70)
    print("Fetching AI Publications from Selected Institution")
    print("=" * 70)
    
    while True:
        # Build the exact query from your URL
        params = {
            "filter": f"institutions.id:{institution_id}",
            "search": 'AI OR "Artificial Intelligence"',
            "per-page": 200,
            "page": page,
            "mailto": EMAIL
        }
        
        print(f"\nFetching page {page}...", end=" ")
        
        try:
            response = requests.get(WORKS_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Get total count on first request
            if total_results is None:
                total_results = data["meta"]["count"]
                total_pages = (total_results + 99) // 100  # Ceiling division
                print(f"\nTotal results found: {total_results}")
                print(f"Total pages to fetch: {total_pages}")
                print("-" * 70)
            
            # Get results from this page
            page_results = data.get("results", [])
            all_results.extend(page_results)
            
            print(f"✓ Got {len(page_results)} results (Total so far: {len(all_results)})")
            
            # Check if we've reached the end
            if len(page_results) == 0 or len(all_results) >= total_results:
                break
            
            # Move to next page
            page += 1
            
            # Be polite - small delay between requests
            time.sleep(0.1)
            
        except requests.exceptions.RequestException as e:
            print(f"\n❌ Error on page {page}: {e}")
            if page > 1:  # If we got some results, continue with what we have
                print("Continuing with results fetched so far...")
                break
            else:
                raise
    
    print("\n" + "=" * 70)
    print(f"✅ Fetch complete! Total papers retrieved: {len(all_results)}")
    print("=" * 70)
    
    return all_results

def save_to_csv(papers, filename="ui_ai_publications.csv"):
    """
    Save all papers to a CSV file with key information
    """
    print(f"\nSaving results to {filename}...")
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        # Define CSV columns
        fieldnames = [
            'openalex_id',
            'title',
            'doi',
            'publication_year',
            'publication_date',
            'type',
            'cited_by_count',
            'is_open_access',
            'primary_location_source',
            'first_author',
            'all_authors',
            'institutions',
            'topics',
            'keywords',
            'abstract_inverted_index',
            'url'
        ]
        
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for paper in papers:
            # Extract authors
            authorships = paper.get('authorships', [])
            first_author = authorships[0]['author']['display_name'] if authorships else ''
            all_authors = '; '.join([a['author']['display_name'] for a in authorships])
            
            # Extract institutions
            institutions = set()
            for authorship in authorships:
                for inst in authorship.get('institutions', []):
                    name = inst.get('display_name', '')
                    if name:  # Only add non-empty names
                        institutions.add(name)
            institutions_str = '; '.join(sorted(institutions)) if institutions else ''
            
            # Extract topics
            topics = paper.get('topics', [])
            topics_str = '; '.join([t.get('display_name', '') for t in topics])
            
            # Extract keywords
            keywords = paper.get('keywords', [])
            keywords_str = '; '.join([k.get('display_name', '') for k in keywords])
            
            # Primary location
            primary_location = paper.get('primary_location', {})
            source = primary_location.get('source', {})
            source_name = source.get('display_name', '') if source else ''
            
            # Write row
            writer.writerow({
                'openalex_id': paper.get('id', ''),
                'title': paper.get('title', ''),
                'doi': paper.get('doi', ''),
                'publication_year': paper.get('publication_year', ''),
                'publication_date': paper.get('publication_date', ''),
                'type': paper.get('type', ''),
                'cited_by_count': paper.get('cited_by_count', 0),
                'is_open_access': paper.get('open_access', {}).get('is_oa', False),
                'primary_location_source': source_name,
                'first_author': first_author,
                'all_authors': all_authors,
                'institutions': institutions_str,
                'topics': topics_str,
                'keywords': keywords_str,
                'abstract_inverted_index': 'Yes' if paper.get('abstract_inverted_index') else 'No',
                'url': f"https://openalex.org/{paper.get('id', '').split('/')[-1]}"
            })
    
    print(f"✅ Successfully saved {len(papers)} papers to {filename}")

def print_summary(papers):
    """
    Print a summary of the fetched papers
    """
    if not papers:
        print("No papers found!")
        return
    
    print("\n" + "=" * 70)
    print("SUMMARY STATISTICS")
    print("=" * 70)
    
    # Year distribution
    years = {}
    for paper in papers:
        year = paper.get('publication_year')
        if year:
            years[year] = years.get(year, 0) + 1
    
    print(f"\nTotal papers: {len(papers)}")
    print(f"\nPublications by year (last 10 years):")
    for year in sorted(years.keys(), reverse=True)[:10]:
        print(f"  {year}: {years[year]} papers")
    
    # Open access count
    oa_count = sum(1 for p in papers if p.get('open_access', {}).get('is_oa', False))
    print(f"\nOpen Access papers: {oa_count} ({oa_count/len(papers)*100:.1f}%)")
    
    # Most cited
    print(f"\nTop 5 most cited papers:")
    sorted_by_citations = sorted(papers, key=lambda x: x.get('cited_by_count', 0), reverse=True)
    for i, paper in enumerate(sorted_by_citations[:5], 1):
        print(f"\n  {i}. {paper.get('title', 'N/A')}")
        print(f"     Citations: {paper.get('cited_by_count', 0)}")
        print(f"     Year: {paper.get('publication_year', 'N/A')}")
        print(f"     DOI: {paper.get('doi', 'N/A')}")

if __name__ == "__main__":
    print("\n" + "█" * 70)
    print("  OpenAlex Institution AI Publications Fetcher")
    print("█" * 70)
    
    # Get institution name from user
    institution_name = input("\n📝 Enter institution name to search: ").strip()
    
    if not institution_name:
        print("❌ No institution name provided!")
        exit(1)
    
    # Search for institution and get ID
    institution_id = search_institution(institution_name)
    
    if not institution_id:
        print("\n❌ No institution selected. Exiting...")
        exit(1)
    
    # Fetch all papers
    papers = fetch_all_ui_ai_papers(institution_id)
    
    if not papers:
        print("\n⚠️  No papers found for this institution!")
        exit(0)
    
    # Save to CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Clean institution name for filename
    clean_name = "".join(c if c.isalnum() or c == ' ' else '_' for c in institution_name)
    clean_name = "_".join(clean_name.split()).lower()
    filename = f"{clean_name}_ai_publications_{timestamp}.csv"
    save_to_csv(papers, filename)
    
    # Print summary
    print_summary(papers)
    
    print("\n" + "=" * 70)
    print("✅ Process complete!")
    print("=" * 70)
