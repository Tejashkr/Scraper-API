from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from scraper import scrape_with_fallback  # This should return a dict with social_links and emails

app = FastAPI()

# CORS setup for cross-origin requests (e.g., from n8n, Postman)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins — customize if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Web Scraper API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "API is running"}

@app.get("/scrape")
async def scrape(url: str, timeout: int = 10):
    """Scrape social media links and emails from the given URL."""
    if not url:
        raise HTTPException(status_code=400, detail="URL parameter is required")

    # Ensure URL starts with http/https
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, scrape_with_fallback, url, timeout)

        # Case 1: result contains error
        if isinstance(result, dict) and "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        # Case 2: valid structured result
        if isinstance(result, dict) and "social_links" in result and "emails" in result:
            return {
                "url": url,
                "social_links": result["social_links"],
                "emails": result["emails"],
                "message": "Success" if result["social_links"] or result["emails"] else "No data found",
                "counts": {
                    "social_links": len(result["social_links"]),
                    "emails": len(result["emails"]),
                }
            }

        # Case 3: fallback legacy behavior (list result)
        if isinstance(result, list):
            return {
                "url": url,
                "social_links": result,
                "emails": [],
                "message": "Only social links found (no emails)",
                "counts": {
                    "social_links": len(result),
                    "emails": 0,
                }
            }

        # Fallback case
        raise HTTPException(status_code=500, detail="Unexpected scraping result format")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")

# For running directly with: `python main.py`
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
