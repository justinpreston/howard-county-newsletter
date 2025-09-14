#!/bin/bash

# Navigate to the project directory
cd "$(dirname "$0")/.."

# Pull the latest changes from the repository
git pull origin main

# Build the Docker containers
docker-compose up -d --build

# Run database migrations (if applicable)
# Uncomment the following line if you have migrations to run
# docker-compose exec app npm run migrate

# Start the n8n workflow
docker-compose up -d n8n

# Output the status of the deployment
echo "Deployment completed. Check the logs for any errors."
docker-compose logs -f n8n