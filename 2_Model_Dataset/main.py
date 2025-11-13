import requests
import time
import pandas as pd

# === CONFIGURATION ===
GITHUB_TOKEN = "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"  # <--- ganti pakai tokenmu
UNIVERSITY = "Universitas Indonesia" OR "University of Indonesia"
FILE_TYPES = ["ipynb", "csv", "h5", "pth"]
PER_PAGE = 30  # maksimal 100 per halaman

headers = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "X-GitHub-Api-Version": "2022-11-28"
}

def search_files(university, file_types):
    results = []
    queries = []

    # tambahkan query untuk file types
    for ext in file_types:
        queries.append(f'extension:{ext} "{university}" in:file')

    # tambahkan query untuk README.md
    queries.append(f'filename:README.md "{university}" in:file')

    # loop semua query
    for query in queries:
        url = f"https://api.github.com/search/code?q={query}&per_page={PER_PAGE}"

        print(f"\n🔍 Searching with query: {query}")
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            for item in data.get("items", []):
                repo_name = item["repository"]["full_name"]
                file_path = item["path"]
                file_url = item["html_url"]
                results.append({
                    "repo": repo_name,
                    "file": file_path,
                    "url": file_url
                })
        else:
            print(f"⚠️ Error: {response.status_code} - {response.text}")

        # GitHub API rate limit: max 30 req/min (authenticated)
        time.sleep(2)

    return results


# === MAIN EXECUTION ===
if __name__ == "__main__":
    results = search_files(UNIVERSITY, FILE_TYPES)

    print(f"\n✅ Found {len(results)} relevant files.\n")
    for i, r in enumerate(results, 1):
        print(f"{i}. [{r['repo']}] {r['file']}\n   {r['url']}")

    # simpan ke CSV
    if results:
        pd.DataFrame(results).to_csv("github_univ_results.csv", index=False)
        print("\n📁 Results saved to github_univ_results.csv")
