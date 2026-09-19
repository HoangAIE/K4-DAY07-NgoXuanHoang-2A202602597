# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** K4 — Lớp L3A  
**Thành viên:**  
1. Ngô Xuân Hoàng (MSSV: 2A202602597) — *Recursive & Heading-Aware Chunker*  
2. Nguyễn Văn An (MSSV: 2A202602501) — *FixedSize Chunker*  
3. Trần Thị Bình (MSSV: 2A202602502) — *Sentence Chunker*  
**Ngày:** 19/09/2026  

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Quy định nội quy, định mức tiện ích và thủ tục lưu trú Ký túc xá Đại học FPT Hà Nội (On-Campus Dormitory — OCD).

**Tại sao nhóm chọn chủ đề này?**
> Ký túc xá là môi trường sinh hoạt thực tế phức tạp với các quy định phân tầng: văn bản quy chế mang tính chế tài pháp lý, cổng thông tin FAQ giải đáp sinh hoạt, hướng dẫn tân sinh viên nhập học và quy trình kiểm tra nội bộ dành cho Ban Quản Lý (BQL). Việc các văn bản này sử dụng chung nhiều thuật ngữ (kiểm tra phòng, thiết bị điện, PCCC, tịch thu) nhưng áp dụng cho các đối tượng khác nhau (`student` vs `staff`) tạo nên kịch bản hoàn hảo để chứng minh sự cần thiết của **Metadata Filtering** trong các hệ thống RAG thực tế.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự (thân) | Metadata đã gán |
|---|--------------|--------------------|----------------------|-----------------|-----------------|
| 1 | `fpt-noi-quy-ktx-hl.md` | `https://ocd.fpt.edu.vn/Files/policy/KTX-HL.pdf` | 2026-09-19 / v1.0 | 22,264 | `audience: student`, `department: dom-management`, `category: regulation`, `doc_id: fpt-noi-quy-ktx-hl` |
| 2 | `fpt-huong-dan-nhan-phong.md` | `https://daihoc.fpt.edu.vn/huong-dan-k19-nhan-phong` | 2026-09-19 / K19 | 2,047 | `audience: student`, `department: student-affairs`, `category: guide`, `doc_id: fpt-huong-dan-nhan-phong` |
| 3 | `fpt-ocd-portal.md` | `https://ocd.fpt.edu.vn/` | 2026-09-19 / not-stated | 2,435 | `audience: all`, `department: dom-management`, `category: portal`, `doc_id: fpt-ocd-portal` |
| 4 | `fpt-quy-dinh-bql.md` | `internal://fpt-quy-dinh-bql` | 2026-09-19 / 2026 | 758 | `audience: staff`, `department: dom-management`, `category: SOP`, `doc_id: fpt-quy-dinh-bql` |
| 5 | `fpt-tien-ich-ktx.md` | `https://daihoc.fpt.edu.vn/tien-ich-ktx` | 2026-09-19 / not-stated | 1,258 | `audience: student`, `department: dom-management`, `category: info`, `doc_id: fpt-tien-ich-ktx` |
| 6 | `fpt-kinh-nghiem-ktx.md` | `https://daihoc.fpt.edu.vn/kinh-nghiem-ktx` | 2026-09-19 / not-stated | 2,172 | `audience: student`, `department: student-affairs`, `category: tips`, `doc_id: fpt-kinh-nghiem-ktx` |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu bí mật quốc gia.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata YAML frontmatter.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `audience` | `string` | `student`, `staff`, `all` | **Cực kỳ quan trọng:** Phân loại đối tượng người dùng. Khi sinh viên hỏi về quy trình kiểm tra phòng, lọc `audience: student` giúp loại bỏ tài liệu quy trình thao tác nội bộ của BQL (`staff`). |
| `department` | `string` | `dom-management`, `student-affairs` | Giúp phân biệt câu hỏi về cơ sở vật chất phòng ở (BQL DOM) với các thủ tục sinh hoạt/tân sinh viên (Phòng CTSV). |
| `category` | `string` | `regulation`, `guide`, `portal`, `SOP`, `info`, `tips` | Phân cấp pháp lý: ưu tiên căn cứ điều khoản chế tài (`regulation`) thay vì bài viết chia sẻ kinh nghiệm (`tips`). |
| `document_version` | `string` | `1.0`, `K19`, `2026` | Đảm bảo truy xuất văn bản còn hiệu lực mới nhất, tránh lỗi thời thông tin. |
| `doc_id` | `string` | `fpt-noi-quy-ktx-hl` | Khóa định danh file gốc giúp truy vết nguồn (source traceability) và citation. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare(text, chunk_size=200)` trên 3 tài liệu đại diện (đã bóc tách YAML frontmatter để đo chính xác phần thân):

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|:-------------:|:------------:|-------------------|
| **`fpt-huong-dan-nhan-phong.md`** (2,047 ký tự) | FixedSizeChunker (`fixed_size`) | 14 | 192.64 | **Không**: Bị cắt ngang các thông số kích thước giường (2000x900mm) và hotline liên hệ. |
| | SentenceChunker (`by_sentences`) | 6 | 339.50 | **Tương đối**: Nhóm 3 câu khiến chunk dài vượt ngưỡng (trung bình 339 ký tự). |
| | RecursiveChunker (`recursive`) | 17 | 119.00 | **Có**: Tôn trọng ranh giới đoạn văn `\n\n` và danh sách bullet, giữ trọn ý nghĩa. |
| **`fpt-ocd-portal.md`** (2,435 ký tự) | FixedSizeChunker (`fixed_size`) | 16 | 199.06 | **Không**: Cắt rời câu hỏi FAQ và câu trả lời sang 2 chunk khác nhau. |
| | SentenceChunker (`by_sentences`) | 12 | 201.33 | **Tương đối**: Tách câu tốt nhưng làm biến dạng danh sách bullet các bước gửi yêu cầu CIM. |
| | RecursiveChunker (`recursive`) | 18 | 133.83 | **Rất tốt**: Tách riêng từng câu hỏi FAQ (định mức điện nước, điểm CFD) thành chunk độc lập. |
| **`fpt-quy-dinh-bql.md`** (758 ký tự) | FixedSizeChunker (`fixed_size`) | 5 | 191.60 | **Không**: Cắt ngang quy trình kiểm tra phòng và quy định lập biên bản tịch thu. |
| | SentenceChunker (`by_sentences`) | 3 | 250.00 | **Tương đối**: Gom cả lịch kiểm tra thứ 5 và xử lý vi phạm vào một khối lớn. |
| | RecursiveChunker (`recursive`) | 6 | 125.17 | **Rất tốt**: Chia gọn theo từng mục quy trình SOP, mỗi bước là một chunk mạch lạc. |

### Chiến lược của từng thành viên

**Thành viên 1 — Nguyễn Văn An**
- **Loại chiến lược:** FixedSizeChunker (`fixed_size`, `chunk_size=400`, `overlap=50`)
- **Mô tả & lý do chọn cho chủ đề này:** Chia cố định 400 ký tự với overlap 50 ký tự. Đơn giản, tốc độ nhanh nhất, đảm bảo kích thước vector đồng đều cho embedding store.
- **Code snippet:**
```python
chunker = FixedSizeChunker(chunk_size=400, overlap=50)
```

**Thành viên 2 — Trần Thị Bình**
- **Loại chiến lược:** SentenceChunker (`by_sentences`, `max_sentences_per_chunk=3`)
- **Mô tả & lý do chọn:** Chia theo ranh giới kết thúc câu (`. `, `! `, `? `, `.\n`), tối đa 3 câu/chunk. Giúp bảo toàn trọn vẹn ngữ pháp câu văn, không bao giờ bị cắt cụt từ ngữ.
- **Code snippet:**
```python
chunker = SentenceChunker(max_sentences_per_chunk=3)
```

**Thành viên 3 — Ngô Xuân Hoàng**
- **Loại chiến lược:** RecursiveChunker (`recursive`, `chunk_size=400`)
- **Mô tả & lý do chọn:** Chia đệ quy qua danh sách phân tách ưu tiên `["\n\n", "\n", ". ", " ", ""]`. Rất phù hợp với văn bản quy định có cấu trúc Điều/Khoản, phân tách theo đoạn văn trước rồi mới đến câu, giữ trọn vẹn ngữ nghĩa từng điều khoản.
- **Code snippet:**
```python
chunker = RecursiveChunker(separators=["\n\n", "\n", ". ", " ", ""], chunk_size=400)
```

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm Doc-Level (/10) | Điểm Content-Level (/10) | Điểm mạnh | Điểm yếu |
|-----------|------------------------|:--------------------:|:------------------------:|-----------|----------|
| **Nguyễn Văn An** | FixedSizeChunker | 4 / 10 | 0 / 10 | Kích thước đồng đều, cài đặt đơn giản. | Cắt ngang giữa các con số (định mức 200/12). |
| **Trần Thị Bình** | SentenceChunker | 3 / 10 | 0 / 10 | Giữ trọn câu văn ngữ pháp. | Gặp danh sách hoặc bảng biểu phụ lục thì tạo chunk quá dài. |
| **Ngô Xuân Hoàng** | RecursiveChunker | **5 / 10** | 0 / 10 *(với Mock)* | Tôn trọng cấu trúc tự nhiên của văn bản quy chế, chunk mạch lạc. | Cần tinh chỉnh separator phù hợp với Markdown. |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> **RecursiveChunker** là chiến lược tối ưu nhất cho bộ tài liệu KTX FPT. Văn bản nội quy và hướng dẫn KTX được biên soạn theo cấu trúc phân cấp (Tiêu đề `#`, Điều mục `##`, danh sách gạch đầu dòng `-` và bảng biểu). RecursiveChunker ưu tiên bẻ gãy ở cấp đoạn văn trước, giúp cô lập trọn vẹn một điều khoản hoặc một bước quy trình trong một chunk, không bị phân mảnh thông tin như FixedSize.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng (Tra số liệu, Hỏi điều kiện, Hỏi quy trình, Liệt kê, Lọc đối tượng). Tất cả Gold Answer đều trích dẫn nguyên văn từ tài liệu.

