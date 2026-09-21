# Individual contribution report

## Thông tin

- Họ và tên: Nguyễn Quốc Đạt
- Mã học viên: `2A202602369`
- Nhóm: K4-L3A
- Repository/branch: `K4-L3A-RAG-Pipeline` / `dat`

## Phần việc đã thực hiện

| Module/deliverable | Việc tôi trực tiếp làm | File/commit/PR | Trạng thái |
|---|---|---|---|
| Task 1 — Legal document collection | Thu thập tài liệu chính sách/pháp lý đầu vào và bổ sung dữ liệu legal cho pipeline | `src/task1_collect_legal_docs.py`; `data/landing/legal/`; commits `eb6f5b4`, `bb920c6` | Done |
| Golden dataset | Đóng góp nội dung câu hỏi, expected answer và expected context cho bộ dữ liệu đánh giá | `group_project/evaluation/golden_dataset.json`; commit `db75be5` | Done |

## Quyết định kỹ thuật quan trọng

1. **Tổ chức tài liệu đầu vào theo nhóm legal trong landing data.**  
   **Lý do/evidence:** Giúp phân biệt tài liệu chính sách/pháp lý với news và giữ nguồn dữ liệu có thể truy vết trong các bước chuẩn hóa, chunking và retrieval.  
   **Trade-off:** Cần duy trì metadata và cấu trúc thư mục nhất quán khi bổ sung tài liệu mới.

2. **Đóng góp các trường expected context cho golden dataset.**  
   **Lý do/evidence:** Cho phép đánh giá không chỉ câu trả lời mà còn khả năng truy xuất đúng ngữ cảnh nguồn.  
   **Trade-off:** Việc rà soát thủ công tốn thời gian nhưng làm kết quả evaluation dễ đối chiếu hơn.

## Kiểm thử và kết quả

- Test hoặc query đã dùng: kiểm tra dữ liệu legal trong `data/landing/legal/`, đối chiếu cấu trúc dữ liệu với `TEAMMATES.md` và golden dataset.
- Kết quả trước/sau: dữ liệu legal được đưa vào repository theo cấu trúc dùng chung của nhóm và có thể tiếp tục qua bước chuẩn hóa.
- Lỗi đã phát hiện và cách xử lý: rà soát nguồn và metadata đầu vào trước khi đưa vào pipeline; các bằng chứng đóng góp được ghi lại bằng file và commit.

## Điều còn hạn chế

- Một hạn chế cụ thể: báo cáo này không bao quát toàn bộ các module retrieval/generation do tôi phụ trách chính phần thu thập legal.
- Nếu có thêm thời gian, thay đổi đầu tiên tôi sẽ thực hiện: bổ sung thêm kiểm tra tự động về chất lượng, độ đầy đủ và khả năng truy xuất nguồn của tài liệu legal.

## Xác nhận đóng góp

Tôi xác nhận nội dung trên phản ánh đúng phần việc của mình và có thể giải thích hoặc chạy lại trong buổi demo.

- Ngày: 2026-09-20
- Tên thành viên: Nguyễn Quốc Đạt
