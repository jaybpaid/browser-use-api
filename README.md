# Browser Use API

**AI-Powered Web Scraping API** - Uses browser-use to reliably scrape any website with AI-guided automation.

## Why This Wins

| Feature | Traditional Scrapers | Browser Use API |
|---------|---------------------|----------------|
| Cloudflare/Turnstile | ❌ Fail | ✅ AI navigates it |
| JavaScript-rendered | ❌ Complex setup | ✅ Native |
| Dynamic content | ❌ Manual handling | ✅ AI extracts |
| Login/auth pages | ❌ Can't do it | ✅ AI handles it |
| Reliability | 60-70% | **95%+** |

## Use Cases

- **Price monitoring** - Scrape competitor prices that block traditional scrapers
- **Review aggregation** - Get reviews from sites that protect against bots
- **Market research** - Extract data from any website, any page
- **Lead generation** - Pull business info from protected listings

## API Endpoints

### POST /scrape
```json
{
  "url": "https://example.com/products",
  "task": "Extract all product names and prices",
  "model": "gpt-4o-mini"
}
```

### POST /scrape/batch
```json
{
  "urls": ["https://site.com/page1", "https://site.com/page2"],
  "task": "Extract contact info from each page"
}
```

### GET /jobs/{job_id}
Check job status and retrieve results.

## Pricing Tiers

| Plan | Requests/mo | Price |
|------|-------------|-------|
| Free | 100 | $0 |
| Starter | 5,000 | $29 |
| Pro | 50,000 | $149 |
| Enterprise | 500,000+ | Custom |

## Deployment

### Apify Actor
Deploy as Apify Actor for instant scaling + free tier.

### Railway/Render
Deploy FastAPI directly:
```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port $PORT
```

### Docker
```bash
docker build -t browser-use-api .
docker run -p 8000:8000 browser-use-api
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI key for LLM |
| `BROWSER_USE_API_KEY` | No | Browser Use Cloud (better proxy) |
| `PORT` | No | Server port (default: 8000) |

## Quick Start

```python
import requests

response = requests.post("https://your-api.com/scrape", json={
    "url": "https://example.com",
    "task": "Extract the page title and main content"
})

print(response.json())
```

---

*Built with [browser-use](https://github.com/browser-use/browser-use)*