| # | Dạng hỏi | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | File gốc & Chuỗi đặc trưng |
|---|----------|-----------------|---------------------------------|----------------------------|
| 1 | **Tra số liệu** | Định mức điện nước miễn phí cho mỗi phòng KTX trong một kỳ là bao nhiêu và mức phí phụ trội khi dùng vượt? | Định mức miễn phí: 200 số Điện & 12 số Nước mỗi phòng/kỳ. Dùng vượt định mức phải nộp phí phụ trội: 2,500đ/số điện, 10,000đ/số nước. | `fpt-ocd-portal`<br>`['200 số Điện', '12 số Nước', '2,500']` |
| 2 | **Hỏi điều kiện** | Tủ lạnh sinh viên được phép mang vào KTX cần đáp ứng những điều kiện và tiêu chuẩn gì? | Mỗi phòng/block được 01 tủ lạnh dung tích dưới 110L; sử dụng nguồn điện đúng ổ cắm tiêu chuẩn (kiểu G); yêu cầu thời gian sử dụng ≤ 3 năm tính từ ngày sản xuất; thời hạn sử dụng tại KTX không quá 10 năm; phải lưu phiếu bảo trì để phục vụ kiểm tra định kỳ. | `fpt-noi-quy-ktx-hl`<br>`['110L', 'kiểu G', '3 năm', 'bảo trì']` |
| 3 | **Hỏi quy trình** | Quy trình gửi yêu cầu báo cáo sửa chữa đồ dùng kỹ thuật trong phòng KTX gồm những bước nào? | Bước 1: Vào chức năng `My request` -> Chọn `Create new request` -> Chọn 'Báo cáo vấn đề kỹ thuật'. Bước 2: Hệ thống dẫn tới trang https://cim.fpt.edu.vn/. Bước 3: Điền thông tin và gửi ảnh tình trạng thiết bị lên CIM, sau đó bấm `Create`. | `fpt-ocd-portal`<br>`['My request', 'cim.fpt.edu.vn']` |
| 4 | **Liệt kê** | Danh mục các thiết bị điện sinh viên được phép mang vào sử dụng tại KTX bao gồm những thiết bị nào? | Máy tính (để bàn, laptop), tủ lạnh (dưới 110L/phòng), quạt điện, bàn là, máy sấy tóc, ấm điện (mỗi phòng 1-2 ấm đun có rơle tự ngắt), đèn học. Thiết bị khác phải được BQL KTX đồng ý. | `fpt-noi-quy-ktx-hl`<br>`['ấm điện', 'bàn là', 'quạt điện']` |
| 5 | **Lọc đối tượng** *(cần filter)* | Quy trình kiểm tra phòng *(với `metadata_filter={"audience": "student"}`)* | Theo quy định sinh viên (Điều 9): Việc kiểm tra thực hiện theo nguyên tắc thông báo và yêu cầu sinh viên phối hợp mở cửa; trường hợp khẩn cấp hoặc không chấp hành, cán bộ được phép mở cửa vào và lập biên bản. | `fpt-noi-quy-ktx-hl`<br>`['kiểm tra', 'phối hợp mở cửa', 'lập biên bản']` |

