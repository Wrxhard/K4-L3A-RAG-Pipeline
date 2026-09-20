# Báo cáo đóng góp cá nhân

## Thông tin

- **Họ và tên:** Nguyễn Văn Huy
- **Mã học viên:** 2A202602428
- **Nhóm:** Sentinel
- **Repository:** https://github.com/Wrxhard/K4-L3A-RAG-Pipeline
- **Nhánh làm việc:** `huy`

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | Bằng chứng trong repository | Trạng thái |
|---|---|---|---|
| Task 3 — Chuẩn hóa dữ liệu sang Markdown | Hoàn thiện luồng chuyển đổi PDF/DOCX và news JSON sang Markdown; kiểm tra schema news; giữ title, URL và ngày crawl; xử lý PDF scan bằng OCR tiếng Việt; ngăn ghi file rỗng và tránh ghi đè các bản OCR đã duyệt | `src/task3_convert_markdown.py`; `data/standardized/legal/`; `data/standardized/news/`; commits `345f32a`, `dee3c0d`, `5006ba4`, `ae24662` | Done |
| Task 3 — Rà soát chất lượng dữ liệu | Đối chiếu và sửa thủ công nội dung Markdown của các tài liệu tuyển sinh bị lỗi OCR; chuẩn hóa lại đầu ra để dùng cho bước chunking | 14 file legal Markdown và 5 file news Markdown; commits `dee3c0d`, `5006ba4`, `ae24662` | Done |
| Task 4 — Chunking và indexing | Hoàn thiện luồng đọc toàn bộ Markdown, giữ title/URL từ Task 3, chia văn bản theo recursive chunking, tạo ID ổn định, embedding/index theo batch và upsert vào ChromaDB cosine; loại bỏ chunk cũ sau khi tài liệu thay đổi | `src/task4_chunking_indexing.py`; `chroma_db/`; `tests/test_contracts.py::test_chunk_documents_preserves_identity_and_metadata`; `tests/test_task4_indexing.py` | Done |

## Quyết định kỹ thuật quan trọng

1. **Dùng OCR tiếng Việt làm fallback cho PDF scan.**
   **Lý do/evidence:** MarkItDown chỉ chuyển đổi tốt khi PDF có text layer. Với tài liệu scan, pipeline render từng trang rồi chạy Tesseract bằng model `vie.traineddata`; các bản đã rà soát được đánh dấu `OCR_REVIEWED` để lần chạy sau không ghi đè.
   **Trade-off:** OCR chậm hơn và vẫn có thể sai ký tự, bảng biểu hoặc xuống dòng, nên các tài liệu quan trọng cần được đối chiếu thủ công với PDF gốc.

2. **Dùng ID chunk ổn định và upsert vào ChromaDB.**
   **Lý do/evidence:** ID có dạng `<document-id>::chunk-<index>`, metadata nguồn và `chunk_index` được giữ xuyên suốt. `upsert` giúp chạy lại indexing mà không tạo thêm bản ghi trùng ID. Chunking hiện dùng `CHUNK_SIZE=500`, `CHUNK_OVERLAP=50` và cosine distance.
   **Trade-off:** Chunk cố định 500 ký tự dễ triển khai và kiểm thử nhưng có thể chia tách một số đoạn văn hoặc bảng dài; tham số cần được đánh giá thêm trên tập câu hỏi thực tế.

## Kiểm thử và kết quả

- Kiểm tra dữ liệu đầu ra hiện có: 14 tài liệu legal Markdown và 5 bài news Markdown; đều đủ số lượng tối thiểu của bài lab.
- Chạy kiểm thử offline cho Task 4 và acceptance: 9/9 test đạt. Các test Task 4 kiểm tra khôi phục title/URL, bỏ file rỗng, embedding theo batch, phát hiện thiếu vector, upsert theo batch, xóa ID cũ và từ chối input rỗng/trùng ID.
- Contract test của Task 4 được thiết kế để kiểm tra chunk không rỗng, ID duy nhất, metadata `source` được giữ, `chunk_index` liên tục và kích thước chunk trong giới hạn cho phép. Trong môi trường hiện tại, chưa thể chạy trọn bộ contract test vì `.venv` thiếu `langchain-text-splitters`, `fpdf2` và `rank-bm25`; cần cài đủ dependency trong `pyproject.toml` trước khi demo.
- Việc dùng ID ổn định kết hợp `collection.upsert(...)` bảo đảm chạy indexing lại không tạo bản ghi trùng theo ID.

## Điều còn hạn chế

- OCR có thể chưa giữ chính xác cấu trúc bảng, công thức và bố cục của PDF scan; một số file cần tiếp tục rà soát thủ công.
- Tôi sẽ thử thêm các cấu hình chunk size/overlap trên golden dataset để chọn tham số dựa trên context recall và context precision thay vì chỉ dùng cấu hình mặc định.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh phần việc Task 3 và Task 4 mà tôi tham gia, và tôi có thể giải thích hoặc chạy lại các bước convert, chunk và index trong buổi demo.

- **Ngày:** 21/09/2026
- **Tên thành viên:** Nguyễn Văn Huy
