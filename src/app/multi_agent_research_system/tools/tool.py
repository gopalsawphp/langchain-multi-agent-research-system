import requests
import trafilatura
import re
from langchain.tools import tool
from tavily import TavilyClient
from app.multi_agent_research_system.multi_agent import get_env_variable
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import json
import logging
import ipaddress
import socket
logger = logging.getLogger(__name__)

# DYNAMIC SCRAPER CONFIGURATION
# Change these values whenever required.
# ==================================================
MAX_WORDS = 1200             # Maximum extracted words per webpage
MAX_DOWNLOAD_BYTES = 1_000_000  # Maximum HTML download: 1 MB
CONNECT_TIMEOUT = 5
READ_TIMEOUT = 20
MAX_REDIRECTS = 3
MIN_CONTENT_WORDS = 50       # Reject pages with too little content


def get_tavily_search() -> TavilyClient:
    return TavilyClient(
        api_key=get_env_variable("TAVILY_API_KEY"),
    )

@tool
def tavily_web_search_tool(query: str) -> str:
    """
    Search the web using Tavily and return at most 3 actual search results.
    Preserve the original titles, URLs, snippets, and scores.
    Never invent or modify source information.
    """
    if not query or not query.strip():
        return json.dumps({
            "query": query,
            "results": [],
            "error": "Query cannot be empty",
        })

    try:
        response = get_tavily_search().search(
            query=query.strip(),
            search_depth="advanced",
            max_results=3,
            topic="general",
        )

        results = response.get("results", [])

        output = []

        for item in results[:3]:
            output.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": item.get("content", "")[:1000],
                "score": item.get("score"),
            })

        return json.dumps(
            {
                "query": query.strip(),
                "result_count": len(output),
                "results": output,
            },
            ensure_ascii=False,
            indent=2,
        )

    except Exception:
        logger.exception("Tavily search failed")

        return json.dumps({
            "query": query.strip(),
            "results": [],
            "error": "Web search failed. Check server logs.",
        })


@tool
def get_weatherstack_tool(city: str) -> str:
    """Fetches weather information for a given city using the Weatherstack API."""
    res = requests.get(
        f"http://api.weatherstack.com/current?access_key={ get_env_variable("WEATHERSTACK_API_KEY")}&query={city}"
    ).json()
    if "current" not in res:
        return f"Failed to retrieve weather information for {city}."
    return (
        f"City: {city}\n"
        f"Temperature: {res['current']['temperature']}°C\n"
        f"Weather: {res['current']['weather_descriptions'][0]}.\n"
        f"Humidity: {res['current']['humidity']}%\n"
        f"WindSpeed: {res['current']['wind_speed']} km/h\n"
    )

def validate_public_url(url: str) -> None:
    """Validate URL and reject non-public network destinations."""
    parsed = urlparse(url)

    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username
        or parsed.password
    ):
        raise ValueError("A valid public HTTP/HTTPS URL is required.")

    hostname = parsed.hostname.lower()

    if hostname == "localhost" or hostname.endswith(".localhost"):
        raise ValueError("Local URLs are not allowed.")

    try:
        addresses = {
            item[4][0]
            for item in socket.getaddrinfo(
                hostname,
                parsed.port or (
                    443 if parsed.scheme == "https" else 80
                ),
            )
        }
    except socket.gaierror as exc:
        raise ValueError("Hostname could not be resolved.") from exc

    if not addresses:
        raise ValueError("No IP addresses found for hostname.")

    for address in addresses:
        if not ipaddress.ip_address(address).is_global:
            raise ValueError("Private or non-public URLs are not allowed.")


def limit_words(text: str, max_words: int) -> str:
    """Limit extracted content to a configurable word count."""
    words = text.split()
    return " ".join(words[:max_words])


