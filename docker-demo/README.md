# UIRAINUS AI Research Intelligence System - Docker Demo

This Docker container runs a comprehensive AI research intelligence crawler that processes the top 100 universities from QS World Rankings.

## Features

The crawler performs 4 main stages for each university:

1. **Publication Crawling**: Fetches AI ethics publications from OpenAlex
2. **Model & Dataset Discovery**:
   - Searches GitHub repositories for AI models and datasets
   - Queries HuggingFace Model Hub
   - Extracts models/datasets from publication references
3. **Policy Analysis**: Crawls institutional websites for AI ethics policies
4. **Organizational Mapping**: Extracts organizational structure and research groups

## Build and Run

### Build the Docker image:

```bash
docker build -t uirainus-crawler .
```

### Run the crawler:

```bash
docker run -it uirainus-crawler
```

### Run with output volume (to save results):

```bash
docker run -it -v $(pwd)/output:/app/output uirainus-crawler
```

## Performance

- **Processing time per university**: 20-30 minutes
- **Total estimated time**: ~33-50 hours for 100 universities
- **Target universities**: Top 100 QS World Rankings

## Output

The crawler logs real-time progress showing:

- API connections and rate limits
- Data retrieval statistics
- Processing status for each stage
- Summary statistics per university
- Overall progress and time estimates

## Technical Stack

- Python 3.11
- Multi-source data aggregation (OpenAlex, GitHub, HuggingFace)
- Institutional web scraping
- Real-time logging and progress tracking
