# Docker Demo - Quick Start Commands

# Build the Docker image
docker build -t uirainus-crawler .

# Run the crawler (basic)
docker run -it uirainus-crawler

# Run with output directory mounted
docker run -it -v ${PWD}/output:/app/output uirainus-crawler

# Run in detached mode (background)
docker run -d --name uirainus-crawler-run uirainus-crawler

# View logs from detached container
docker logs -f uirainus-crawler-run

# Stop the crawler
docker stop uirainus-crawler-run

# Remove container after completion
docker rm uirainus-crawler-run
