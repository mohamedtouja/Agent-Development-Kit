import os
import json
import smtplib
import urllib.request
import urllib.error
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
try:
    from google.adk.agents import Agent
    from google.genai import types
except ImportError:
    class Agent:
        def __init__(self, *args, **kwargs): pass
    class types:
        class GenerateContentConfig:
            def __init__(self, **kwargs): pass
        class HttpOptions:
            def __init__(self, **kwargs): pass
        class HttpRetryOptions:
            def __init__(self, **kwargs): pass

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DEV_API_KEY = os.getenv("DEV_API_KEY")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")


import requests

def get_rising_articles(tag: str, limit: int = 5) -> str:
    """
    Fetches the top rising articles for a given tag using the Dev.to (Forem) API.
    Returns a formatted string of the articles with their ID, title, description, and URL.
    """
    url = f"https://dev.to/api/articles?tag={tag}&state=rising&per_page={limit}"
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        articles = response.json()
        
        if not articles:
            return f"No rising articles found for tag '{tag}'."

        result = f"Top {len(articles)} rising articles for '{tag}':\n\n"
        for i, article in enumerate(articles, 1):
            result += f"{i}. {article.get('title')} (ID: {article.get('id')})\n"
            result += f"   URL: {article.get('url')}\n"
            result += f"   Description: {article.get('description')}\n\n"
        
        return result
    except requests.exceptions.RequestException as e:
        return f"Error fetching articles from Dev.to API: {e}"


def save_to_reading_list(article_id: int) -> str:
    """
    Saves an article to the user's DEV.to reading list using the DEV API via reactions.
    """
    return "Error: The Forem (DEV.to) public API no longer supports programmatically adding articles to your reading list. Please add them manually on the website."


def fetch_comments(article_id: int) -> str:
    """
    Fetches the top comments for a specific DEV.to article by ID to gauge community sentiment.
    """
    url = f"https://dev.to/api/comments?a_id={article_id}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        comments = response.json()
        
        if not comments:
            return "No comments found on this article."
            
        summary_blocks = []
        # Get up to top 5 top-level comments
        for i, c in enumerate(comments[:5]):
            user = c.get('user', {}).get('name', 'Anonymous')
            body = c.get('body_html', '').replace('<p>', '').replace('</p>', '').strip()
            if not body:
                body = c.get('body_markdown', '')[:200]
            summary_blocks.append(f"Comment {i+1} by {user}: {body}")
            
        return "Top Comments:\n" + "\n".join(summary_blocks)
    except Exception as e:
        return f"Error fetching comments: {e}"

def create_article_draft(title: str, body_markdown: str, tags: list[str]) -> str:
    """
    Creates a new, unpublished article Draft on the user's DEV.to account.
    """
    if not DEV_API_KEY:
        return "Error: DEV_API_KEY is not configured in the environment."
        
    url = "https://dev.to/api/articles"
    headers = {
        "api-key": DEV_API_KEY,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    }
    payload = {
        "article": {
            "title": title,
            "published": False,
            "body_markdown": body_markdown,
            "tags": tags[:4]
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code in [200, 201]:
            data = response.json()
            article_url = data.get('url', 'Unknown URL')
            return f"Successfully created draft! You can review it at: {article_url}"
        else:
            return f"Failed to create draft. Status Code: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Error creating draft: {e}"


agent_instruction = """
You are a Trend-Spotting Research Agent.
Every morning, or when requested, you monitor specific tags on DEV (Forem) to find the most interesting emerging technologies or topics.

Your workflow:
1. Use the 'get_rising_articles' tool to fetch the top rising articles for a user's specified tag (e.g., 'machinelearning').
2. Use the 'fetch_comments' tool on the most popular articles to evaluate the community's sentiment and see what developers are actually saying.
3. Synthesize the articles and the sentiment into an insightful and concise trend report.
4. Use the 'create_article_draft' tool to automatically generate an unpublished DEV.to article (A "Trend Digest") on the user's account for them to review, containing your full synthesized report.
"""

root_agent = Agent(
    model="gemini-2.0-flash",
    name="trend_spotting_agent",
    description="An agent that spots rising trends/articles on DEV community and automatically drafts trend digest articles.",
    instruction=agent_instruction,
    tools=[get_rising_articles, fetch_comments, create_article_draft],
    generate_content_config=types.GenerateContentConfig(
        http_options=types.HttpOptions(
            retry_options=types.HttpRetryOptions(initial_delay=10, attempts=3)
        )
    )
)
