# Individual contribution report

## Thông tin

- Họ và tên: Nguyễn Trọng Phúc
- Mã học viên: 2A202602552
- Nhóm: Sentinel
- Repository/branch: https://github.com/Wrxhard/K4-L3A-RAG-Pipeline/tree/phuc— `phuc`

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Task 2 — Crawl news | Xây dựng crawler lấy bài viết tuyển sinh NEU, lưu từng bài thành JSON với `url`, `title`, `date_crawled`, `content_markdown`; bổ sung xử lý lỗi theo từng URL | `src/task2_crawl_news.py`, `data/landing/news/`, commit `40554de` | Done |
| Cập nhật corpus news | Rà soát và cập nhật các URL nguồn, crawl lại 5 bài news và cập nhật dữ liệu landing | `src/task2_crawl_news.py`, `data/landing/news/article_01.json`–`article_05.json`, commits `2205780`, `edb80bd` | Done |
| Golden dataset | Phối hợp cùng Nguyễn Hữu Nam, Nguyễn Văn Huy và Nguyễn Quốc Đạt xây dựng/rà soát 15 câu hỏi cùng `expected_answer` và `expected_context` | `group_project/evaluation/golden_dataset.json`, commit nhóm `db75be5` | Done |
| Evaluation / A-B review | Tham gia chạy và rà soát kết quả đánh giá trên 15 golden cases, đối chiếu dense-only với hybrid + RRF | `group_project/evaluation/RESULT.md`, `evaluate.py` | Done |

## Quyết định kỹ thuật quan trọng

1. **Dùng BeautifulSoup kết hợp requests cho crawler.**  
   **Lý do/evidence:** phù hợp với bài viết HTML công khai, dễ kiểm thử bằng fixture HTML và không yêu cầu browser runtime trong luồng cơ bản. Crawler ưu tiên `article`, sau đó fallback về `main` hoặc `body`.  
   **Trade-off:** không xử lý được nội dung chỉ xuất hiện sau JavaScript, nhưng đơn giản và ổn định hơn cho corpus hiện tại.

2. **Chuẩn hóa mỗi bài news thành một JSON có metadata đầy đủ.**  
   **Lý do/evidence:** acceptance test yêu cầu `url`, `title`, `date_crawled` và `content_markdown`; metadata nguồn giúp Task 3 và phần citation truy ngược về bài gốc.  
   **Trade-off:** giữ nội dung dạng text/Markdown tối giản, không bảo toàn toàn bộ layout hoặc hình ảnh của trang.

## Kiểm thử và kết quả

- Chạy `pytest tests/test_crawl_news.py -q`: 3 test pass.
- Kiểm tra 5 JSON trong `data/landing/news/`: đủ metadata bắt buộc và nội dung không rỗng.
- Các commit chính: `40554de`, `2205780`, `edb80bd`.
- Golden dataset của nhóm có 15 cases, được dùng chung cho đánh giá retrieval/generation.
- Theo `group_project/evaluation/RESULT.md`, Config B (hybrid + RRF) đạt average `0.91`, cao hơn Config A (dense-only) `0.84`; context recall tăng từ `0.60` lên `0.72` và context precision từ `0.83` lên `0.97`.
- Kết quả này được dùng để thống nhất chọn hybrid + RRF làm chiến lược retrieval mặc định của nhóm.

## Điều còn hạn chế

- Crawler phụ thuộc khả năng truy cập HTTPS của môi trường; khi CA bundle lỗi cần cấu hình riêng cho môi trường chạy, không nên tắt TLS verification trong production.
- Khi chính sách tuyển sinh hoặc corpus thay đổi, cần rà soát lại URL và expected context của golden dataset.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 20/09/2026
- Tên thành viên: Nguyễn Trọng Phúc
