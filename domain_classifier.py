"""
RAGEWARE — Domain classifier.
Two plain lists: PRODUCTIVE and DISTRACTING. Edit live if classification
embarrasses you mid-demo.
"""

PRODUCTIVE_DOMAINS = {
    "github.com",
    "gitlab.com",
    "bitbucket.org",
    "stackoverflow.com",
    "docs.python.org",
    "developer.mozilla.org",
    "learn.microsoft.com",
    "devdocs.io",
    "arxiv.org",
    "scholar.google.com",
    "readthedocs.io",
    "pypi.org",
    "npmjs.com",
    "docs.rs",
    "man7.org",
    "cppreference.com",
    "coursera.org",
    "edx.org",
    "khanacademy.org",
    "leetcode.com",
    "hackerrank.com",
    "codeforces.com",
    "kaggle.com",
    "notion.so",
    "linear.app",
    "jira.atlassian.com",
    "confluence.atlassian.com",
}

DISTRACTING_DOMAINS = {
    "youtube.com",
    "reddit.com",
    "twitter.com",
    "x.com",
    "facebook.com",
    "instagram.com",
    "tiktok.com",
    "twitch.tv",
    "netflix.com",
    "hulu.com",
    "disneyplus.com",
    "primevideo.com",
    "9gag.com",
    "imgur.com",
    "buzzfeed.com",
    "tumblr.com",
    "pinterest.com",
    "snapchat.com",
    "discord.com",
    "telegram.org",
    "whatsapp.com",
    "tinder.com",
    "amazon.com",
    "ebay.com",
    "aliexpress.com",
    "wish.com",
    "espn.com",
    "sports.yahoo.com",
}


def classify(domain: str) -> str:
    """
    Classify a domain as 'productive', 'distracting', or 'neutral'.
    Matches against base domain (strips subdomains by checking if
    the domain ends with a known entry).
    """
    if not domain:
        return "neutral"

    domain = domain.lower().strip()

    # Strip www. prefix
    if domain.startswith("www."):
        domain = domain[4:]

    for d in DISTRACTING_DOMAINS:
        if domain == d or domain.endswith("." + d):
            return "distracting"

    for d in PRODUCTIVE_DOMAINS:
        if domain == d or domain.endswith("." + d):
            return "productive"

    return "neutral"
