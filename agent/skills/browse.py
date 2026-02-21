"""
Web browsing skill — fetch and summarize web page content.
"""

import re
import urllib.request
import urllib.error
from html.parser import HTMLParser

from agent.skills import Skill, SkillResult


class _TextExtractor(HTMLParser):
    """Simple HTML-to-text extractor."""

    def __init__(self):
        super().__init__()
        self._text_parts = []
        self._skip_tags = {"script", "style", "noscript", "svg", "head"}
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in self._skip_tags:
            self._skip_depth += 1

    def handle_endtag(self, tag):
        if tag in self._skip_tags and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data):
        if self._skip_depth == 0:
            text = data.strip()
            if text:
                self._text_parts.append(text)

    def get_text(self) -> str:
        return "\n".join(self._text_parts)


def _html_to_text(html: str) -> str:
    extractor = _TextExtractor()
    extractor.feed(html)
    return extractor.get_text()


class BrowseSkill(Skill):

    @property
    def name(self) -> str:
        return "web_browse"

    @property
    def description(self) -> str:
        return "Fetch a web page URL and return its text content (summarized)."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL to fetch and read.",
                },
                "max_chars": {
                    "type": "integer",
                    "description": "Maximum characters to return (default 3000).",
                },
            },
            "required": ["url"],
        }

    def execute(self, url: str, max_chars: int = 3000, **kwargs) -> SkillResult:
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; AgentBot/1.0)",
                "Accept": "text/html,application/xhtml+xml,*/*",
            })
            with urllib.request.urlopen(req, timeout=15) as resp:
                content_type = resp.headers.get("Content-Type", "")
                raw = resp.read()

                # Detect encoding
                encoding = "utf-8"
                if "charset=" in content_type:
                    encoding = content_type.split("charset=")[-1].split(";")[0].strip()

                html = raw.decode(encoding, errors="replace")

        except urllib.error.HTTPError as e:
            return SkillResult(
                success=False,
                output=f"HTTP error {e.code}: {e.reason}",
                error=str(e),
            )
        except urllib.error.URLError as e:
            return SkillResult(
                success=False,
                output=f"URL error: {e.reason}",
                error=str(e),
            )
        except Exception as e:
            return SkillResult(
                success=False,
                output=f"Failed to fetch URL: {e}",
                error=str(e),
            )

        # Extract text
        text = _html_to_text(html)

        # Clean up excessive whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" {2,}", " ", text)

        # Truncate
        if len(text) > max_chars:
            text = text[:max_chars] + "\n\n[... truncated]"

        return SkillResult(
            success=True,
            output=text,
            data={"url": url, "length": len(text)},
        )
