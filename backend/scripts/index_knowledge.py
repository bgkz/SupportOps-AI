from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer


def main() -> None:
    knowledge_dir = Path(__file__).resolve().parents[1] / "knowledge"

    model = SentenceTransformer(
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )

    client = QdrantClient(url="http://localhost:6333")
    collection_name = "support_knowledge"

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
        vector = model.encode(text).tolist()

        # Gleicher relativer Dateipfad ergibt immer dieselbe ID
        relative_path = file_path.relative_to(knowledge_dir).as_posix()
        point_id = str(uuid5(NAMESPACE_URL, f"supportops/knowledge/{relative_path}"))

        client.upsert(
            collection_name=collection_name,
            points=[
                models.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "text": text,
                        "source": relative_path,
                        "document_id": file_path.stem,
                    },
                )
            ],
            wait=True,
        )

        print(f"Indexiert: {relative_path}")

    client.close()


if __name__ == "__main__":
    main()
