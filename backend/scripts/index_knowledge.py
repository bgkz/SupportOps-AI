import re
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer

from backend.config import QDRANT_CLIENT_URL, QDRANT_COLLECTION_NAME


def chunk_text(text: str) -> list[str]:
    sections = re.split(r"(?m)(?=^#{1,6}\s+)", text)

    return [section.strip() for section in sections if section.strip()]


def main() -> None:
    knowledge_dir = Path(__file__).resolve().parents[1] / "knowledge"

    model = SentenceTransformer(
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )

    client = QdrantClient(url=QDRANT_CLIENT_URL)
    collection_name = QDRANT_COLLECTION_NAME

    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=384,
                distance=models.Distance.COSINE,
            ),
        )

    for file_path in knowledge_dir.glob("*.md"):
        text = file_path.read_text(encoding="utf-8")
        chunks = chunk_text(text)
        relative_path = file_path.relative_to(knowledge_dir).as_posix()

        points = []

        for chunk_index, chunk in enumerate(chunks):
            vector = model.encode(chunk).tolist()

            point_id = str(
                uuid5(
                    NAMESPACE_URL,
                    f"supportops/knowledge/{relative_path}/chunk/{chunk_index}",
                )
            )

            points.append(
                models.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "text": chunk,
                        "source": relative_path,
                        "document_id": file_path.stem,
                        "chunk_index": chunk_index,
                    },
                )
            )

        if points:
            client.upsert(
                collection_name=collection_name,
                points=points,
                wait=True,
            )

    client.close()


if __name__ == "__main__":
    main()
