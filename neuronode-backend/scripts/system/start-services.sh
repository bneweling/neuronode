#!/bin/bash
docker-compose up -d neo4j chromadb redis
echo "Warte auf Services..."
sleep 10
docker-compose ps
