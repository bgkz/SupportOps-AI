from pathlib import Path

from qdrant_client import QdrantClient

client = QdrantClient(url="http://localhost:6333")

file_path = Path(__file__).resolve().parent / "knowledge" / "damaged_goods.md"
text = file_path.read_text(encoding="utf-8")

print(text)
