#!/bin/bash
set -e
echo "🎯 Build Baccarat Predictor"

cd frontend
npm ci --only=production
npm run build
echo "✅ Frontend built → dist/"
mv dist/* ../backend/staticdist/
echo "✅ Assets → staticdist/"

cd ../backend
pip install --only-binary=all -r requirements.txt
echo "✅ Backend deps OK"

echo "🚀 Deploy listo!"