#!/bin/bash
# deploy.sh

# Build the production image
docker build -t stackr -f Dockerfile.prod .

# Launch Fly.io deployment
fly launch --name stackr-cold-violet-2349 --dockerfile Dockerfile.prod

# Set environment variables
# ...

# Scale the app
fly scale count 1

# Deploy the app
fly deploy