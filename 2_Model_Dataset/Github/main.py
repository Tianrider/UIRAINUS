import requests
import time
import pandas as pd
import os
from dotenv import load_dotenv

# === CONFIGURATION ===
load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
# Pastikan token
if not GITHUB_TOKEN:
    print("❌ Error: GITHUB_TOKEN tidak ditemukan di .env")
    exit()

# List Universitas
UNIVERSITY_LIST = ["Universitas Indonesia", "University of Indonesia"]

# Tipe file
FILE_TYPES = ["ipynb", "csv", "h5", "pth"]
PER_PAGE = 30 

headers = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "X-GitHub-Api-Version": "2022-11-28"
}

def search_files(univ_list, file_types):
    results = []
    queries = []

    # Loop universitasnya cek file
    for univ in univ_list:
        
        # 1. Query untuk tipe file spesifik
        for ext in file_types:
            # Query: extension:ipynb "Universitas Indonesia" in:file
            queries.append(f'extension:{ext} "{univ}" in:file')

        # 2. Query untuk README.md
        queries.append(f'filename:README.md "{univ}" in:file')

    print(f"📋 Total queries yang akan dijalankan: {len(queries)}")

    # === EKSEKUSI REQUEST ===
    for query in queries:
        url = f"https://api.github.com/search/code?q={query}&per_page={PER_PAGE}"

        print(f"\n🔍 Searching: {query}")
        
        try:
            response = requests.get(url, headers=headers)

            # Handle Rate Limit (Penting!)
            if response.status_code in [403, 429]:
                print("⏳ Rate limited! Menunggu 10 detik...")
                time.sleep(10)
                continue

            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                print(f"   👉 Ditemukan: {len(items)} item")

                for item in items:
                    repo_name = item["repository"]["full_name"]
                    file_path = item["path"]
                    file_url = item["html_url"]
                    
                    # Mencegah duplikasi data
                    if not any(r['url'] == file_url for r in results):
                        results.append({
                            "keyword": query, # Biar tau ini hasil query yg mana
                            "repo": repo_name,
                            "file": file_path,
                            "url": file_url
                        })
            else:
                print(f"⚠️ Error {response.status_code}: {response.text}")

        except Exception as e:
            print(f"❌ Connection Error: {e}")

        # Jeda antar request (Code Search API limit)
        time.sleep(5) 

    return results


# === MAIN EXECUTION ===
if __name__ == "__main__":
    
    print("🚀 Memulai pencarian...")
    results = search_files(UNIVERSITY_LIST, FILE_TYPES)

    print(f"\n✅ SELESAI! Ditemukan total {len(results)} file relevan.\n")
    
    # Preview 5 hasil pertama
    for i, r in enumerate(results[:5], 1):
        print(f"{i}. [{r['repo']}] {r['file']}")

    # Simpan ke CSV
    if results:
        pd.DataFrame(results).to_csv("github_univ_results2.csv", index=False)
        print("\n📁 Results saved to github_univ_results2.csv")
    else:
        print("Tidak ada data yang ditemukan.")