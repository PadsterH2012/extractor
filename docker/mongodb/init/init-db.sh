#!/bin/bash
# MongoDB initialization script for AI-Powered Extraction v3

echo "Initializing MongoDB for AI-Powered Extraction v3..."

# Switch to the application database
mongosh rpger --eval "
  // Create collections with proper indexes
  db.createCollection('extractions');
  db.createCollection('characters');
  db.createCollection('locations');
  db.createCollection('items');
  db.createCollection('spells');
  db.createCollection('sessions');

  // Create indexes for better performance
  db.extractions.createIndex({ 'game_type': 1, 'edition': 1 });
  db.extractions.createIndex({ 'created_at': -1 });
  db.extractions.createIndex({ 'source_file': 1 });
  
  db.characters.createIndex({ 'name': 'text', 'description': 'text' });
  db.locations.createIndex({ 'name': 'text', 'description': 'text' });
  db.items.createIndex({ 'name': 'text', 'description': 'text' });
  db.spells.createIndex({ 'name': 'text', 'description': 'text' });
  
  db.sessions.createIndex({ 'session_id': 1 });
  db.sessions.createIndex({ 'created_at': -1 });

  print('MongoDB initialization completed for AI-Powered Extraction v3');
"