from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        # Lưu reference đến store và llm_fn
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        """
        Trả lời câu hỏi bằng cách:
        1. Truy xuất top_k chunks liên quan từ store.
        2. Xây dựng prompt với chunks làm context.
        3. Gọi llm_fn để sinh câu trả lời.
        """
        # Bước 1: Truy xuất các chunk liên quan
        retrieved = self.store.search(question, top_k=top_k)

        # Bước 2: Xây dựng context từ các chunk truy xuất được
        context_parts = []
        for i, result in enumerate(retrieved, 1):
            context_parts.append(f"[Chunk {i}]: {result['content']}")

        context = "\n\n".join(context_parts) if context_parts else "Không có thông tin liên quan."

        # Bước 3: Xây dựng prompt RAG
        prompt = (
            f"Dưới đây là các đoạn văn bản liên quan được truy xuất từ cơ sở tri thức:\n\n"
            f"{context}\n\n"
            f"Dựa vào các thông tin trên, hãy trả lời câu hỏi sau:\n"
            f"Câu hỏi: {question}\n"
            f"Câu trả lời:"
        )

        # Bước 4: Gọi LLM để sinh câu trả lời
        return self.llm_fn(prompt)
