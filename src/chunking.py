from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []

        # Tách câu bằng regex: nhận ra ". ", "! ", "? ", ".\n"
        # Giữ lại dấu cuối câu bằng cách dùng lookahead
        sentence_pattern = re.compile(r'(?<=[.!?])\s+|(?<=\.)\n')
        sentences = sentence_pattern.split(text.strip())

        # Lọc bỏ chuỗi rỗng sau khi split
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            return [text.strip()]

        chunks: list[str] = []
        for i in range(0, len(sentences), self.max_sentences_per_chunk):
            group = sentences[i : i + self.max_sentences_per_chunk]
            chunk_text = " ".join(group).strip()
            if chunk_text:
                chunks.append(chunk_text)

        return chunks if chunks else [text.strip()]


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        """Bắt đầu quá trình split đệ quy với danh sách separators đầy đủ."""
        if not text:
            return []

        # Nếu không có separator nào, trả về nguyên văn bản
        if not self.separators:
            # Fallback: chia theo chunk_size cố định nếu không có separator
            if len(text) <= self.chunk_size:
                return [text]
            # Chia theo ký tự
            chunks = []
            for i in range(0, len(text), self.chunk_size):
                c = text[i : i + self.chunk_size]
                if c:
                    chunks.append(c)
            return chunks

        return self._split(text, list(self.separators))

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        """
        Recursive helper:
        - Nếu text đủ ngắn (<= chunk_size), trả về [text].
        - Thử separator đầu tiên trong remaining_separators để split.
        - Nếu separator này không tạo ra kết quả hữu ích, thử separator tiếp theo.
        - Gộp các mảnh nhỏ lại nếu chúng còn đủ nhỏ để gộp.
        - Nếu mảnh vẫn còn quá lớn, đệ quy với separator tiếp theo.
        """
        # Base case: văn bản đủ ngắn
        if len(current_text) <= self.chunk_size:
            return [current_text] if current_text.strip() else []

        # Hết separator: trả về nguyên văn bản (buộc phải)
        if not remaining_separators:
            return [current_text]

        sep = remaining_separators[0]
        next_separators = remaining_separators[1:]

        # Nếu separator là chuỗi rỗng "" → chia từng ký tự (last resort)
        if sep == "":
            # Chia theo chunk_size ký tự
            chunks = []
            for i in range(0, len(current_text), self.chunk_size):
                c = current_text[i : i + self.chunk_size]
                if c:
                    chunks.append(c)
            return chunks

        # Tách text bằng separator hiện tại
        parts = current_text.split(sep)

        # Nếu separator không tìm thấy trong text (chỉ 1 phần), thử separator tiếp
        if len(parts) == 1:
            return self._split(current_text, next_separators)

        # Gộp lại các mảnh nhỏ thành chunks không vượt quá chunk_size
        final_chunks: list[str] = []
        current_buffer = ""

        for part in parts:
            candidate = (current_buffer + sep + part) if current_buffer else part

            if len(candidate) <= self.chunk_size:
                current_buffer = candidate
            else:
                # Lưu buffer hiện tại nếu có nội dung
                if current_buffer.strip():
                    # Nếu buffer vẫn quá lớn, đệ quy chia tiếp
                    if len(current_buffer) > self.chunk_size:
                        final_chunks.extend(self._split(current_buffer, next_separators))
                    else:
                        final_chunks.append(current_buffer)
                # Bắt đầu buffer mới từ part này
                if len(part) > self.chunk_size:
                    # Part này quá lớn → đệ quy với separator tiếp theo
                    final_chunks.extend(self._split(part, next_separators))
                    current_buffer = ""
                else:
                    current_buffer = part

        # Đừng quên phần còn lại trong buffer
        if current_buffer.strip():
            if len(current_buffer) > self.chunk_size:
                final_chunks.extend(self._split(current_buffer, next_separators))
            else:
                final_chunks.append(current_buffer)

        return [c for c in final_chunks if c.strip()]


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    dot_product = _dot(vec_a, vec_b)
    mag_a = math.sqrt(sum(x * x for x in vec_a))
    mag_b = math.sqrt(sum(x * x for x in vec_b))

    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0

    return dot_product / (mag_a * mag_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        """
        Gọi từng chunker, tính thống kê, trả về dict so sánh.

        Returns:
            {
                'fixed_size': {'count': int, 'avg_length': float, 'chunks': list[str]},
                'by_sentences': {'count': int, 'avg_length': float, 'chunks': list[str]},
                'recursive': {'count': int, 'avg_length': float, 'chunks': list[str]},
            }
        """
        # FixedSizeChunker với overlap mặc định 50
        fixed_chunks = FixedSizeChunker(chunk_size=chunk_size, overlap=50).chunk(text)

        # SentenceChunker — dùng max_sentences_per_chunk=3
        sentence_chunks = SentenceChunker(max_sentences_per_chunk=3).chunk(text)

        # RecursiveChunker
        recursive_chunks = RecursiveChunker(chunk_size=chunk_size).chunk(text)

        def _stats(chunks: list[str]) -> dict:
            count = len(chunks)
            avg_length = sum(len(c) for c in chunks) / count if count > 0 else 0.0
            return {
                "count": count,
                "avg_length": round(avg_length, 2),
                "chunks": chunks,
            }

        return {
            "fixed_size": _stats(fixed_chunks),
            "by_sentences": _stats(sentence_chunks),
            "recursive": _stats(recursive_chunks),
        }
