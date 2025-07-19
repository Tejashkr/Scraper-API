from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from scraper import scrape_with_fallback

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

        # Handle new structured response
        if isinstance(result, dict) and "status" in result:
            if result["status"] == "error":
                # Return error data instead of raising exception
                return {
                    "url": url,
                    "social_links": [],
                    "emails": [],
                    "message": f"Error: {result['error']}",
                    "counts": {"social_links": 0, "emails": 0}
                }
            
            # Success case
            data = result.get("data", {})
            return {
                "url": url,
                "social_links": data.get("social_links", []),
                "emails": data.get("emails", []),
                "message": "Success" if data.get("social_links") or data.get("emails") else "No data found",
                "counts": {
                    "social_links": len(data.get("social_links", [])),
                    "emails": len(data.get("emails", [])),
                }
            }

        # Legacy format fallback
        if isinstance(result, dict) and "social_links" in result:
            return {
                "url": url,
                "social_links": result["social_links"],
                "emails": result.get("emails", []),
                "message": "Success",
                "counts": {
                    "social_links": len(result["social_links"]),
                    "emails": len(result.get("emails", [])),
                }
            }

        # Unexpected format
        return {
            "url": url,
            "social_links": [],
            "emails": [],
            "message": "Unexpected result format",
            "counts": {"social_links": 0, "emails": 0}
        }

    except Exception as e:
        return {
            "url": url,
            "social_links": [],
            "emails": [],
            "message": f"Exception: {str(e)}",
            "counts": {"social_links": 0, "emails": 0}
        }

# For running directly with: `python main.py`
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)