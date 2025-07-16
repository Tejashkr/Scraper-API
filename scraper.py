import time
import threading
import re
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

SOCIAL_DOMAINS = [
    "facebook.com", "instagram.com", "twitter.com", "linkedin.com", 
    "youtube.com", "tiktok.com", "x.com"
]

EMAIL_REGEX = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"

driver_lock = threading.Lock()

# ---------------------- UC Chrome Driver ----------------------
def create_uc_driver():
    """Create undetected Chrome driver (headless)"""
    options = uc.ChromeOptions()
    options.headless = True
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-web-security")
    options.add_argument("--disable-features=VizDisplayCompositor")
    options.add_argument("--remote-debugging-port=0")

    with driver_lock:
        driver = uc.Chrome(options=options)
    return driver

def extract_emails_from_html(html):
    """Extract emails from the raw page HTML"""
    return re.findall(EMAIL_REGEX, html)

def scrape_social_links(url: str, timeout: int = 10):
    """Scrape social media links and emails using undetected_chromedriver"""
    driver = None
    try:
        driver = create_uc_driver()
        driver.get(url)
        time.sleep(timeout)

        social_links = set()
        emails = set()

        elements = driver.find_elements(By.TAG_NAME, "a")
        for el in elements:
            href = el.get_attribute("href")
            if href and any(domain in href.lower() for domain in SOCIAL_DOMAINS):
                social_links.add(href)

        # Scan other common attributes too
        for attr in ["data-href", "data-url", "data-link"]:
            elements = driver.find_elements(By.XPATH, f"//*[@{attr}]")
            for el in elements:
                href = el.get_attribute(attr)
                if href and any(domain in href.lower() for domain in SOCIAL_DOMAINS):
                    social_links.add(href)

        # Get emails from page source
        html = driver.page_source
        emails.update(extract_emails_from_html(html))

        return {
            "social_links": list(social_links),
            "emails": list(emails)
        }

    except Exception as e:
        return {"error": str(e)}

    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

# ---------------------- Regular Selenium Fallback ----------------------
def scrape_social_links_alternative(url: str, timeout: int = 10):
    """Alternative fallback using regular ChromeDriver (via webdriver-manager)"""
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager

    driver = None
    try:
        options = Options()
        options.headless = True
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-web-security")
        options.add_argument("--remote-debugging-port=0")

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

        driver.get(url)
        time.sleep(timeout)

        social_links = set()
        emails = set()

        elements = driver.find_elements(By.TAG_NAME, "a")
        for el in elements:
            href = el.get_attribute("href")
            if href and any(domain in href.lower() for domain in SOCIAL_DOMAINS):
                social_links.add(href)

        html = driver.page_source
        emails.update(extract_emails_from_html(html))

        return {
            "social_links": list(social_links),
            "emails": list(emails)
        }

    except Exception as e:
        return {"error": str(e)}

    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

# ---------------------- Smart Wrapper ----------------------
def scrape_with_fallback(url: str, timeout: int = 10):
    """Try undetected_chromedriver first, fallback to regular ChromeDriver"""
    try:
        result = scrape_social_links(url, timeout)
        if isinstance(result, dict) and "error" not in result:
            return result
    except Exception:
        pass

    try:
        result = scrape_social_links_alternative(url, timeout)
        if isinstance(result, dict) and "error" not in result:
            return result
        else:
            return {"error": "Fallback scraper returned invalid result"}
    except Exception as e:
        return {"error": f"Both methods failed. Last error: {str(e)}"}
