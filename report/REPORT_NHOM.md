# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** G12 - E403 (K4 — Lớp L3A)  
**Thành viên:**
1. **Nguyễn Khánh Sơn** (Strategy Lead — MSSV: 2A202602388)
2. **Ngô Xuân Hoàng** (Benchmark Lead — MSSV: 2A202602597)
3. **Bùi Thị Thu Uyên** (Code Lead — MSSV: 2A202602613)  
4. **Lê Châu Trần Phát** (Data Lead — MSSV: 2A202602545)  
**Ngày:** 2026-09-19  

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Quy định, nội quy và dịch vụ Ký túc xá Trường Đại học FPT phân hiệu Hà Nội (Campus Hòa Lạc).

**Tại sao nhóm chọn chủ đề này?**
> Nhóm chọn chủ đề Ký túc xá Đại học FPT vì đây là dịch vụ đời sống thiết yếu phục vụ hàng nghìn sinh viên nội trú tại Campus Hòa Lạc. Bộ dữ liệu bao gồm các quy định chính thức (Quyết định số 1034/QĐ-ĐHFPT ngày 16/09/2025), hướng dẫn nhận phòng K19, tiện ích, kinh nghiệm sống, cổng thông tin nội trú OCD và quy trình SOP kiểm tra phòng của BQL. Dữ liệu có sự phân hóa đối tượng rõ nét (`student`, `all`, `staff`), rất phù hợp để kiểm thử chiến lược chia nhỏ (chunking) và tính năng lọc theo metadata trong hệ thống RAG.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Hướng dẫn K19 nhận phòng KTX | https://daihoc.fpt.edu.vn/chua-phan-loai/huong-dan-k19-chuan-bi-va-nhan-phong-ktx-dai-hoc-fpt-ha-noi/ | 2026-09-19 / K19 | 2404 | audience: student, dept: student-affairs, cat: guide |
| 2 | Bí quyết làm quen KTX | https://daihoc.fpt.edu.vn/chua-phan-loai/sinh-vien-chia-se-bi-quyet-lam-quen-voi-cuoc-song-ktx-dh-fpt-ha-noi/ | 2026-09-19 / not-stated | 2505 | audience: student, dept: student-affairs, cat: tips |
| 3 | Nội quy Ký túc xá FPT Hòa Lạc | https://ocd.fpt.edu.vn/Files/policy/KTX-HL.pdf | 2026-09-19 / 1.0 | 22614 | audience: student, dept: dom-management, cat: regulation |
| 4 | Cổng thông tin nội bộ FPT OCD | https://ocd.fpt.edu.vn/ | 2026-09-19 / not-stated | 2732 | audience: all, dept: dom-management, cat: portal |
| 5 | Quy định kiểm tra phòng dành cho BQL DOM | internal://fpt-quy-dinh-bql | 2026-09-19 / 2026 | 1063 | audience: staff, dept: dom-management, cat: SOP |
| 6 | Tiện ích KTX FPT Hà Nội | https://daihoc.fpt.edu.vn/chua-phan-loai/kham-pha-khong-gian-va-nhung-tien-ich-tai-ky-tuc-xa-dai-hoc-fpt-ha-noi/ | 2026-09-19 / not-stated | 1583 | audience: student, dept: dom-management, cat: info |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu bí mật.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | string | `fpt-noi-quy-ktx-hl` | Định danh duy nhất của tài liệu, dùng để truy vết nguồn (provenance) và phục vụ việc xóa tài liệu (`delete_document`). |
| `title` | string | `Nội quy Ký túc xá FPT Hòa Lạc` | Hiển thị tiêu đề tự nhiên khi trích dẫn nguồn cho người dùng. |
| `source_url` | string | `https://ocd.fpt.edu.vn/Files/policy/KTX-HL.pdf` | Lưu URL gốc để kiểm chứng và dẫn nguồn trong câu trả lời. |
| `retrieved_at` | string | `2026-09-19` | Kiểm soát tính mới và thời điểm thu thập dữ liệu. |
| `document_version` | string | `1.0` / `K19` / `not-stated` | Xác định phiên bản hoặc khóa áp dụng của văn bản. |
| `audience` | string | `student` / `all` / `staff` | Lọc chính xác thông tin dành cho sinh viên nội trú, cán bộ BQL hay thông tin chung cho mọi người. |
| `department` | string | `dom-management`, `student-affairs` | Khoanh vùng phòng ban phụ trách trực tiếp để định tuyến câu hỏi. |
| `category` | string | `regulation`, `guide`, `portal`, `SOP`, `info`, `tips` | Phân nhóm nghiệp vụ theo chủ đề cụ thể để tối ưu hóa truy xuất. |
| `language` | string | `vi` | Định rõ ngôn ngữ tài liệu (tiếng Việt). |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 3 tài liệu đại diện trong `data/kytucxa/` với tham số `chunk_size=300`:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| `fpt-huong-dan-nhan-phong` | FixedSizeChunker (`fixed_size`) | 8 | 273.4 | Dễ cắt ngang các gạch đầu dòng liệt kê thiết bị được phép mang vào KTX. |
| `fpt-huong-dan-nhan-phong` | SentenceChunker (`by_sentences`) | 6 | 339.5 | Giữ trọn vẹn từng câu quy định kích thước giường và thiết bị. |
| `fpt-huong-dan-nhan-phong` | RecursiveChunker (`recursive`) | 10 | 203.4 | Cắt tốt theo các ranh giới đoạn `\n\n` và ngắt dòng `\n`. |
| `fpt-ocd-portal` | FixedSizeChunker (`fixed_size`) | 9 | 288.3 | Dễ cắt đôi các câu hỏi FAQ và số liệu định mức điện nước. |
| `fpt-ocd-portal` | SentenceChunker (`by_sentences`) | 12 | 201.3 | Tách theo câu hỏi - đáp án khá tốt, một số chunk hơi ngắn. |
| `fpt-ocd-portal` | RecursiveChunker (`recursive`) | 11 | 219.9 | Cắt đúng ranh giới các mục FAQ đánh số (### 1, ### 2...). |
| `fpt-quy-dinh-bql` | FixedSizeChunker (`fixed_size`) | 3 | 266.0 | Cắt ngang các bước trong quy trình kiểm tra phòng. |
| `fpt-quy-dinh-bql` | SentenceChunker (`by_sentences`) | 3 | 250.0 | Giữ nguyên từng bước quy trình SOP kiểm tra phòng. |
| `fpt-quy-dinh-bql` | RecursiveChunker (`recursive`) | 4 | 188.5 | Tách theo từng bước đánh số và đoạn văn bản. |

---

### Chiến lược của từng thành viên (Tổng hợp từ Báo cáo cá nhân)

#### 1. Nguyễn Khánh Sơn — Strategy Lead (`HeadingChunker`)
- **Chiến lược:** Custom `HeadingChunker` (`max_chunk_size=400`) kết hợp nhận diện cấu trúc tiêu đề Markdown và đệ quy bảo toàn ngữ cảnh cha.
- **Mô tả thuật toán & Lý do chọn:**
  - Văn bản quy chế KTX được cấu trúc chặt chẽ theo các đề mục lớn (`## 1. `, `## 2. `, `### `). `HeadingChunker` sử dụng regex lookahead `(?=(?:\n|^)#{1,3}\s+)` để phân tách tài liệu thành các khối section hoàn chỉnh.
  - **Kỹ thuật Heading Prefixing:** Khi một section quá dài buộc phải chia nhỏ, thuật toán gọi `RecursiveChunker` nhưng tự động chèn dòng tiêu đề mục cha `#` vào đầu mỗi chunk con (`f"{header}\n{sub}"`). Nhờ đó, vector embedding của chunk con không bao giờ bị "mất gốc", luôn giữ được ngữ cảnh "đang nói về quy định gì".
- **Minh họa code:**
```python
class HeadingChunker:
    def __init__(self, max_chunk_size: int = 400) -> None:
        self.max_chunk_size = max_chunk_size
        self.recursive = RecursiveChunker(chunk_size=max_chunk_size)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []
        sections = re.split(r'(?=(?:\n|^)#{1,3}\s+)', text.strip())
        chunks: list[str] = []
        for sec in sections:
            sec_clean = sec.strip()
            if not sec_clean:
                continue
            if len(sec_clean) <= self.max_chunk_size:
                chunks.append(sec_clean)
            else:
                lines = sec_clean.split("\n", 1)
                header = lines[0] if lines[0].startswith("#") else ""
                body = lines[1] if len(lines) > 1 else ""
                sub_chunks = self.recursive.chunk(body if body else sec_clean)
                for sub in sub_chunks:
                    chunks.append(f"{header}\n{sub}" if header and not sub.startswith("#") else sub)
        return chunks
```

#### 2. Ngô Xuân Hoàng — Benchmark Lead (`RecursiveChunker`)
- **Chiến lược:** `RecursiveChunker` (`chunk_size=400`, separators `["\n\n", "\n", ". ", " ", ""]`).
- **Mô tả thuật toán & Lý do chọn:**
  - Hoạt động theo nguyên tắc **chia để trị đệ quy**: thử nghiệm lần lượt các separator từ lớn đến nhỏ. Ưu tiên ngắt đoạn `\n\n` và xuống dòng `\n` trước khi hạ xuống câu `. ` và từ `" "`.
  - **Kỹ thuật Buffer Accumulation:** Sau khi cắt theo separator, gom dần các mảnh nhỏ vào buffer cho đến khi sát `chunk_size` mới flush, tránh sinh ra các chunk vụn 5–10 ký tự.
  - **Ba trường hợp cơ sở (Base cases):** `len(text) <= chunk_size` trả về ngay; hết separator thì fallback chia cố định; `sep == ""` cắt theo ký tự. Chiến lược này cân bằng tối ưu giữa kích thước chunk và ngữ nghĩa phân đoạn của các điều khoản KTX.

#### 3. Bùi Thị Thu Uyên — Code Lead (`FixedSizeChunker`)
- **Chiến lược:** `FixedSizeChunker` (`chunk_size=500`, `overlap=50` hoặc `chunk_size=400, overlap=50`).
- **Mô tả thuật toán & Lý do chọn:**
  - Cắt cố định văn bản thành các đoạn dài tối đa `chunk_size`, bước dịch `step = chunk_size - overlap`. Hai chunk liền kề chia sẻ `overlap` ký tự để giữ ngữ cảnh ở ranh giới.
  - **Kiểm soát chặt chẽ:** Đã kiểm chứng công thức toán học `ceil((10000 - overlap)/(chunk_size - overlap)) = 23 chunks` (hoặc 25 chunks khi `overlap=100`). Dừng ngay khi chạm cuối văn bản để không sinh chunk rỗng. Đóng vai trò là đường cơ sở (baseline) đồng đều, ổn định để so sánh với các phương pháp chia theo cấu trúc.

#### 4. Lê Châu Trần Phát — Data Lead (`SentenceChunker`)
- **Chiến lược:** `SentenceChunker` (`max_sentences=3`, tích hợp regex positive lookbehind).
- **Mô tả thuật toán & Lý do chọn:**
  - Dùng biểu thức chính quy `(?<=\. )|(?<=! )|(?<=\? )|(?<=\.\n)` để tách câu dựa vào các dấu kết thúc câu mà không làm mất dấu câu. Sau đó gom nhóm tối đa `max_sentences_per_chunk` và strip khoảng trắng thừa.
  - **Bảo toàn cú pháp:** Giữ trọn vẹn từng câu quy định (như kích thước giường 1.0m x 1.9m, định mức điện nước), hạn chế tối đa việc câu bị đứt ngang giữa chừng. Đồng thời đóng góp giải pháp phân tích quan hệ giữa metadata `audience: student` và `audience: all`.

---

### So Sánh Giữa Các Thành Viên

| Thành viên | Vai trò (Workstream) | Chiến lược (Strategy) | Điểm mạnh | Điểm yếu |
|-----------|----------------------|-----------------------|-----------|----------|
| **Nguyễn Khánh Sơn** | Strategy Lead | HeadingChunker | Giữ trọn vẹn ngữ cảnh của từng điều khoản; luôn bảo toàn tiêu đề mục `#` trong mọi chunk con. | Cần văn bản có định dạng tiêu đề Markdown chuẩn xác; kích thước chunk dao động. |
| **Ngô Xuân Hoàng** | Benchmark Lead | RecursiveChunker | Cân bằng tuyệt vời giữa cấu trúc đoạn và kích thước; tôn trọng ngắt đoạn và gạch đầu dòng. | Vẫn có thể tạo ra các chunk con không mang theo tiêu đề mục cha nếu không prefix. |
| **Bùi Thị Thu Uyên** | Code Lead | FixedSizeChunker | Đơn giản, độ dài chunk cực kỳ đồng đều, dễ dự đoán bộ nhớ và chi phí token. | Cắt cơ học dễ xé đôi câu văn, tách rời tiêu đề khỏi bảng số liệu hoặc điều khoản. |
| **Lê Châu Trần Phát** | Data Lead | SentenceChunker | Giữ nguyên vẹn tính trọn vẹn cú pháp của từng câu đơn lẻ; không bao giờ bị cụt câu. | Không gom nhóm được cấu trúc bảng biểu (Markdown tables) hoặc danh mục dài. |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> **Chiến lược `HeadingChunker` (kết hợp RecursiveChunker)** là tối ưu nhất cho văn bản quy định, pháp quy đại học. Vì toàn bộ nội quy KTX luôn được soạn thảo theo cấu trúc phân tầng (Chương -> Điều -> Khoản). Việc phân rã theo heading và gắn kèm tiêu đề mục cha vào từng chunk con giúp embedding store luôn nắm bắt được chủ đề gốc của chunk, loại bỏ hiện tượng chunk bị "vô danh" khi tìm kiếm.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Bộ 5 câu hỏi đánh giá chuẩn (Thống nhất chung cả nhóm)

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chuỗi đặc trưng cần có (Content check) | Tài liệu đích (Target Doc) |
|---|-------|-------------------------------|----------------------------------------|---------------------------|
| 1 | Sinh viên ở KTX FPT được phép mang những thiết bị điện nào vào phòng và tủ lạnh cần đáp ứng dung tích bao nhiêu? | Sinh viên được phép mang ti vi, tủ lạnh (dung tích dưới 110L/phòng), quạt điện, bàn là, ấm điện, đèn học. | `110L`, `110`, `tủ lạnh` | `fpt-huong-dan-nhan-phong` |
| 2 | Định mức sử dụng điện nước miễn phí mỗi kỳ tại KTX FPT là bao nhiêu và đơn giá thu phụ trội khi vượt mức là bao nhiêu? | Định mức miễn phí mỗi kỳ là 200 số điện và 12 số nước. Khi dùng vượt định mức, đơn giá phụ trội là 2.500đ/số điện và 10.000đ/số nước. | `200`, `2.500`, `2,500` | `fpt-ocd-portal` |
| 3 | Hạn chót làm thủ tục check-out trả phòng cuối kỳ là khi nào và mức phạt nếu check-out muộn là bao nhiêu? | Sinh viên phải làm thủ tục check-out chậm nhất ngày 30 của tháng cuối kỳ; làm check-out muộn phải thanh toán chi phí bồi thường tương đương 100% tiền phòng kỳ sau. | `ngày 30`, `100%` | `fpt-noi-quy-ktx-hl` |
| 4 | Ban Quản lý KTX kiểm tra phòng sinh viên định kỳ vào thời gian nào và quy trình kiểm tra ra sao? | BQL kiểm tra phòng định kỳ vào thứ 5 hàng tuần, từ 14:00 đến 16:00. Cán bộ gõ cửa trước ít nhất 3 lần, kiểm tra thiết bị cấm và vệ sinh phòng. | `thứ 5`, `14:00`, `gõ cửa` | `fpt-quy-dinh-bql` |
| 5 | Các lưu ý và giờ giới nghiêm khi ở KTX? *(Cần lọc `audience: student`)* | Cửa KTX mở từ 05h00 đến 23h00; sinh viên không được tiếp khách hoặc người lạ trong phòng ở, chỉ được tiếp khách tại khu vực quy định trong khung giờ 07h00 - 21h00, cấm sang phòng người khác giới. | `23h00`, `người lạ trong phòng`, `07h00` | `fpt-noi-quy-ktx-hl` |

---

### Đánh giá hai mức: Mức 1 (Doc-level Naive) vs Mức 2 (Content-level Strict)

> **Phát hiện quan trọng nhất của nhóm (Thống nhất từ phân tích của Sơn, Hoàng, Uyên, Phát):**  
> - **Cách chấm ngây thơ (Mức 1 - Doc-level):** Chỉ kiểm tra xem `doc_id` của tài liệu gold có xuất hiện trong Top-3 hay không. Cách này tạo ra sự **thổi phồng kết quả (false confidence)** rất lớn vì tài liệu dài như `fpt-noi-quy-ktx-hl` chiếm phần lớn corpus (gần 80 chunks), xác suất ngẫu nhiên một chunk của nó rơi vào top-3 là rất cao dù nội dung hoàn toàn không chứa câu trả lời.  
> - **Cách chấm thực chất (Mức 2 - Content-level):** Bắt buộc chunk lọt Top-3 phải chứa đúng chuỗi đặc trưng chứa câu trả lời (số liệu định mức, hạn chót, danh mục thiết bị).  
> - Thang điểm: 2đ nếu gold ở Top-1 và có đáp án; 1đ nếu ở Top-2/3 có đáp án; 0đ nếu vắng mặt hoặc không trả lời được.

#### 1. Kết quả trên MockEmbedder (Băm MD5 — Phản ánh chênh lệch thổi phồng GAP):
| Chiến lược (Strategy) | Điểm Mức 1 (Doc-level Naive) | Điểm Mức 2 (Content-level Strict) | Chênh lệch thổi phồng (GAP) | Nhận xét bản chất |
|-----------------------|------------------------------|-----------------------------------|-----------------------------|-------------------|
| **FixedSizeChunker** | 4 / 10 | 0 / 10 | 4 điểm | Cắt cơ học khiến số liệu bị chia cắt, trúng top-3 ngẫu nhiên theo hash ký tự. |
| **RecursiveChunker** | 5 / 10 | 0 / 10 | 5 điểm | Trúng tài liệu gold nhờ kích thước lớn nhưng trượt mất section có đáp án. |
| **HeadingChunker** | 3 / 10 | 0 / 10 | 3 điểm | Trúng doc nhưng section đúng bị trôi do MockEmbedder không hiểu ngữ nghĩa. |
| **SemanticChunker** | 6 / 10 | 0 / 10 | 6 điểm | Thổi phồng lớn nhất: doc-level bắt được 3 câu nhưng content không có đáp án. |

#### 2. Kết quả đột phá khi nâng cấp lên Google Gemini Embedding (`gemini-embedding-2` thực tế):
| Chiến lược (Strategy) | Điểm Mức 1 (Doc-level Naive) | Điểm Mức 2 (Content-level Strict) | Chênh lệch thổi phồng (GAP) | Nhận xét thực tế |
|-----------------------|------------------------------|-----------------------------------|-----------------------------|------------------|
| **FixedSizeChunker** | 8 / 10 | 8 / 10 | 0 điểm | Embedding ngữ nghĩa 3072 chiều giúp kéo các đoạn có số liệu lên Top-1/Top-2. |
| **RecursiveChunker** | 9 / 10 | 8 / 10 | 1 điểm | Độ mạch lạc cao, giữ trọn vẹn câu trả lời ở 4/5 câu hỏi. |
| **HeadingChunker** | 9 / 10 | 8 / 10 | 1 điểm | Truy xuất chính xác các section quy định có kèm tiêu đề mục. |
| **SemanticChunker** | **10 / 10** | **10 / 10** | **0 điểm (Hoàn hảo)** | Tách chunk theo ranh giới ngữ nghĩa kết hợp Gemini Embedding đạt độ chính xác tuyệt đối. |

---

### A/B Testing Bắt Buộc: Kiểm chứng giá trị của Metadata Filter (Câu hỏi 5)

Chạy câu hỏi 5 hai lần trên cả 4 chiến lược: một lần **Không có Filter** (`metadata_filter=None`) và một lần **Có Filter** (`metadata_filter={"audience": "student"}`).

| Chiến lược | Kết quả KHÔNG DÙNG FILTER (`None`) | Kết quả CÓ DÙNG FILTER (`audience: student`) | Bằng chứng metadata filter giúp ích |
|------------|-----------------------------------|---------------------------------------------|--------------------------------------|
| **FixedSizeChunker** | **Top-1:** `fpt-ocd-portal` (`audience: all`, score 0.8103)<br>**Top-2:** `fpt-huong-dan-nhan-phong` (`student`) | **Top-1:** `fpt-huong-dan-nhan-phong` (`student`, score 0.7954)<br>**Top-2:** `fpt-noi-quy-ktx-hl` (`student`) | Loại bỏ tài liệu cổng chung OCD ở Top-1, ưu tiên tài liệu sinh viên. |
| **RecursiveChunker** | **Top-1:** `fpt-ocd-portal` (`audience: all`, score 0.8558)<br>**Top-2:** `fpt-noi-quy-ktx-hl` (`student`) | **Top-1:** `fpt-noi-quy-ktx-hl` (`student`, score 0.7888)<br>**Top-2:** `fpt-kinh-nghiem-ktx` (`student`) | Đưa trực tiếp văn bản Nội quy sinh viên lên dẫn đầu Top-1. |
| **HeadingChunker** | **Top-1:** `fpt-ocd-portal` (`audience: all`, score 0.8558)<br>**Top-2:** `fpt-ocd-portal` (`audience: all`) | **Top-1:** `fpt-noi-quy-ktx-hl` (`student`, score 0.7961)<br>**Top-2:** `fpt-noi-quy-ktx-hl` (`student`) | Loại bỏ hoàn toàn 2 chunk FAQ chung chiếm Top-1 và Top-2. |
| **SemanticChunker** | **Top-1:** `fpt-ocd-portal` (`audience: all`, score 0.8026)<br>**Top-2:** `fpt-noi-quy-ktx-hl` (`student`) | **Top-1:** `fpt-noi-quy-ktx-hl` (`student`, score 0.7854)<br>**Top-2:** `fpt-noi-quy-ktx-hl` (`student`) | 100% Top-3 kết quả thuộc văn bản quy định dành riêng cho sinh viên. |

**Kết luận chung về Metadata Pre-filtering:**
> Thử nghiệm A/B chứng minh **Metadata Filter là chốt chặn sống còn** trong hệ thống RAG thực tế. Nếu không có filter, hệ thống trả về quy định chung của cổng trường (nêu giờ đóng cổng 22h00) hoặc quy trình SOP của cán bộ BQL (`fpt-quy-dinh-bql`). Nhờ có `audience: student`, hệ thống loại bỏ triệt để nhiễu và trả lời chính xác giờ đóng cửa KTX của sinh viên là 23h00.

---

## 4. Thuyết trình (Demo) & Phân tích lỗi (Failure Analysis) — Nhóm (5 điểm)

### Phân tích lỗi thực tế (Failure Case Analysis)

#### Failure Case 1: Đúng tài liệu nhưng sai Section / Trượt số liệu (Trích từ phân tích của Hoàng & Sơn)
1. **Hiện tượng:** Ở Câu hỏi 1 & Câu hỏi 2, hệ thống trả về đúng tài liệu `fpt-noi-quy-ktx-hl` nhưng chunk được chọn lại là điều khoản cấm mua bán qua hàng rào hoặc quy định an toàn PCCC, hoàn toàn vắng bóng định mức điện nước hay quy định dung tích tủ lạnh.
2. **Nguyên nhân kỹ thuật:**
   - Khi dùng MockEmbedder (băm MD5), hàm băm không hiểu ngữ nghĩa của các con số ("110L", "200 số điện").
   - Văn bản `fpt-noi-quy-ktx-hl` quá dài (79 chunks) tạo ra mật độ từ khóa chung ("Ký túc xá", "quy định", "sinh viên") lấn át các tài liệu chuyên biệt ngắn hơn như `fpt-ocd-portal`.
3. **Giải pháp khắc phục:**
   - **Kích hoạt Dense Semantic Embedding:** Dùng `gemini-embedding-2` hoặc `paraphrase-multilingual-MiniLM-L12-v2` để đưa ngữ nghĩa thực vào không gian vector (giải quyết triệt để vấn đề này, nâng điểm Content-level từ 0/10 lên 8-10/10).
   - **Hybrid Search (Dense Vector + BM25):** Kết hợp tìm kiếm từ khóa chính xác BM25 cho các câu hỏi tra cứu con số cụ thể.

#### Failure Case 2: Đánh đổi Precision vs Recall khi dùng Hard Filter (Trích từ phát hiện của Phát & Uyên)
1. **Hiện tượng:** Khi áp dụng hard filter `metadata_filter={"audience": "student"}`, hệ thống loại bỏ 100% các tài liệu có tag `audience: all` (như Cổng thông tin `fpt-ocd-portal`), khiến các câu hỏi về "Điểm uy tín" hay "Kinh nghiệm chung" bị báo không tìm thấy.
2. **Nguyên nhân kỹ thuật:**
   - Cơ chế so khớp bằng tuyệt đối (`record['audience'] == filter['audience']`) xem `all` và `student` là hai tập tách biệt.
3. **Giải pháp khắc phục:**
   - **Lọc mềm (Hierarchical Soft Filtering / Metadata Boosting):** Cập nhật logic trong `EmbeddingStore`: nếu người dùng lọc theo `student`, hệ thống tự động chấp nhận cả tài liệu có `audience: all`, hoặc cộng điểm ưu tiên `score += 0.15` cho `student` thay vì loại bỏ hoàn toàn `all`.

---

### Những bài học và phân tích hay nhất nhóm sẽ trình bày (Demo Highlights)

1. **Sơn (Strategy Lead):** Chiến lược `HeadingChunker` kết hợp Heading Prefixing giúp bảo toàn trọn vẹn ngữ cảnh phân tầng của văn bản quy chế, khắc phục triệt để tình trạng chunk con bị "mất gốc".
2. **Hoàng (Benchmark Lead):** Chấm 2 mức (Doc-level vs Content-level) là thước đo thực chất duy nhất để tránh "ảo tưởng kết quả". Đánh giá RAG bắt buộc phải gắn với Grounding & Factuality.
3. **Uyên (Code Lead):** Thiết kế chunking đóng vai trò quyết định: cùng một câu hỏi và cùng một mô hình embedding, chỉ cần thay đổi kích thước và cách cắt chunk là kết quả Top-1 có thể thay đổi hoàn toàn.
4. **Phát (Data Lead):** Quản trị metadata và cơ chế lọc theo đối tượng (`audience`) là chìa khóa để giải quyết bài toán đa đối tượng trong môi trường doanh nghiệp và trường học.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Nhóm sẽ chuẩn hóa dữ liệu đầu vào bằng cách tự động bóc tách và bảo toàn các bảng biểu Markdown (bảng định mức điện nước, bảng khung xử lý kỷ luật) thành các đơn vị không thể chia cắt; đồng thời triển khai cơ chế Hybrid Search kết hợp BM25 và Semantic Caching.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá | Ghi chú |
|----------|-------------------|---------|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 | 6 tài liệu KTX FPT đầy đủ URL nguồn sống 200 OK, chuẩn hóa metadata đa đối tượng |
| Thiết kế chiến lược (Strategy Design) | 15 / 15 | 4 chiến lược rõ nét của 4 thành viên, phân tích baseline định lượng sâu sắc |
| Chất lượng truy xuất (Retrieval Quality) | 10 / 10 | Đánh giá 2 mức chi tiết, đo GAP thổi phồng, A/B Testing chứng minh giá trị filter |
| Thuyết trình (Demo) | 5 / 5 | Phân tích 2 failure cases thực tế, giải pháp Hybrid Search và Soft Filtering |
| **Tổng phần nhóm** | **40 / 40** | **Đầy đủ 100% minh chứng định lượng từ thực nghiệm** |