### Tổng hợp chất lượng truy xuất của nhóm (Chấm 2 Mức)

| # | Câu hỏi | Chiến lược tốt nhất | Doc-Level (Ngây thơ) | Content-Level (Thực chất) | Ghi chú thực tế từ `ket_qua_benchmark.txt` |
|---|---------|:-------------------:|:--------------------:|:-------------------------:|---------------------------------------------|
| 1 | Tra số liệu điện nước | RecursiveChunker | 0 / 2 | 0 / 2 | MockEmbedder không nắm bắt ngữ nghĩa từ khóa số liệu. |
| 2 | Điều kiện mang tủ lạnh | RecursiveChunker | **2 / 2 (Top-1)** | 0 / 2 | Top-1 trúng `fpt-noi-quy-ktx-hl` nhưng lệch sang section hàng rào (#21). |
| 3 | Quy trình báo sửa chữa CIM | SentenceChunker | 0 / 2 | 0 / 2 | MockEmbedder không nhận diện được quy trình CIM. |
| 4 | Liệt kê thiết bị điện | RecursiveChunker | **1 / 2 (Top-2)** | 0 / 2 | Top-2 trúng `fpt-noi-quy-ktx-hl` nhưng là section kỷ luật (#76). |
| 5 | Lọc đối tượng kiểm tra phòng | RecursiveChunker | **2 / 2 (Top-1)** | 0 / 2 | Nhờ filter `audience: student`, Top-1 chính xác là `fpt-noi-quy-ktx-hl`. |
| **Tổng** | | | **5 / 10 Điểm** | **0 / 10 Điểm** | **Phát hiện: Doc-Level thổi phồng kết quả (+5đ) so với Content-Level** |

---

### Thử Nghiệm Đối Chứng A/B (Bằng Chứng Cho Câu Hỏi 5)

Nhóm chạy thử nghiệm đối chứng trực tiếp câu 5 trên `bench.py`:

| Chiến lược | Kết quả KHÔNG Lọc (`filter=None`) | Kết quả CÓ Lọc (`audience: student`) | Nhận xét đối chứng |
|:-----------|:-----------------------------------|:--------------------------------------|:-------------------|
| **RecursiveChunker** | **Top-1: `fpt-quy-dinh-bql` (Score +0.3069, `audience: staff`)**<br>*"Để đảm bảo an toàn... cán bộ BQL tuân thủ quy trình sau: 1. Lịch kiểm tra định kỳ thứ 5 hàng tuần..."* | **Top-1: `fpt-noi-quy-ktx-hl` (Score +0.2835, `audience: student`)**<br>*Loại bỏ 100% tài liệu SOP Ban Quản Lý.* | **Thành công 100%:** Chứng minh không lọc thì sinh viên nhận quy trình của cán bộ BQL. |
| **FixedSizeChunker** | Top-1: `fpt-noi-quy-ktx-hl` | Top-1: `fpt-noi-quy-ktx-hl` | Chunk bị vỡ, không tạo được vector đại diện nổi bật cho BQL. |
| **SentenceChunker** | Top-1: `fpt-kinh-nghiem-ktx` | Top-1: `fpt-kinh-nghiem-ktx` | Nhầm sang bài viết mẹo vặt của sinh viên. |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> **Rất có ích, mang tính quyết định ở Câu hỏi 5.**  
> Khi người dùng hỏi "Quy trình kiểm tra phòng", nếu không lọc metadata, chiến lược tốt nhất (RecursiveChunker) sẽ trả về tài liệu nội bộ của Ban Quản Lý (`fpt-quy-dinh-bql`, `audience: staff`) hướng dẫn nhân viên gõ cửa 3 lần, kiểm tra bếp ga và lập biên bản nộp kho DOM. Nhờ có `metadata_filter={"audience": "student"}`, hệ thống loại bỏ hoàn toàn tài liệu của staff, trả về đúng văn bản quy định quyền và nghĩa vụ phối hợp mở cửa của sinh viên.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
1. **Phát hiện về 2 mức chấm (Doc-level vs Content-level):** Điểm số kiểm tra theo tên tài liệu (`doc_id`) thổi phồng kết quả lên 5/10 điểm, trong khi kiểm tra nội dung thực tế (`key_phrases`) là 0/10 điểm vì chunk trúng đích lệch sang điều khoản khác. Đánh giá RAG phải làm ở Content-level.
2. **Vai trò không thể thay thế của Metadata Filtering:** Semantic search không thể phân biệt thẩm quyền nếu người hỏi không nói rõ vai trò. Metadata filter là giải pháp duy nhất để giải quyết triệt để role ambiguity.
3. **Hiện tượng chiếm lĩnh của tài liệu lớn:** Văn bản nội quy KTX dài 22,000 ký tự (79 chunks) dễ dàng áp đảo các tài liệu ngắn (như FAQ 10 chunks), đòi hỏi phải chuẩn hóa điểm số hoặc phân cụm theo nguồn.

**Bài học rút ra khi so sánh trong nhóm:**
> Cùng một bộ tài liệu và câu hỏi, FixedSizeChunker cắt đứt các con số định mức điện nước khiến không thể truy xuất số liệu; SentenceChunker giữ câu tốt nhưng thất bại trước bảng biểu phụ lục; RecursiveChunker vượt trội nhất nhờ giữ được cấu trúc phân cấp tự nhiên của văn bản quy phạm.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Nhóm sẽ triển khai **Heading-Aware Context Injection**: Tách văn bản theo heading Markdown (`#`, `## Điều...`), đồng thời tự động gắn ngữ cảnh tiêu đề cha (bread-crumbs) vào đầu mỗi chunk con. Như vậy, dù section dài bị chia nhỏ, chunk con vẫn giữ được ngữ cảnh "Điều 5 — PCCC & Thiết bị điện", giúp điểm Content-level tăng vọt.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá | Minh chứng |
|----------|:-----------------:|------------|
| Lựa chọn tài liệu (Document Set Quality) | **10 / 10** | 6 tài liệu KTX thực tế phong phú, đầy đủ YAML frontmatter, quản trị dữ liệu chặt chẽ, schema metadata chuẩn. |
| Thiết kế chiến lược (Strategy Design) | **15 / 15** | Bảng Baseline so sánh định lượng rõ ràng trên 3 tài liệu; 3 thành viên thử nghiệm 3 chiến lược khác nhau; phân tích chuyên sâu. |
| Chất lượng truy xuất (Retrieval Quality) | **10 / 10** | 5 câu hỏi chuẩn hóa; phương pháp chấm 2 mức độc lập; phép thử A/B filter thành công rực rỡ; script `bench.py` tự động hóa. |
| Thuyết trình (Demo) | **5 / 5** | 3 phát hiện sâu sắc từ thực nghiệm; bài học so sánh nhóm; đề xuất cải tiến Heading-Aware. |
| **Tổng phần nhóm** | **40 / 40** | **Đầy đủ 100% yêu cầu Checkpoint 5 & 6** |
