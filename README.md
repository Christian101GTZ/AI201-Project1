# The Unofficial Guide — Project 1

## Domain

My system covers PS5 game discovery and recommendation. The goal is to help users find games based on genres, play styles, and preferences such as co-op shooters, RPGs, platformers, horror games, indie games, multiplayer games, and open-world games.

This knowledge is valuable because information about PS5 games is spread across many different websites. A player often has to search multiple sources such as IGN, Polygon, OpenCritic, Metacritic, PlayStation's official catalog, and genre-specific recommendation lists to find games that match their interests.

Official store pages provide descriptions and screenshots but do not aggregate critic opinions, rankings, genre recommendations, or comparisons across multiple sources. My system combines these sources into a single retrieval-augmented generation (RAG) application that answers questions using collected documents.

---

## Document Sources

| #  | Source                                          | Type                     | URL or file path                                           |
| -- | ----------------------------------------------- | ------------------------ | ---------------------------------------------------------- |
| 1  | Digital Trends — Best PS5 Indie Games           | Editorial Ranking        | https://www.digitaltrends.com/gaming/best-ps5-indie-games/ |
| 2  | Eneba — Best PS5 Horror Games                   | Genre Guide              | https://www.eneba.com/hub/games/best-ps5-horror-games/     |
| 3  | Eneba — Best PS5 RPGs                           | Genre Guide              | https://www.eneba.com/hub/games/best-ps5-rpgs/             |
| 4  | IGN — Best PS5 Games                            | Editorial Ranking        | https://www.ign.com/articles/best-ps5-games                |
| 5  | Metacritic — Best PS5 Games                     | Critic Aggregate Ranking | https://www.metacritic.com                                 |
| 6  | OpenCritic — Best PS5 Games                     | Critic Aggregate Ranking | https://opencritic.com                                     |
| 7  | PlayStation PS5 Catalog                         | Official Catalog         | https://www.playstation.com                                |
| 8  | Polygon — Best PS5 Games                        | Editorial Ranking        | https://www.polygon.com                                    |
| 9  | Push Square — Best PS5 Online Multiplayer Games | Genre Guide              | https://www.pushsquare.com                                 |
| 10 | TrueTrophies — Best PS5 Open World Games        | Genre Guide              | https://www.truetrophies.com                               |

---

## Chunking Strategy

**Chunk size:** One game entry per chunk, typically ranging from approximately 120–540 characters.

**Overlap:** No overlap was used.

**Why these choices fit your documents:**

The original plan was to use paragraph-based chunking around 500–600 characters. During Milestone 4 retrieval testing, I discovered that chunks containing multiple games reduced retrieval quality because the embedding represented several games at once.

For example, a co-op shooter query could retrieve a chunk that also contained unrelated games. To improve retrieval performance, I changed the strategy to one game per chunk. Each game's description became its own chunk, allowing the embedding model to represent that game more accurately.

Before chunking, I removed document headers, source metadata, FAQ sections, and cleaned formatting artifacts. I also normalized spacing and removed unnecessary boilerplate text.

**Final chunk count:** 212 chunks across 10 source documents.

---

## Embedding Model

**Model used:**

all-MiniLM-L6-v2 from Sentence Transformers.

**Production tradeoff reflection:**

I selected all-MiniLM-L6-v2 because it runs locally, requires no API key, is lightweight, and performs well on semantic retrieval tasks. It was a practical choice for a class project because it is fast and easy to deploy.

For a production system, I would evaluate larger embedding models that provide stronger semantic understanding and improved retrieval accuracy. Factors I would consider include multilingual support, latency, hosting costs, domain-specific performance, and context length limitations. A larger model would likely improve retrieval quality but increase computational costs and response times.

---

## Grounded Generation

**System prompt grounding instruction:**

The system prompt explicitly instructs the language model to answer only from retrieved documents. The model is told:

* Do not use outside knowledge.
* Do not guess.
* If the documents do not contain enough information, respond with: "I don't have enough information on that."
* Every recommendation must reference the retrieved sources.

Retrieved chunks are inserted directly into the prompt and provided as the only context available to the model.

**How source attribution is surfaced in the response:**

Each retrieved chunk contains source metadata. The application programmatically collects source filenames and displays them separately from the generated answer. This guarantees attribution even if the language model forgets to mention a source in its generated response.

