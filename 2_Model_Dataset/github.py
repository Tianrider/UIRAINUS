import requests
import time
import pandas as pd
import os
from dotenv import load_dotenv

# === LOAD TOKEN DARI FILE .env ===
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# === CONFIGURATION ===
UNIVERSITY = "Universitas Indonesia" OR "University of Indonesia"
FILE_TYPES = ["ipynb", "csv", "h5", "pth"]
PER_PAGE = 30  # maksimal 100 per halaman

headers = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "X-GitHub-Api-Version": "2022-11-28"
}

# === STEP 1: CARI REPO DENGAN README YANG MENGANDUNG UNIVERSITAS ===
def search_repos_with_readme(university):
    print(f"\n🔍 Searching repositories mentioning {university} in README...")
    query = f'filename:README.md "{university}" in:file'
    url = f"https://api.github.com/search/code?q={query}&per_page={PER_PAGE}"

    repos = set()
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        for item in data.get("items", []):
            repo_name = item["repository"]["full_name"]
            repos.add(repo_name)
        print(f"✅ Found {len(repos)} repositories mentioning {university}")
    else:
        print(f"⚠️ Error: {response.status_code} - {response.text}")

    time.sleep(2)
    return list(repos)

# === STEP 2: CARI FILE BEREKSTENSI TERTENTU DI REPO TERSEBUT ===
def search_files_in_repos(repos, file_types):
    results = []
    for repo in repos:
        for ext in file_types:
            query = f'repo:{repo} extension:{ext}'
            url = f"https://api.github.com/search/code?q={query}&per_page={PER_PAGE}"

            print(f"\n📂 Searching *.{ext} files in {repo}...")
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                data = response.json()
                for item in data.get("items", []):
                    results.append({
                        "repo": repo,
                        "file": item["path"],
                        "url": item["html_url"],
                        "extension": ext
                    })
            else:
                print(f"⚠️ Error: {response.status_code} - {response.text}")

            time.sleep(2)
    return results


# === MAIN EXECUTION ===
if __name__ == "__main__":
    repos = search_repos_with_readme(UNIVERSITY)
    results = search_files_in_repos(repos, FILE_TYPES)

    print(f"\n✅ Found total {len(results)} relevant files across {len(repos)} repositories.\n")
    for i, r in enumerate(results, 1):
        print(f"{i}. [{r['repo']}] {r['file']} ({r['extension']})\n   {r['url']}")

    # simpan ke CSV
    if results:
        pd.DataFrame(results).to_csv("github_univ_results.csv", index=False)
        print("\n📁 Results saved to github_univ_results.csv")
