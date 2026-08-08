from langchain_google_genai import ChatGoogleGenerativeAI
from core.config import GOOGLE_API_KEY

llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite", google_api_key=GOOGLE_API_KEY)


def get_text_content(result) -> str:
    """Convert LangChain/Gemini response content into a plain string.

    Newer versions of langchain-google-genai return content as a list of
    dicts (e.g. [{'type': 'text', 'text': '...', 'extras': {...}}]) rather
    than a plain string.  This helper normalises both formats.
    """
    content = result.content

    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, dict):
                parts.append(part.get("text", ""))
            else:
                parts.append(str(part))
        content = "".join(parts)

    return str(content)
