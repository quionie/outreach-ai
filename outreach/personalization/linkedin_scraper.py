"""LinkedIn public profile scraper for prospect personalization.

DISCLAIMER: This module scrapes publicly visible LinkedIn profile data.
LinkedIn's Terms of Service may restrict automated access to their platform.
This tool is provided for educational and personal use. Users are responsible
for ensuring their usage complies with applicable terms and laws.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


@dataclass
class ProspectProfile:
    """Parsed LinkedIn profile data."""

    name: str = ""
    headline: str = ""
    current_role: str = ""
    company: str = ""
    summary: str = ""
    recent_activity: list[str] = field(default_factory=list)
    raw_text: str = ""

    def to_personalization_string(self) -> str:
        """Format profile data as a string for use in prompts."""
        parts = []
        if self.headline:
            parts.append(f"Headline: {self.headline}")
        if self.current_role:
            parts.append(f"Role: {self.current_role}")
        if self.company:
            parts.append(f"Company: {self.company}")
        if self.summary:
            parts.append(f"About: {self.summary[:500]}")
        if self.recent_activity:
            parts.append("Recent activity:")
            for activity in self.recent_activity[:3]:
                parts.append(f"  - {activity[:200]}")
        return "\n".join(parts) if parts else "No LinkedIn data available."


def scrape_linkedin_profile(url: str) -> ProspectProfile:
    """Scrape a public LinkedIn profile for personalization data.

    Args:
        url: The LinkedIn profile URL.

    Returns:
        A ProspectProfile with whatever data could be extracted.
        Falls back gracefully if scraping fails.
    """
    profile = ProspectProfile()

    try:
        response = httpx.get(url, headers=HEADERS, follow_redirects=True, timeout=15.0)
        response.raise_for_status()
    except (httpx.HTTPError, httpx.TimeoutException) as e:
        logger.warning(f"Could not fetch LinkedIn profile: {e}")
        return profile

    try:
        soup = BeautifulSoup(response.text, "html.parser")
        profile.raw_text = soup.get_text(separator=" ", strip=True)[:2000]

        # Try to extract structured data from meta tags (works on public profiles)
        title_tag = soup.find("title")
        if title_tag and title_tag.string:
            title = title_tag.string.strip()
            # LinkedIn titles typically follow: "Name - Role - Company | LinkedIn"
            if " | LinkedIn" in title:
                title = title.replace(" | LinkedIn", "")
            parts = [p.strip() for p in title.split(" - ")]
            if len(parts) >= 1:
                profile.name = parts[0]
            if len(parts) >= 2:
                profile.current_role = parts[1]
            if len(parts) >= 3:
                profile.company = parts[2]

        # Meta description often has the summary
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            profile.summary = str(meta_desc["content"])[:500]

        # og:title for headline
        og_title = soup.find("meta", attrs={"property": "og:title"})
        if og_title and og_title.get("content"):
            profile.headline = str(og_title["content"])

    except Exception as e:
        logger.warning(f"Error parsing LinkedIn profile: {e}")

    return profile
