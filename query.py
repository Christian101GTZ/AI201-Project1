"""
query.py

End-to-end retrieval + grounded generation.
"""

import os
from dotenv import load_dotenv
from groq import Groq

from retrieval import retrieve

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

MODEL_NAME = "llama-3.3-70b-versatile"


def ask(question: str) -> dict:
    """
    Retrieve relevant chunks and generate a grounded answer.
    """

    hits = retrieve(question, k=5)

    context_parts = []
    sources = []

    for hit in hits:
        context_parts.append(
            f"[SOURCE: {hit['source']}]\n{hit['text']}"
        )
        sources.append(hit["source"])

    context = "\n\n".join(context_parts)

    system_prompt = """
You are a PS5 Game Discovery Guide assistant.

Answer ONLY using the information provided in the retrieved documents.

Rules:
1. Do not use outside knowledge.
2. Do not guess.
3. If the documents do not contain enough information, reply exactly:
   "I don't have enough information on that."
4. Every recommendation must mention the source filename in the sentence.
5. Keep answers concise and factual.

Example format:
"Helldivers 2 is a good co-op shooter because the retrieved Polygon source describes it as a co-op third-person shooter for a squad of pals. Source: polygon_best_ps5_games.md"
"""

    user_prompt = f"""
QUESTION:
{question}

RETRIEVED DOCUMENTS:
{context}
"""

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0,
    )

    answer = response.choices[0].message.content

    return {
        "answer": answer,
        "sources": sorted(set(sources))
    }


if __name__ == "__main__":
    result = ask(
        "What is a good co-op shooter to play on PS5?"
    )

    print("\nANSWER\n")
    print(result["answer"])

    print("\nSOURCES\n")
    for source in result["sources"]:
        print("-", source)