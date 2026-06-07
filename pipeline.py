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
# CHUNK_OVERLAP is 0 on purpose: our chunker keeps whole game entries together
# and never splits one, so repeating text between chunks wasn't needed and only
# pasted half-words onto the next chunk. (planning.md originally said 75-90.)
CHUNK_SIZE = 600        # the biggest a chunk should get, in characters
CHUNK_OVERLAP = 0       # how many characters to repeat between chunks (0 = none)


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE,
               overlap: int = CHUNK_OVERLAP) -> list[str]:
    """JOB 3 — Cut one cleaned document into small chunks (~one game each).

    Each game entry is its own paragraph (separated by a blank line). We add
    whole entries to a chunk until it would get bigger than `chunk_size`, then
    we start a new chunk. This keeps each game's name + description together.
    """
    # Split the text on blank lines into paragraphs (= game entries),
    # dropping any empty ones and trimming stray spaces.
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    chunks: list[str] = []      # finished chunks go here
    current = ""                # the chunk we are currently building up

    for para in paragraphs:     # go through the game entries one at a time
        # Edge case: if a single entry is somehow bigger than the whole chunk
        # size, give it its own chunk so we never lose it.
        if len(para) > chunk_size:
            if current:                 # if we were mid-chunk,
                chunks.append(current)  # save what we had so far
                current = ""            # and reset
            chunks.append(para)         # the oversized entry becomes its own chunk
            continue                    # move on to the next entry

        # Normal case: would adding this entry push the current chunk over the
        # size limit? (the "+ 2" accounts for the blank line we put between entries)
        if current and len(current) + 2 + len(para) > chunk_size:
            chunks.append(current)      # the current chunk is full -> save it
            # Optionally carry the last `overlap` characters into the next chunk.
            # The guard avoids a Python trap: current[-0:] would return the WHOLE
            # string, so when overlap is 0 we carry nothing.
            carry = current[-overlap:] if overlap > 0 else ""
            current = f"{carry}\n\n{para}" if carry else para  # start the new chunk
        else:
            # There's still room -> add this entry to the current chunk.
            # (If current is empty, just start it with this entry.)
            current = f"{current}\n\n{para}" if current else para

    if current:                 # after the loop, save the last partly-filled chunk
        chunks.append(current)

    return chunks               # hand back the list of chunks for this document


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
