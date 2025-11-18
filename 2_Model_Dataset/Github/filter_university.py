import os
import time
import requests
import pandas as pd
from dotenv import load_dotenv

# === KONFIGURASI ===
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Pisahkan keyword agar logika filternya lebih ketat (AND logic)
KEYWORDS_UNIV = [
    "universitas indonesia",
    "university of indonesia",
    "ui.ac.id",
]

KEYWORDS_AI = [
    "artificial intelligence",
    "machine learning",
    "deep learning",
    "neural network",
    "dataset",
    "model",
    "sklearn",
    "tensorflow",
    "pytorch",
    "keras",
    "dataframe",
    "classification",
    "clustering"
]

# Hanya file teks yang bisa dibaca
VALID_EXTENSIONS = [".md", ".ipynb", ".csv", ".txt", ".py", ".json"]

headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}"
}

# === FUNGSI BANTUAN ===
def convert_to_raw_url(html_url):
    """
    Mengubah URL halaman GitHub menjadi URL Raw Content.
    Contoh:
    Dari: https://github.com/user/repo/blob/main/file.txt
    Ke:   https://raw.githubusercontent.com/user/repo/main/file.txt
    """
    return html_url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")

# === LOAD DATA ===
try:
    df = pd.read_csv("github_univ_results2.csv")
    print(f"📂 Data awal: {len(df)} baris")
except FileNotFoundError:
    print("❌ File 'github_univ_results2.csv' tidak ditemukan!")
    exit()

results = []

# === LOOP SETIAP FILE ===
for i, row in df.iterrows():
    repo = row["repo"]
    file_path = row["file"]
    original_url = row["url"]

    # 1. Filter Ekstensi
    if not any(file_path.endswith(ext) for ext in VALID_EXTENSIONS):
        continue

    # 2. Ubah ke Raw URL (PENTING!)
    raw_url = convert_to_raw_url(original_url)

    print(f"[{i+1}/{len(df)}] Cek Konten: {repo} ... ", end="")

    try:
        # Request ke Raw URL
        response = requests.get(raw_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            # Ambil konten dan jadikan huruf kecil semua biar gampang dicari
            content = response.text.lower()
            
            # 3. Logika Filter Ketat (AND Logic)
            # Harus ada 'Universitas Indonesia' dan 'AI'
            has_univ = any(k in content for k in KEYWORDS_UNIV)
            has_ai = any(k in content for k in KEYWORDS_AI)

            if has_univ and has_ai:
                # Simpan data
                row["raw_url"] = raw_url # Simpan juga link raw-nya
                results.append(row)
                print(f"✅ MATCH! (Univ + AI)")
            elif has_univ:
                print(f"❌ Skip (Hanya Univ, bukan AI)")
            elif has_ai:
                print(f"❌ Skip (Hanya AI, bukan Univ)")
            else:
                print(f"❌ Skip (Tidak relevan)")
        
        elif response.status_code == 404:
            print(f"⚠️ 404 Not Found (Mungkin private/dihapus)")
        else:
            print(f"⚠️ Error {response.status_code}")

    except Exception as e:
        print(f"⚠️ Gagal request: {e}")

    # Delay sedikit biar sopan ke server GitHub
    time.sleep(1)

# === OUTPUT ===
if results:
    filtered_df = pd.DataFrame(results)
    filtered_df.to_csv("filtered_university_final.csv", index=False)

    print(f"\n✅ HASIL AKHIR: Ditemukan {len(filtered_df)} file SUPER RELEVAN.")
    print("📁 Disimpan di: filtered_university_final.csv")
    
    # Tampilkan preview
    print("\nPreview 3 teratas:")
    print(filtered_df[["repo", "file"]].head(3))
else:
    print("\n❌ Tidak ada file yang lolos filter ketat.")