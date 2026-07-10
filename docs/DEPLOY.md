# Deploy OmniForge

## API (Render) — done

Live: https://omniforge-api.onrender.com

Env to set on Render:

| Key | Notes |
|-----|--------|
| `OMNIFORGE_MODE` | `live` |
| `OPENAI_API_KEY` | optional |
| `ANTHROPIC_API_KEY` | optional |
| `GROQ_API_KEY` | optional |
| `GOOGLE_API_KEY` | Gemini cascade (optional) |
| `CORS_ORIGINS` | include your Vercel URL, e.g. `https://omniforge.vercel.app,https://venkat-ai.com` |

Health: `GET /health`

## UI (Vercel) — manual deploy

The UI is a **static export** (`output: "export"` → `ui/out`). Do **not** use the default Next.js serverless preset.

### Project settings (Vercel dashboard)

1. **Import** `vpeetla-ai/omniforge`
2. **Root Directory:** `ui`  ← critical
3. **Framework Preset:** Other (`framework: null` in `ui/vercel.json`)
4. **Build Command:** `npm run build`
5. **Output Directory:** `out`
6. **Install Command:** `npm install`
7. **Environment variable:**
   - `NEXT_PUBLIC_API_URL` = `https://omniforge-api.onrender.com`

### Why builds looked “stuck”

`framework: "nextjs"` + static `out/` fights Vercel’s Next.js runtime. After pages generate, “Collecting build traces” can hang or fail the deploy step. Fixed config uses `framework: null` (same pattern as DomainForge).

### CLI manual deploy (optional)

```bash
cd ui
npm install
NEXT_PUBLIC_API_URL=https://omniforge-api.onrender.com npm run build
npx vercel --prod --yes
# when prompted / in project link: root = ui, output = out
```

Or from repo root with linked project:

```bash
cd ui && npx vercel --prod --yes
```

After deploy, add the Vercel URL to Render `CORS_ORIGINS` and redeploy the API if needed.

Cold start on Render free tier may take ~30s on first Ask.
