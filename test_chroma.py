import sys
import logging
logging.basicConfig(level=logging.INFO)
try:
    from pathlib import Path
    from showrunner_tool.repositories.chroma_indexer import ChromaIndexer
    chroma_dir = Path.cwd() / ".chroma"
    chroma_indexer = ChromaIndexer(persist_dir=chroma_dir)
    print("Success")
except Exception as e:
    import traceback
    traceback.print_exc()
