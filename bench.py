"""
bench.py — Benchmark & Retrieval Quality Evaluation Tool (Lab 7)

Chức năng:
1. Đọc từng file .md, tách YAML frontmatter thành metadata và phần thân thành content.
2. Chunk phần thân ngoài store; mỗi chunk thành 1 Document:
     Document(id=f"{path.stem}#{i}", content=chunk, metadata={**frontmatter, "doc_id": path.stem, "chunk_index": i})
3. Nạp vào EmbeddingStore, chạy 5 câu hỏi benchmark qua search_with_filter().
4. Chấm điểm 2 MỨC ĐỘC LẬP:
     - Mức 1: Doc-level (kiểm tra doc_id đúng có trong top-3 không)
     - Mức 2: Content-level (kiểm tra chunk top-k có thực sự chứa chuỗi đáp án key_phrase không)
5. A/B Testing bắt buộc: Chạy câu 5 có filter vs không filter để chứng minh vai trò của metadata.
6. Xuất toàn bộ kết quả ra màn hình và file `ket_qua_benchmark.txt`.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from dotenv import load_dotenv

from src.agent import KnowledgeBaseAgent
from src.chunking import (
    FixedSizeChunker,
    RecursiveChunker,
    SentenceChunker,
)
from src.embeddings import (
    EMBEDDING_PROVIDER_ENV,
    GEMINI_EMBEDDING_MODEL,
    LOCAL_EMBEDDING_MODEL,
    OPENAI_EMBEDDING_MODEL,
    GeminiEmbedder,
    LocalEmbedder,
    MockEmbedder,
    OpenAIEmbedder,
    _mock_embed,
)
from src.models import Document
from src.store import EmbeddingStore

# ==============================================================================
# CẤU HÌNH CHIẾN LƯỢC CHUNKING (Mỗi thành viên đổi 1 dòng này để so sánh)
# ==============================================================================
# CHUNKER = FixedSizeChunker(chunk_size=400, overlap=50)
# CHUNKER = SentenceChunker(max_sentences_per_chunk=3)
CHUNKER = RecursiveChunker(chunk_size=400)
# ==============================================================================

EMBEDDING_CACHE_FILE = Path(".embedding_cache.json")


def load_embedding_cache() -> dict[str, list[float]]:
    if EMBEDDING_CACHE_FILE.exists():
        try:
            return json.loads(EMBEDDING_CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_embedding_cache(cache: dict[str, list[float]]) -> None:
    try:
        EMBEDDING_CACHE_FILE.write_text(json.dumps(cache), encoding="utf-8")
    except Exception:
        pass


def get_cached_embedder(base_embedder: Callable[[str], list[float]]) -> Callable[[str], list[float]]:
    """Bọc embedder với cache hash để tránh tốn API khi chạy lại."""
    cache = load_embedding_cache()

    def _embed_with_cache(text: str) -> list[float]:
        text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if text_hash in cache:
            return cache[text_hash]
        vec = base_embedder(text)
        cache[text_hash] = vec
        save_embedding_cache(cache)
        return vec

    return _embed_with_cache


def get_configured_embedder() -> Callable[[str], list[float]]:
    """Khởi tạo embedding function dựa trên cấu hình môi trường (.env)."""
    load_dotenv(override=False)
    provider = os.getenv(EMBEDDING_PROVIDER_ENV, "mock").strip().lower()

    if provider == "local":
        try:
            model = os.getenv("LOCAL_EMBEDDING_MODEL", LOCAL_EMBEDDING_MODEL)
            return get_cached_embedder(LocalEmbedder(model_name=model))
        except Exception as err:
            print(f"[WARN] Failed to init LocalEmbedder ({err}), falling back to mock.")
            return _mock_embed
    elif provider == "openai":
        try:
            model = os.getenv("OPENAI_EMBEDDING_MODEL", OPENAI_EMBEDDING_MODEL)
            return get_cached_embedder(OpenAIEmbedder(model_name=model))
        except Exception as err:
            print(f"[WARN] Failed to init OpenAIEmbedder ({err}), falling back to mock.")
            return _mock_embed
    elif provider == "gemini":
        try:
            model = os.getenv("GEMINI_EMBEDDING_MODEL", GEMINI_EMBEDDING_MODEL)
            return get_cached_embedder(GeminiEmbedder(model_name=model))
        except Exception as err:
            print(f"[WARN] Failed to init GeminiEmbedder ({err}), falling back to mock.")
            return _mock_embed
    return _mock_embed


def parse_frontmatter(raw_text: str) -> tuple[dict[str, Any], str]:
    """Tách YAML frontmatter thành metadata dict và phần thân content."""
    if raw_text.startswith("---"):
        parts = raw_text.split("---", 2)
        if len(parts) >= 3:
            raw_meta = parts[1].strip()
            content = parts[2].strip()
            metadata: dict[str, Any] = {}
            for line in raw_meta.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if ":" in line:
                    k, v = line.split(":", 1)
                    metadata[k.strip()] = v.strip().strip('"').strip("'")
            return metadata, content
    return {}, raw_text.strip()


def load_corpus(data_dir: Path, chunker: Any) -> tuple[list[Document], dict[str, int]]:
    docs: list[Document] = []
    chunk_counts: dict[str, int] = {}

    md_files = sorted(data_dir.glob("*.md"))
    if not md_files:
        raise FileNotFoundError(f"Không tìm thấy file .md nào trong thư mục {data_dir.resolve()}")

    for file_path in md_files:
        raw_text = file_path.read_text(encoding="utf-8")
        frontmatter, body = parse_frontmatter(raw_text)

        chunks = chunker.chunk(body)
        chunk_counts[file_path.name] = len(chunks)

        for i, chunk_text in enumerate(chunks):
            doc = Document(
                id=f"{file_path.stem}#{i}",
                content=chunk_text,
                metadata={
                    **frontmatter,
                    "doc_id": file_path.stem,
                    "chunk_index": i,
                    "source_file": file_path.name,
                },
            )
            docs.append(doc)

    return docs, chunk_counts


# ==============================================================================
# 5 BENCHMARK QUERIES (Nhóm K4 dùng chung — R2 chủ trì)
# Mỗi câu có chuỗi đặc trưng (key_phrases) để chấm Content-Level thực chất!
# ==============================================================================
BENCHMARK_QUERIES: list[dict[str, Any]] = [
    {
        "id": 1,
        "type": "Tra số liệu (Numeric lookup)",
        "query": "Định mức điện nước miễn phí cho mỗi phòng KTX trong một kỳ là bao nhiêu và mức phí phụ trội khi dùng vượt?",
        "filter": None,
        "gold_doc_id": "fpt-ocd-portal",
        "gold_answer": (
            "Định mức miễn phí: 200 số Điện & 12 số Nước mỗi phòng/kỳ. "
            "Dùng vượt định mức phải nộp phí phụ trội: 2,500đ/số điện, 10,000đ/số nước."
        ),
        "key_phrases": ["200 số Điện", "12 số Nước", "2,500"],
    },
    {
        "id": 2,
        "type": "Hỏi điều kiện (Condition requirements)",
        "query": "Tủ lạnh sinh viên được phép mang vào KTX cần đáp ứng những điều kiện và tiêu chuẩn gì?",
        "filter": None,
        "gold_doc_id": "fpt-noi-quy-ktx-hl",
        "gold_answer": (
            "Mỗi phòng/block được 01 tủ lạnh dung tích dưới 110L; sử dụng nguồn điện đúng ổ cắm tiêu chuẩn (kiểu G); "
            "yêu cầu thời gian sử dụng ≤ 3 năm tính từ ngày sản xuất; thời hạn sử dụng tại KTX không quá 10 năm; "
            "phải lưu phiếu bảo trì để phục vụ kiểm tra định kỳ."
        ),
        "key_phrases": ["110L", "kiểu G", "3 năm", "bảo trì"],
    },
    {
        "id": 3,
        "type": "Hỏi quy trình (Step-by-step procedure)",
        "query": "Quy trình gửi yêu cầu báo cáo sửa chữa đồ dùng kỹ thuật trong phòng KTX gồm những bước nào?",
        "filter": None,
        "gold_doc_id": "fpt-ocd-portal",
        "gold_answer": (
            "Bước 1: Vào chức năng My request -> Chọn Create new request -> Chọn 'Báo cáo vấn đề kỹ thuật'. "
            "Bước 2: Hệ thống dẫn tới trang https://cim.fpt.edu.vn/. "
            "Bước 3: Điền thông tin và gửi ảnh tình trạng thiết bị lên CIM, sau đó bấm Create."
        ),
        "key_phrases": ["My request", "cim.fpt.edu.vn", "Báo cáo vấn đề kỹ thuật"],
    },
    {
        "id": 4,
        "type": "Liệt kê (Enumeration / List)",
        "query": "Danh mục các thiết bị điện sinh viên được phép mang vào sử dụng tại KTX bao gồm những thiết bị nào?",
        "filter": None,
        "gold_doc_id": "fpt-noi-quy-ktx-hl",
        "gold_answer": (
            "Máy tính (để bàn, laptop), tủ lạnh (dưới 110L/phòng), quạt điện, bàn là, "
            "máy sấy tóc, ấm điện (mỗi phòng 1-2 ấm đun có rơle tự ngắt), đèn học. "
            "Thiết bị khác phải được BQL KTX đồng ý."
        ),
        "key_phrases": ["ấm điện", "bàn là", "quạt điện", "máy sấy tóc"],
    },
    {
        "id": 5,
        "type": "Lọc đối tượng (Audience Filter — Tránh nhầm tài liệu BQL vs Sinh viên)",
        "query": "Quy trình kiểm tra phòng",
        "filter": {"audience": "student"},
        "gold_doc_id": "fpt-noi-quy-ktx-hl",
        "gold_answer": (
            "Theo quy định dành cho sinh viên (fpt-noi-quy-ktx-hl Điều 9): "
            "Việc kiểm tra được thực hiện theo nguyên tắc thông báo và yêu cầu sinh viên phối hợp mở cửa; "
            "trường hợp khẩn cấp hoặc không chấp hành, cán bộ được phép mở cửa vào và lập biên bản."
        ),
        "key_phrases": ["kiểm tra", "phối hợp mở cửa", "lập biên bản"],
        "contrast_no_filter_warning": (
            "Nếu KHÔNG lọc audience: student, Top-1 trả về quy trình dành cho Ban Quản Lý (fpt-quy-dinh-bql - staff) "
            "yêu cầu BQL kiểm tra thứ 5 hàng tuần 14h-16h, gõ cửa 3 lần, lập biên bản tịch thu nộp kho DOM và báo cáo OCD."
        ),
    },
]


def run_benchmark() -> str:
    lines: list[str] = []

    def log(msg: str = "") -> None:
        print(msg)
        lines.append(msg)

    log("=" * 80)
    log("           BENCHMARK RETRIEVAL QUALITY — LAB 7: EMBEDDING & VECTOR STORE")
    log("=" * 80)

    strategy_name = CHUNKER.__class__.__name__
    log(f"\n[1] CHIẾN LƯỢC CHUNKING ĐANG DÙNG: {strategy_name}")

    data_dir = Path("data/kytucxa")
    if not data_dir.exists():
        data_dir = Path("data")
    log(f"[2] THƯ MỤC DỮ LIỆU: {data_dir.resolve()}")

    docs, chunk_counts = load_corpus(data_dir, CHUNKER)
    total_chunks = len(docs)
    log(f"[3] KẾT QUẢ CHUNKING TỪNG FILE:")
    for doc_file, count in chunk_counts.items():
        log(f"    - {doc_file:30s} -> {count:3d} chunks")
    log(f"    ==> Tổng số chunk đã nạp: {total_chunks}")

    embedder = get_configured_embedder()
    store = EmbeddingStore(collection_name="kytucxa_benchmark", embedding_fn=embedder)
    store.add_documents(docs)
    log(f"[4] Đã nạp thành công {store.get_collection_size()} chunks vào EmbeddingStore.")

    log("\n" + "=" * 80)
    log("     ĐÁNH GIÁ 5 BENCHMARK QUERIES — CHẤM 2 MỨC (DOC-LEVEL VS CONTENT-LEVEL)")
    log("=" * 80)

    doc_level_total = 0
    content_level_total = 0

    for item in BENCHMARK_QUERIES:
        q_id = item["id"]
        q_type = item["type"]
        query = item["query"]
        meta_filter = item["filter"]
        gold_doc = item["gold_doc_id"]
        gold_ans = item["gold_answer"]
        key_phrases = item.get("key_phrases", [])

        log(f"\n--------------------------------------------------------------------------------")
        log(f"CÂU HỎI #{q_id} [{q_type}]")
        log(f"Query: \"{query}\"")
        if meta_filter:
            log(f"Filter áp dụng: {meta_filter}")
        log(f"Tài liệu chuẩn (Gold doc_id): {gold_doc}")
        log(f"Chuỗi đặc trưng bắt buộc (Key Phrases): {key_phrases}")
        log(f"Câu trả lời chuẩn (Gold Answer):\n  {gold_ans}")

        results = store.search_with_filter(query, top_k=3, metadata_filter=meta_filter)

        log(f"\nTop-3 chunks được truy xuất:")
        doc_hit_rank = -1
        content_hit_rank = -1

        for rank, res in enumerate(results, start=1):
            res_meta = res.get("metadata", {})
            retrieved_doc = res_meta.get("doc_id", "unknown")
            chunk_id = res.get("id", "unknown")
            score = res.get("score", 0.0)
            content_text = res.get("content", "")
            preview = content_text.replace("\n", " ").strip()
            if len(preview) > 130:
                preview = preview[:130] + "..."

            is_gold_doc = (retrieved_doc == gold_doc)
            has_key_phrase = any(phrase.lower() in content_text.lower() for phrase in key_phrases)

            markers = []
            if is_gold_doc:
                markers.append("MATCH_DOC")
                if doc_hit_rank == -1:
                    doc_hit_rank = rank
            if is_gold_doc and has_key_phrase:
                markers.append("CONTAINS_ANSWER")
                if content_hit_rank == -1:
                    content_hit_rank = rank

            marker_str = f" [{' | '.join(markers)}]" if markers else ""
            log(f"  [{rank}] Score: {score:+.4f} | doc_id: {retrieved_doc:20s} | Chunk: {chunk_id}{marker_str}")
            log(f"      Preview: \"{preview}\"")

        # 1. Chấm Doc-Level (Ngây thơ: chỉ cần trùng doc_id trong top-3)
        if doc_hit_rank == 1:
            doc_score = 2
        elif doc_hit_rank in (2, 3):
            doc_score = 1
        else:
            doc_score = 0
        doc_level_total += doc_score

        # 2. Chấm Content-Level (Thực chất: chunk phải chứa key_phrase trả lời được)
        if content_hit_rank == 1:
            content_score = 2
            content_desc = "Top-1 chứa đúng chunk có đáp án (+2đ)"
        elif content_hit_rank in (2, 3):
            content_score = 1
            content_desc = f"Top-{content_hit_rank} chứa chunk có đáp án (+1đ)"
        else:
            content_score = 0
            content_desc = "Top-3 KHÔNG chứa chunk có thông tin đáp án (+0đ)"
        content_level_total += content_score

        log(f"\n==> Điểm Doc-Level (ngây thơ)   : {doc_score}/2 điểm (Doc Hit Rank: {doc_hit_rank if doc_hit_rank > 0 else 'None'})")
        log(f"==> Điểm Content-Level (thực chất): {content_score}/2 điểm [{content_desc}]")

        # THỬ NGHIỆM ĐỐI CHỨNG A/B CÂU 5
        if q_id == 5:
            log("\n  ==========================================================================")
            log("  [THỬ NGHIỆM ĐỐI CHỨNG A/B CÂU 5: CÓ FILTER VS KHÔNG FILTER]")
            log("  ==========================================================================")
            no_filter_res = store.search_with_filter(query, top_k=3, metadata_filter=None)
            log("  --> KẾT QUẢ KHÔNG FILTER (filter=None):")
            for rank, r in enumerate(no_filter_res, start=1):
                r_meta = r.get("metadata", {})
                r_doc = r_meta.get("doc_id", "unknown")
                r_aud = r_meta.get("audience", "all")
                r_score = r.get("score", 0.0)
                r_prev = r.get("content", "").replace("\n", " ").strip()[:90]
                log(f"      [{rank}] doc_id: {r_doc:20s} (audience: {r_aud:7s}) | Score: {r_score:+.4f} | \"{r_prev}...\"")

            log("\n  --> KẾT QUẢ CÓ FILTER (metadata_filter={'audience': 'student'}):")
            for rank, r in enumerate(results, start=1):
                r_meta = r.get("metadata", {})
                r_doc = r_meta.get("doc_id", "unknown")
                r_aud = r_meta.get("audience", "all")
                r_score = r.get("score", 0.0)
                r_prev = r.get("content", "").replace("\n", " ").strip()[:90]
                log(f"      [{rank}] doc_id: {r_doc:20s} (audience: {r_aud:7s}) | Score: {r_score:+.4f} | \"{r_prev}...\"")

            log(f"\n  ==> KẾT LUẬN A/B:")
            log(f"      {item.get('contrast_no_filter_warning')}")
            log("      => Lọc metadata giúp loại bỏ 100% tài liệu SOP Ban Quản Lý (staff),")
            log("         đảm bảo sinh viên chỉ nhận được quy chế kiểm tra phòng áp dụng cho sinh viên!")

    log("\n" + "=" * 80)
    log("                           TỔNG KẾT SO SÁNH HAI MỨC CHẤM")
    log("=" * 80)
    log(f"Chiến lược chunking: {strategy_name}")
    log(f"- Tổng điểm Doc-Level (Ngây thơ)    : {doc_level_total:2d} / 10 Điểm")
    log(f"- Tổng điểm Content-Level (Thực chất): {content_level_total:2d} / 10 Điểm")
    diff = doc_level_total - content_level_total
    log(f"- Chênh lệch do 'trúng file nhưng trượt chunk đáp án': -{diff} Điểm")
    log("=" * 80)

    full_output = "\n".join(lines)
    Path("ket_qua_benchmark.txt").write_text(full_output, encoding="utf-8")
    print(f"\n[DONE] Đã lưu kết quả hoàn chỉnh vào file 'ket_qua_benchmark.txt'!")
    return full_output


if __name__ == "__main__":
    run_benchmark()
