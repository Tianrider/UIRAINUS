# University AI Research Analysis System

A comprehensive analysis system that processes university AI research data across 4 key dimensions:

1. **Publications** (OpenAlex API)
2. **Models & Datasets** (HuggingFace Hub)
3. **AI Policies** (Web scraping with AI agent)
4. **Organizational Structure** (Organigram with AI division identification)

## 🚀 Quick Start

### Run Complete Analysis

```bash
python orchestrator.py "University of Indonesia"
```

Or run interactively:

```bash
python orchestrator.py
```

Then enter the university name when prompted.

## 📁 Output Structure

All results are saved to: `outputs/[university-name]/`

```
outputs/
└── university_of_indonesia/
    ├── publications_20251118_120000.csv
    ├── huggingface_20251118_120000.csv
    ├── huggingface_20251118_120000.json
    ├── policies_20251118_120000.csv
    ├── organigram_20251118_120000.csv
    └── analysis_summary.json
```

## 📊 Output Files

### 1. Publications CSV

Contains AI-related publications from OpenAlex:

- Title, DOI, Publication date
- Authors and institutions
- Citation count
- Topics and keywords
- Open access status

### 2. HuggingFace CSV/JSON

Contains AI models and datasets:

- Model/Dataset ID
- Author information
- Tags and categories
- Pipeline information

### 3. Policies CSV

Contains AI policy documents:

- Policy title and URL
- Document type (PDF/webpage)
- Publishing date
- Department

### 4. Organigram CSV

Contains AI division information:

- Division/Department name
- Chair name and title
- Source URL

### 5. Analysis Summary JSON

Contains metadata about the analysis run:

- Timestamp
- Processing duration
- Success/failure status for each step

## 🔧 Individual Module Usage

Each processing step can also be run independently:

### Publications Analysis

```bash
cd 1_Publication
python openAlex.py
```

### Model & Dataset Analysis

```bash
cd 2_Model_Dataset/HuggingFace
python main.py --university "University Name"
```

### Policy Analysis

```bash
cd 3_Policy
python main.py
```

### Organigram Analysis

```bash
cd 4_Organigram
python main.py
```

## 📦 Requirements

Install dependencies:

```bash
pip install -r requirements.txt
```

Key packages:

- `requests` - API calls
- `browser-use` - Browser automation
- `pydantic` - Data validation
- `huggingface_hub` - HuggingFace API
- `python-dotenv` - Environment variables
- `steel-python` - Browser session management

## 🔑 Environment Setup

Create a `.env` file in the root directory:

```env
STEEL_API_KEY=your_steel_api_key
GOOGLE_API_KEY=your_google_api_key
```

## 🎯 Features

- ✅ Unified interface for all analysis steps
- ✅ Automatic output organization by university
- ✅ CSV reports for all data sources
- ✅ Pydantic structured output validation
- ✅ Progress tracking and error handling
- ✅ Summary report generation
- ✅ Command-line and interactive modes

## 📝 Notes

- The orchestrator runs all 4 steps sequentially
- Each step is independent - if one fails, others continue
- Results are timestamped to prevent overwriting
- University names are sanitized for folder creation
- All CSV files use UTF-8 encoding

## 🤝 Contributing

To add new analysis modules:

1. Create a new folder with your module
2. Implement CSV output functionality
3. Add the step to `orchestrator.py`
4. Update this README

## 📄 License

Educational/Research use only.
