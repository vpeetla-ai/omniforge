# Deploy OmniForge

## API (Render)

1. Connect repo → Blueprint `render.yaml`
2. Set secrets: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GROQ_API_KEY` (optional)
3. Set `OMNIFORGE_MODE=live` when keys present, else `mock`
4. Health: `GET /health`

## UI (Vercel)

1. Root directory: `ui`
2. Env: `NEXT_PUBLIC_API_URL=https://omniforge-api.onrender.com`
3. Build: `npm run build` (static export)

Cold start on Render free tier may take ~30s.
