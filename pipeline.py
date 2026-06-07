"""
PS5 Game Discovery Guide — Document Pipeline (Milestone 3)

Big picture: this file turns 10 game-list documents into small, searchable
"chunks". It does three jobs in order:

  1. LOAD  -> read all 10 .md files from disk into memory.
  2. CLEAN -> remove the repeated header junk, keep only the game content.
  3. CHUNK -> cut each document into small pieces (about one game each).

Run this file directly to test it and print stats:
    .venv/Scripts/python.exe pipeline.py
"""

import re                       # regex tools, used to find/replace text patterns
import sys                      # lets us fix how text prints in the terminal
from pathlib import Path        # a clean way to work with file/folder paths

# Build the path to the "documents" folder that sits next to this file.
# Path(__file__) = this script's location; .parent = the folder it lives in.
DOCUMENTS_DIR = Path(__file__).parent / "documents"


def load_documents(documents_dir: Path = DOCUMENTS_DIR) -> list[dict]:
    """JOB 1 — Load every .md file in the documents folder into memory.

    Returns a list where each item is one document, stored as:
        {"source": "<filename>", "text": "<the whole file's text>"}
    We keep the filename so later we can say which file a chunk came from.
    """
    documents = []                                      # start with an empty list to fill
    for path in sorted(documents_dir.glob("*.md")):     # find every .md file, in name order
        text = path.read_text(encoding="utf-8")         # read the file's full text (utf-8 = handles — and " correctly)
        documents.append({"source": path.name, "text": text})  # save filename + text together
    return documents                                    # hand back the list of all documents


def clean_document(text: str) -> str:
    """JOB 2 — Remove the repeated header block and tidy the text.

    Every file starts with the same kind of header that is NOT game content:
        # Title
        Source: https://...
        Type: ...
        Domain: PS5 Game Discovery Guide
        Note: ...        (sometimes)
        ---
        <the actual game entries start here>
    We delete everything up to and including that first "---" line.
    """
    # Delete the header: ^ = start of text, .*? = any characters (as few as
    # possible), up to the first line that is exactly "---". DOTALL lets "."
    # also match newlines, so it can span the whole multi-line header.
    text = re.sub(r"^.*?\n---\n", "", text, count=1, flags=re.DOTALL)

    # Remove any "## ... FAQ" section (the heading and everything until the next
    # "##" heading or the end of the document). Discovered in Milestone 4: these
    # FAQ blocks are written as questions ("What is the best game on PS5?"), so
    # they matched the *structure* of our queries and outranked real game entries.
    text = re.sub(r"\n#{2,}[^\n]*FAQ.*?(?=\n## |\Z)", "",
                  text, flags=re.DOTALL | re.IGNORECASE)

    # Just-in-case cleanup: if any leftover HTML codes ever appear, turn them
    # back into normal characters (e.g. "&amp;" should read as "&").
    text = (
        text.replace("&amp;", "&")
        .replace("&nbsp;", " ")
        .replace("&#39;", "'")
        .replace("&quot;", '"')
    )

    # Squash 3-or-more blank lines into a single blank line, then strip any
    # extra spaces/newlines off the very start and end.
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text                                         # hand back the cleaned text


# --- Chunking settings (see planning.md, Chunking Strategy section) ---------
# Strategy: ONE GAME PER CHUNK. Each game entry is already its own paragraph
# (blank-line separated), so we make each entry its own chunk and do NOT pack
# several together. We learned this in Milestone 4: packing multiple games into
# one chunk blurred their embeddings (e.g. Helldivers 2's "co-op shooter" signal
# was averaged away among 11 other games and ranked #26). One game per chunk
# gives each game a sharp, undiluted embedding so specific queries match it.
MIN_CHUNK_LEN = 120      # skip tiny scraps (e.g. an orphan section heading alone)


def chunk_text(text: str, min_chunk_len: int = MIN_CHUNK_LEN) -> list[str]:
    """JOB 3 — Cut one cleaned document into chunks of one game entry each.

    Each game entry is its own paragraph (separated by a blank line), so we
    simply treat every paragraph as one chunk. Two small tidy-ups:
      - An orphan section heading on its own (e.g. "## Unmissable Games" with
        no description) is attached to the next entry instead of becoming a
        meaningless tiny chunk.
      - Anything still shorter than min_chunk_len characters is dropped.
    """
    # Split on blank lines into paragraphs (= game entries), dropping empties.
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    chunks: list[str] = []
    pending_heading = ""        # holds an orphan "## Heading" line to attach next

    for para in paragraphs:
        # Is this paragraph ONLY a markdown heading (one line starting with #)?
        # If so, hold it and prepend it to the next real entry for context.
        if para.startswith("#") and "\n" not in para:
            pending_heading = para
            continue

        # Attach any held heading to the front of this entry, then reset it.
        if pending_heading:
            para = f"{pending_heading}\n{para}"
            pending_heading = ""

        chunks.append(para)     # one game entry = one chunk

    # If a heading was left dangling at the very end, keep it rather than lose it.
    if pending_heading:
        chunks.append(pending_heading)

    # Drop any chunk too short to carry real meaning.
    return [c for c in chunks if len(c) >= min_chunk_len]


def build_chunks(documents_dir: Path = DOCUMENTS_DIR) -> list[dict]:
    """Run all three jobs over every document and collect the results.

    Returns one flat list of every chunk from every file, each labeled so we
    can trace it back to its source:
        {"source": "<filename>", "chunk_index": <number>, "text": "<chunk>"}
    """
    all_chunks: list[dict] = []                         # collect every chunk here
    for doc in load_documents(documents_dir):           # JOB 1: for each loaded document
        cleaned = clean_document(doc["text"])           # JOB 2: clean its text
        for i, chunk in enumerate(chunk_text(cleaned)): # JOB 3: chunk it (i = chunk's position)
            all_chunks.append(                          # store the chunk with its labels
                {"source": doc["source"], "chunk_index": i, "text": chunk}
            )
    return all_chunks                                   # hand back chunks from all 10 files


# --- Test run: only happens when you run "python pipeline.py" directly -------
if __name__ == "__main__":
    # Force the terminal to print special characters (— and ") correctly on Windows.
    sys.stdout.reconfigure(encoding="utf-8")

    chunks = build_chunks()                             # build every chunk
    lengths = [len(c["text"]) for c in chunks]          # list of each chunk's character count

    # Print the headline stats.
    print(f"Total chunks across all documents: {len(chunks)}")
    print(f"Chunk length — min {min(lengths)}, "       # smallest chunk
          f"avg {sum(lengths) // len(lengths)}, "       # average chunk size
          f"max {max(lengths)} chars\n")                # biggest chunk

    # Count how many chunks each document produced.
    print("Chunks per document:")
    per_doc: dict[str, int] = {}                        # filename -> count
    for c in chunks:                                    # tally one per chunk
        per_doc[c["source"]] = per_doc.get(c["source"], 0) + 1
    for source, count in per_doc.items():               # print the tally, lined up
        print(f"  {source:<55} {count:>3}")

    # Print 5 spread-out chunks so we can read them and confirm each one makes
    # sense on its own (the milestone's required inspection step).
    print("\n" + "=" * 70)
    print("5 REPRESENTATIVE CHUNKS")
    print("=" * 70)
    step = max(1, len(chunks) // 5)                     # jump size to spread picks across the list
    for c in chunks[::step][:5]:                        # take every `step`-th chunk, first 5
        print(f"\n--- {c['source']} #{c['chunk_index']} ({len(c['text'])} chars) ---")
        print(c["text"])
