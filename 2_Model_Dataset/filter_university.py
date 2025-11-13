import os
import time
import requests
import pandas as pd
from dotenv import load_dotenv

# === KONFIGURASI ===
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise ValueError("❌ GITHUB_TOKEN tidak ditemukan di .env")

TARGET_KEYWORDS = [
    "universitas indonesia",
    "university of indonesia",
    "ui.ac.id",
    "Artificial Intelligence",
    "Machine Learning",
    "Deep Learning",
    "AI",
    "ML"
]

VALID_EXTENSIONS = [".md", ".ipynb", ".csv", ".txt"]

headers = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "X-GitHub-Api-Version": "2022-11-28"
}

# === LOAD DATA ===
df = pd.read_csv("github_univ_results.csv")
print(f"📂 Data awal: {len(df)} baris")

results = []

# === LOOP SETIAP FILE ===
for i, row in df.iterrows():
    repo = row["repo"]
    file_path = row["file"]
    file_url = row["url"]

    # Skip kalau ekstensi file tidak termasuk
    if not any(file_path.endswith(ext) for ext in VALID_EXTENSIONS):
        continue

    print(f"[{i+1}/{len(df)}] Mengecek: {file_path}")

    try:
        response = requests.get(file_url, headers=headers)
        if response.status_code == 200:
            content = response.text.lower()

            # Cek apakah ada keyword universitas
            if any(keyword in content for keyword in TARGET_KEYWORDS):
                results.append(row)
                print(f"   ✅ Relevan (menyebut universitas target)")
            else:
                print(f"   ❌ Tidak menyebut universitas target")
        else:
            print(f"   ⚠️ Error {response.status_code}")
    except Exception as e:
        print(f"   ⚠️ Gagal baca file: {e}")

    # Delay biar aman dari rate limit (GitHub REST limit = 5000 requests/jam)
    time.sleep(1.5)

# === OUTPUT ===
filtered_df = pd.DataFrame(results)
filtered_df.to_csv("filtered_university.csv", index=False)

print(f"\n✅ Ditemukan {len(filtered_df)} file relevan dari {len(df)} total file.")
print("📁 Hasil disimpan di: filtered_university.csv")
