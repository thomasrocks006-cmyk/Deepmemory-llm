#!/bin/bash

cd /workspaces/Deepmemory-llm/frontend

echo "🧹 Cleaning previous builds..."
rm -rf .next

echo "🚀 Starting Next.js development server..."
npm run dev
