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


SOURCE_LABELS = {
    "digitaltrends_best_ps5_indie_games.md": "Digital Trends — Best PS5 Indie Games",
    "eneba_best_ps5_horror_games.md": "Eneba — Best PS5 Horror Games",
    "eneba_best_ps5_rpgs.md": "Eneba — Best PS5 RPGs",
    "ign_best_ps5_games.md": "IGN — Best PS5 Games",
    "metacritic_best_ps5_games.md": "Metacritic — Best PS5 Games",
    "opencritic_best_ps5_games.md": "OpenCritic — Best PS5 Games",
    "playstation_ps5_catalog.md": "PlayStation — Official PS5 Catalog",
    "polygon_best_ps5_games.md": "Polygon — Best PS5 Games",
    "pushsquare_best_ps5_online_multiplayer_games.md": "Push Square — Best PS5 Online Multiplayer Games",
    "truetrophies_best_ps5_open_world_games.md": "TrueTrophies — Best PS5 Open-World Games",
}


def ask(question: str) -> dict:
    """
    Retrieve relevant chunks and generate a grounded answer.
    """

    hits = retrieve(question, k=5)

    context_parts = []
    sources = []

    for hit in hits:
        clean_source = SOURCE_LABELS.get(hit["source"], hit["source"])

        context_parts.append(
            f"[SOURCE: {clean_source}]\n{hit['text']}"
        )

        sources.append(clean_source)

    context = "\n\n".join(context_parts)

    system_prompt = """
You are a PS5 Game Discovery Guide assistant.

Answer ONLY using the information provided in the retrieved documents.

Rules:
1. Do not use outside knowledge.
2. Do not guess.
3. If the documents do not contain enough information, reply exactly:
   "I don't have enough information on that."
4. Every recommendation must mention the source name in the sentence.
5. Keep answers concise and factual.

Example format:
"Helldivers 2 is a good co-op shooter because Polygon — Best PS5 Games describes it as a co-op third-person shooter for a squad of pals. Source: Polygon — Best PS5 Games"
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