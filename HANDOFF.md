# UIRAINUS (University AI Research Analysis System) - Handoff Documentation

## 1. Project Overview

**UIRAINUS** is a comprehensive analysis system designed to evaluate a university's AI research footprint across four key dimensions. It automates data collection from various sources to provide a holistic view of an institution's AI activities.

**Key Dimensions:**

1.  **Publications**: Fetches AI-related research papers from OpenAlex.
2.  **Models & Datasets**: Identifies AI models and datasets hosted on HuggingFace.
3.  **Policies**: Uses AI agents to scrape and identify official university AI policies.
4.  **Organigram**: Uses AI agents to map organizational structures and identify AI-specific divisions/leadership.

## 2. Tech Stack

- **Language**: Python
- **Core Frameworks & Libraries**:
  - **`browser-use`**: Used for the AI agents in the Policy and Organigram modules to perform autonomous web browsing and scraping.
  - **`langchain_google_genai` / `ChatGoogle`**: Uses Google's Gemini models (specifically `gemini-flash-latest`) as the brain for the agents.
  - **`steel-python`**: Manages browser sessions for the agents.
  - **`huggingface_hub`**: Interacts with the HuggingFace API.
  - **`requests`**: Handles HTTP requests for the OpenAlex API.
  - **`pydantic`**: Ensures structured data output (JSON) from the AI agents.
  - **`python-dotenv`**: Manages environment variables.
  - **`serpapi`** (Optional): Used in the HuggingFace module for advanced Google dorking.

## 3. Project Structure

The project is organized into modular components, orchestrated by a central script.

```text
UIRAINUS/
├── .venv/                       # Virtual environment directory
├── orchestrator.py              # MAIN ENTRY POINT. Coordinates all 4 steps.
├── requirements.txt             # Project dependencies.
├── .env                         # API keys (STEEL_API_KEY, GOOGLE_API_KEY, etc.)
├── outputs/                     # Generated results, organized by university folder.
│   └── [university_name]/       # e.g., university_of_indonesia/
│       ├── analysis_summary.json
│       ├── publications_*.csv
│       ├── huggingface_*.csv
│       ├── policies_*.csv
│       └── organigram_*.csv
├── 1_Publication/
│   └── openAlex.py              # Fetches papers via OpenAlex API.
├── 2_Model_Dataset/
│   └── HuggingFace/
│       └── huggingface.py       # Searches HuggingFace Hub (API + Google Dork).
├── 3_Policy/
│   └── computer-use.py          # AI Agent for finding policy documents.
└── 4_Organigram/
    └── computer-use.py          # AI Agent for finding organizational structure.
```

## 4. Module Details

### Step 1: Publication Analysis (`1_Publication/openAlex.py`)

- **Source**: OpenAlex API.
- **Logic**:
  1.  Searches for the institution ID by name.
  2.  Fetches all works filtered by that institution ID and the search term "AI OR 'Artificial Intelligence'".
  3.  Handles pagination automatically.
- **Output**: A CSV containing title, DOI, authors, citations, topics, and open access status.

### Step 2: Model & Dataset Analysis (`2_Model_Dataset/HuggingFace/huggingface.py`)

- **Source**: HuggingFace Hub.
- **Logic**:
  1.  Sanitizes the university name.
  2.  Searches the Hub for models and datasets matching the name.
  3.  **Advanced Feature**: Can optionally use `serpapi` to run a Google dork (`"University Name" site:huggingface.co`) to find resources that standard search might miss.
- **Output**: JSON and CSV files listing models, datasets, authors, and tags.

### Step 3: Policy Analysis (`3_Policy/computer-use.py`)

- **Source**: Web Scraping (Google Search + University Websites).
- **Logic**:
  1.  Initializes a `browser-use` agent with a `ChatGoogle` LLM.
  2.  Agent searches for official policies (e.g., "University Name Policy").
  3.  Verifies the domain is an official university domain (e.g., `.edu`, `.ac.id`).
  4.  Extracts title, URL, type, date, and department.
- **Output**: Returns a structured JSON array via Pydantic validation (`PolicyResults` model).

### Step 4: Organigram Analysis (`4_Organigram/computer-use.py`)

- **Source**: Web Scraping (Google Search + University Websites).
- **Logic**:
  1.  Initializes a `browser-use` agent.
  2.  Searches for organigrams or "People" pages.
  3.  Analyzes the structure to find divisions with "AI", "Machine Learning", "Data Science", etc.
  4.  Identifies the Chair/Head of those divisions.
- **Output**: Returns a structured JSON array via Pydantic validation (`OrganigramResults` model).

## 5. How to Run

### Prerequisites

1.  **Virtual Environment Setup**:
    The project uses a virtual environment named `.venv`.

    - **Create (if missing)**:
      ```bash
      python -m venv .venv
      ```
    - **Activate**:
      - **Windows (PowerShell)**:
        ```powershell
        .\.venv\Scripts\Activate.ps1
        ```
      - **Windows (CMD)**:
        ```cmd
        .venv\Scripts\activate.bat
        ```
      - **Mac/Linux**:
        ```bash
        source .venv/bin/activate
        ```

2.  **Install Dependencies**:
    Once the environment is activated:

    ```bash
    pip install -r requirements.txt
    ```

3.  **Environment Variables**:
    Create a `.env` file in the root with the following keys:
    ```env
    STEEL_API_KEY=your_steel_key
    GOOGLE_API_KEY=your_google_gemini_key
    SERPAPI_API_KEY=your_serpapi_key  # Optional, for advanced HF search
    ```

### Execution

You can run the entire pipeline or individual modules.

- **Run Everything (Recommended):**

  ```bash
  python orchestrator.py "University of Indonesia"
  ```

  _Or run without arguments to enter interactive mode._

- **Run Individual Modules:**
  - **Publications**: `cd 1_Publication && python openAlex.py`
  - **HuggingFace**: `cd 2_Model_Dataset/HuggingFace && python huggingface.py --university "Harvard University"`
  - **Policy**: `cd 3_Policy && python computer-use.py` (Note: Default is hardcoded to "Harvard University" in `main()`, modify if needed for standalone run).
  - **Organigram**: `cd 4_Organigram && python computer-use.py` (Note: Default is hardcoded to "Harvard University" in `main()`).

## 6. Important Notes for Handoff

- **Agent Configuration**: The agents in steps 3 and 4 are configured to use **Vision** (`use_vision=True`), which helps them read PDFs and complex web layouts.
- **Error Handling**: The `orchestrator.py` is designed to be resilient. If one step fails (e.g., no policies found), it logs the error and proceeds to the next step.
- **Output Management**: The orchestrator automatically creates a "safe" folder name (e.g., `university_of_indonesia`) and timestamps all files to prevent data loss.
- **Dependencies**: Ensure `browser-use` and `steel-python` are correctly installed and API keys are valid, as these are the most complex parts of the setup.