@tool
def scrape_url(url: str) -> str:
    """
    Extract readable content from a public webpage.

    Uses Trafilatura first and BeautifulSoup as a fallback.
    Returns page title, final URL, extraction method, word count,
    and content limited to MAX_WORDS.

    Does not invent or summarize webpage content.
    """
    try:
        validate_public_url(url)

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml",
        }

        current_url = url
        session = requests.Session()

        try:
            for _ in range(MAX_REDIRECTS + 1):
                validate_public_url(current_url)

                with session.get(
                    current_url,
                    headers=headers,
                    timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
                    allow_redirects=False,
                    stream=True,
                ) as response:

                    if response.is_redirect or response.is_permanent_redirect:
                        location = response.headers.get("Location")

                        if not location:
                            return "ERROR: Redirect missing Location header."

                        from urllib.parse import urljoin

                        current_url = urljoin(current_url, location)
                        continue

                    response.raise_for_status()

                    content_type = response.headers.get(
                        "Content-Type", ""
                    ).lower()

                    if not any(
                        kind in content_type
                        for kind in (
                            "text/html",
                            "application/xhtml+xml",
                        )
                    ):
                        return (
                            "ERROR: Unsupported content type: "
                            f"{content_type or 'unknown'}"
                        )

                    content_length = response.headers.get("Content-Length")

                    if content_length:
                        try:
                            if int(content_length) > MAX_DOWNLOAD_BYTES:
                                return "ERROR: Webpage exceeds download size limit."
                        except ValueError:
                            pass

                    chunks = []
                    total_bytes = 0

                    for chunk in response.iter_content(16_384):
                        total_bytes += len(chunk)

                        if total_bytes > MAX_DOWNLOAD_BYTES:
                            return "ERROR: Webpage exceeds download size limit."

                        chunks.append(chunk)

                    encoding = response.encoding or "utf-8"
                    page_html = b"".join(chunks).decode(
                        encoding, errors="replace"
                    )
                    final_url = response.url
                    break
            else:
                return "ERROR: Maximum redirect count exceeded."

        finally:
            session.close()

        soup = BeautifulSoup(page_html, "html.parser")

        title = (
            soup.title.get_text(" ", strip=True)
            if soup.title
            else "Untitled page"
        )

        # Strategy 1: Extract article/main content.
        content = None
        extraction_method = None

        try:
            content = trafilatura.extract(
                page_html,
                url=final_url,
                include_comments=False,
                include_tables=True,
                favor_precision=True,
            )

            if content and content.strip():
                extraction_method = "trafilatura"
        except Exception:
            logger.warning(
                "Trafilatura failed for %s",
                final_url,
                exc_info=True,
            )

        # Strategy 2: Fallback to BeautifulSoup.
        if not content:
            for element in soup(
                [
                    "script",
                    "style",
                    "nav",
                    "footer",
                    "header",
                    "aside",
                    "noscript",
                    "form",
                    "svg",
                ]
            ):
                element.decompose()

            main = (
                soup.find("main")
                or soup.find("article")
                or soup.find(attrs={"role": "main"})
                or soup.body
                or soup
            )

            content = main.get_text(separator=" ", strip=True)
            extraction_method = "beautifulsoup"

        # Normalize whitespace and enforce word limit.
        content = " ".join(content.split())
        original_word_count = len(content.split())

        if original_word_count < MIN_CONTENT_WORDS:
            return (
                "ERROR: Insufficient readable webpage content. "
                f"Extracted only {original_word_count} words. "
                f"URL: {final_url}"
            )

        limited_content = limit_words(content, MAX_WORDS)
        final_word_count = len(limited_content.split())

        return (
            "STATUS: success\n"
            f"TITLE: {title}\n"
            f"URL: {final_url}\n"
            f"EXTRACTION_METHOD: {extraction_method}\n"
            f"WORDS_EXTRACTED: {final_word_count}\n"
            f"WORDS_AVAILABLE_BEFORE_LIMIT: {original_word_count}\n"
            f"WORD_LIMIT: {MAX_WORDS}\n"
            f"CONTENT:\n{limited_content}"
        )

    except ValueError as exc:
        return f"ERROR: {exc}"

    except requests.RequestException:
        logger.exception("Failed to scrape URL: %s", url)
        return f"ERROR: Could not download webpage: {url}"

    except Exception:
        logger.exception("Unexpected scraper failure: %s", url)
        return "ERROR: Unexpected webpage extraction failure."
