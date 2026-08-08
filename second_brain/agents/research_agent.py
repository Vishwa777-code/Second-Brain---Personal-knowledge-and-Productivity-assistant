"""Module 3 — Research Agent"""
from langchain_community.tools import DuckDuckGoSearchRun, WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from core.llm import llm, get_text_content

_web_search = DuckDuckGoSearchRun()
_wiki_search = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())


def research(query: str) -> str:
    """Combine live web search and Wikipedia background knowledge into one answer."""
    try:
        web_result = _web_search.run(query)
    except Exception as e:
        web_result = f"(web search unavailable: {e})"
    try:
        wiki_result = _wiki_search.run(query)
    except Exception as e:
        wiki_result = f"(wikipedia unavailable: {e})"

    prompt = f"""Summarize this into one clear, well-organized answer for the user.
Web results: {web_result}
Wikipedia: {wiki_result}
Question: {query}"""
    return get_text_content(llm.invoke(prompt))