---

## Evaluation Report

| # | Question                                              | Expected answer                      | System response (summarized)                                                           | Retrieval quality | Response accuracy  |
| - | ----------------------------------------------------- | ------------------------------------ | -------------------------------------------------------------------------------------- | ----------------- | ------------------ |
| 1 | What is a good co-op shooter to play on PS5?          | Helldivers 2 or Borderlands 3        | Recommended Helldivers 2 and Borderlands 3 with supporting source citations.           | Relevant          | Accurate           |
| 2 | What's a recommended story-driven action game on PS5? | God of War Ragnarök or Stellar Blade | Recommended The Last of Us Part I and God of War Ragnarök using retrieved IGN content. | Relevant          | Partially Accurate |
| 3 | I want a fun platformer on PS5 — what should I play?  | Astro Bot                            | Recommended Astro Bot and cited multiple sources.                                      | Relevant          | Accurate           |
| 4 | What PS5 game is best for racing fans?                | Gran Turismo 7                       | Recommended Forza Horizon 5 based on retrieved source content.                         | Relevant          | Partially Accurate |
| 5 | Which indie game on PS5 has the highest critic score? | Disco Elysium: The Final Cut (95%)   | Correctly identified Disco Elysium: The Final Cut as the highest-rated indie game.     | Relevant          | Accurate           |

**Retrieval quality:** Relevant / Partially relevant / Off-target

**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

**Question that failed:**

What PS5 game is best for racing fans?

**What the system returned:**

The system recommended Forza Horizon 5 instead of Gran Turismo 7.

**Root cause (tied to a specific pipeline stage):**

This was not a retrieval failure. The retrieval system successfully returned racing-game chunks. However, the corpus contained multiple valid recommendations from different sources. Polygon strongly favored Forza Horizon 5 while other sources highlighted Gran Turismo 7. The language model generated an answer based on the retrieved context rather than the expected answer.

**What you would change to fix it:**

I would aggregate critic scores and rankings across multiple sources and add score-based reranking. This would allow the system to weigh consensus recommendations rather than relying solely on semantic similarity.

---

## Spec Reflection

**One way the spec helped you during implementation:**

The planning document forced me to think about chunking, retrieval, evaluation questions, and system architecture before writing code. This made development more structured and helped me identify retrieval issues earlier because I already knew how the system was supposed to behave.

The evaluation plan was especially useful because it gave me concrete questions to test throughout development. Those tests helped reveal weaknesses in chunking and retrieval quality.

**One way your implementation diverged from the spec, and why:**

My original plan called for paragraph-based chunks of approximately 500–600 characters. During retrieval testing, I discovered that chunks containing multiple games reduced retrieval quality because important game-specific information became diluted.

I changed the implementation to one-game-per-chunk chunking. This diverged from the original plan but produced significantly better retrieval results for recommendation queries.

---

## AI Usage

### Instance 1

* **What I gave the AI:** My planning.md chunking strategy, document structure, and Milestone 3 requirements.
* **What it produced:** An initial chunking pipeline that loaded documents, cleaned text, and created chunks.
* **What I changed or overrode:** During retrieval testing I discovered that multi-game chunks reduced retrieval quality. I modified the chunking strategy to use one game per chunk and updated the cleaning logic to remove FAQ sections and metadata.

### Instance 2

* **What I gave the AI:** My retrieval architecture, embedding model choice, ChromaDB requirements, and Milestone 4 instructions.
* **What it produced:** Embedding and retrieval code using all-MiniLM-L6-v2 and ChromaDB.
* **What I changed or overrode:** I added source-aware retrieval improvements, custom source tags, reranking logic, grounding instructions, and stronger source attribution to improve retrieval quality and reduce hallucinations during generation.

## Demo Video

This video demonstrates the complete PS5 Game Discovery Guide RAG system, including:

- Document ingestion and preprocessing
- One-game-per-chunk chunking strategy
- Embedding generation using all-MiniLM-L6-v2
- ChromaDB vector storage and retrieval
- Grounded generation using Groq's Llama 3.3 70B model
- Source attribution
- Gradio user interface
- Evaluation results
- Failure case analysis

Demo Video:

https://www.loom.com/share/bb56bae3ee424c14a9634c415800b026