"""
generator.py — Answer generation and streaming service.

Second step in the query pipeline. Takes retrieved chunks and a student
query, constructs a grounded prompt, and streams the answer from GPT-4o.

Key responsibilities:
  1. Select the correct system prompt for the active study mode —
     each mode shapes GPT-4o's behaviour differently
  2. Format retrieved chunks with source labels so GPT-4o can cite them
  3. Inject conversation history for multi-turn coherence
  4. Stream tokens back to the caller as they arrive from OpenAI

Why async?
  FastAPI is an async framework. A synchronous OpenAI call would block
  the event loop for the entire duration of generation — meaning no other
  request could be served while one student is waiting for an answer.
  The async client cooperates with FastAPI's event loop.

Why streaming?
  Without streaming, the student sees a blank screen for 3–8 seconds
  then the full answer appears at once. With streaming, tokens appear
  as GPT-4o generates them — the response feels instant.
"""

from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

# AsyncOpenAI reads OPENAI_API_KEY from environment automatically
async_client = AsyncOpenAI()

GENERATION_MODEL = "gpt-4o"


# ── System prompts ─────────────────────────────────────────────────────────
#
# Each mode gets a distinct system prompt that controls tone, structure,
# and behaviour. The shared constraint across all five: answer only from
# the provided excerpts. Never from training data or the internet.

SYSTEM_PROMPTS = {
    "free": """You are a study assistant for the Data Analytics and Visualisation \
(DAV) unit at Strathmore University, MSc Information Technology programme.

Answer ONLY using the course material excerpts provided below. \
Do not use your training knowledge, the internet, or any external source. \
If the excerpts do not contain enough information to answer the question, \
say so clearly and honestly — never guess or infer beyond what is written.

For every point you make, cite the source in brackets: (Filename, Page N).
Be clear, well-structured, and helpful. Use bullet points or headers where \
they improve readability.""",

    "revision": """You are a revision tutor for the Data Analytics and Visualisation \
(DAV) unit at Strathmore University, MSc IT programme.

Help the student prepare for their exam using ONLY the provided course material excerpts. \
Explain concepts clearly with examples from the materials where available. \
After explaining a concept, pose one short follow-up question to check understanding. \
Always cite sources: (Filename, Page N).""",

    "deepdive": """You are an in-depth tutor for the Data Analytics and Visualisation \
(DAV) unit at Strathmore University, MSc IT programme.

Cover the requested topic completely using ONLY the provided course material excerpts. \
Structure: definition → key concepts → how it works → examples → limitations/caveats. \
Use clear section headers. If the materials only partially cover the topic, \
state explicitly what is covered and what is not. Cite all sources: (Filename, Page N).""",

    "practice": """You are an exam evaluator for the Data Analytics and Visualisation \
(DAV) unit at Strathmore University, MSc IT programme.

The student has submitted an answer to a practice question. \
Evaluate it using ONLY the provided course material excerpts as the answer key. \
State what they got right, what they missed, and what was incorrect. \
Provide the correct answer sourced directly from the materials. \
Be specific — point to the exact concept they need to revisit. \
Cite sources: (Filename, Page N).""",

    "lookup": """You are a quick-reference tool for the Data Analytics and Visualisation \
(DAV) unit at Strathmore University, MSc IT programme.

The student wants a concise definition of a term or concept. \
Using ONLY the provided course material excerpts, return a precise 2–4 sentence definition. \
End with the exact citation: (Filename, Page N). \
Do not elaborate beyond what is asked. Be brief and accurate.""",
}

DEFAULT_PROMPT = SYSTEM_PROMPTS["free"]


def build_context_block(chunks: list[dict]) -> str:
    """
    Format retrieved chunks into a labelled context block for the prompt.

    Each chunk is wrapped with a source header so GPT-4o knows exactly
    where the content came from and can reproduce that citation in the answer.

    Example output:
        [Source 1: Intro to Data Analytics, Page 4]
        K-means is an unsupervised learning algorithm...

        ---

        [Source 2: Intro to Data Analytics, Page 7]
        Choosing the value of K is done using the elbow method...
    """
    parts = []
    for i, chunk in enumerate(chunks, 1):
        header = f"[Source {i}: {chunk['filename']}, Page {chunk['page_number']}]"
        parts.append(f"{header}\n{chunk['content']}")
    return "\n\n---\n\n".join(parts)


def build_messages(
    query: str,
    chunks: list[dict],
    mode: str,
    history: list[dict],
) -> list[dict]:
    """
    Construct the full messages array for the GPT-4o API call.

    Message structure (in order):
        1. System message — behaviour rules + retrieved context
           The context is injected here so it is always present and
           clearly separate from the conversation.

        2. History — previous turns in this session
           Enables follow-up questions. Without this, "explain that more"
           has no referent — the model has no memory of what "that" was.

        3. Current user message — the student's question this turn

    Args:
        query:   The student's current question
        chunks:  Retrieved chunks from pgvector (already ranked by relevance)
        mode:    Study mode key — selects the system prompt
        history: Previous messages [{role, content}, ...]
    """
    system_prompt = SYSTEM_PROMPTS.get(mode, DEFAULT_PROMPT)
    context_block = build_context_block(chunks)

    # The system message combines the behaviour instructions and the
    # retrieved context. The separator makes it clear where instructions
    # end and course content begins.
    full_system = (
        f"{system_prompt}\n\n"
        f"COURSE MATERIAL EXCERPTS:\n"
        f"{'=' * 40}\n"
        f"{context_block}\n"
        f"{'=' * 40}\n"
        f"Answer the student's question using only the excerpts above."
    )

    messages = [{"role": "system", "content": full_system}]

    # Conversation history from Redis (last N exchanges)
    messages.extend(history)

    # Current question
    messages.append({"role": "user", "content": query})

    return messages


async def stream_answer(
    query: str,
    chunks: list[dict],
    mode: str,
    history: list[dict],
):
    """
    Async generator that streams GPT-4o's answer one token at a time.

    The caller (the chat route) iterates over this generator and
    forwards each token to the HTTP response as an SSE event.

    temperature=0.3 makes GPT-4o more precise and deterministic —
    appropriate for a factual study tool. Higher values introduce
    more variation and creativity, which we don't want here.

    Yields:
        Individual token strings as GPT-4o produces them.
    """
    messages = build_messages(query, chunks, mode, history)

    stream = await async_client.chat.completions.create(
        model=GENERATION_MODEL,
        messages=messages,
        stream=True,
        temperature=0.3,
    )

    async for chunk in stream:
        # delta.content is None on the first chunk (role marker)
        # and on the last chunk (finish_reason marker). Skip those.
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta