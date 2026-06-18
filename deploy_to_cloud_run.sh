#!/bin/bash
PROJECT_ID="gen-lang-client-0797624578"
REGION="asia-south1"
IMAGE_NAME="gcr.io/$PROJECT_ID/swarmops-backend"

echo "📂 Changing to backend directory..."
cd backend || exit

echo "🚀 Building Docker image..."
docker build -t $IMAGE_NAME .

echo "📦 Pushing image to Google Cloud..."
docker push $IMAGE_NAME

echo "☁️ Deploying to Cloud Run..."
gcloud run deploy swarmops-backend \
  --image $IMAGE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars 'SUPABASE_URL=YOUR_SUPABASE_URL,SUPABASE_ANON_KEY=YOUR_SUPABASE_ANON_KEY,SUPABASE_SERVICE_ROLE_KEY=YOUR_SUPABASE_SERVICE_ROLE_KEY,OPENROUTER_API_KEY=YOUR_OPENROUTER_API_KEY'

echo "✅ Deployment pipeline complete!"
