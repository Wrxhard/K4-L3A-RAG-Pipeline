# Team Sentinel — Thành viên và phân công

Repository: [K4-L3A-RAG-Pipeline](https://github.com/Wrxhard/K4-L3A-RAG-Pipeline/)

Danh sách dưới đây được tổng hợp từ lịch sử commit, các branch hiện có và template/report đóng góp trong repo. Mã học viên chỉ được điền khi có thông tin xác thực trong report hoặc từ thành viên; không suy đoán từ email Git.

| Họ tên | Mã học viên | Vai trò | Nhánh / phần việc | Bằng chứng trong repo |
|---|---|---|---|---|
| Nguyễn Trọng Phúc | `2A202602552` | Data collection / News crawler | `phuc`; Task 2 — crawl và cập nhật 5 bài news NEU, chuẩn hóa JSON landing | `40554de`, `2205780`, `edb80bd`; `src/task2_crawl_news.py`; `data/landing/news/` |
| Nguyễn Trần Nhựt Nam (`nhut-nam`) | `2A202602981` | Retrieval, indexing và evaluation | `nam`; Task 4, 5, 6, 7, 9, 10; tạo golden dataset và script đánh giá | `1f75145`, `b400bcf`, `db75be5`; `group_project/evaluation/golden_dataset.json`; `evaluate.py` |
| Nguyễn Văn Huy (`HuyHaiThanh`) | `2A202602428` | Document conversion / quality review | `huy`; Task 3 và rà soát, hiệu chỉnh standardized legal Markdown | `345f32a`, `dee3c0d`; `src/task3_convert_markdown.py`; `data/standardized/legal/` |
| Nguyễn Quốc Đạt (`Dat Nguyen Quoc`) | `2A202602369` | Legal document collection | `dat`; Task 1 — thu thập tài liệu chính sách/pháp lý đầu vào | `eb6f5b4`, `bb920c6`; `data/landing/legal/` |

## Ghi chú về golden dataset

Commit `db75be5` của Nguyễn Trần Nhựt Nam thêm `group_project/evaluation/golden_dataset.json`; kiểm tra nội dung commit cho thấy bộ dữ liệu có 15 cases. Việc xây dựng và rà soát nội dung được thực hiện cùng các thành viên trong nhóm, trong đó Nguyễn Trọng Phúc, Nguyễn Hữu Nam, Nguyễn Văn Huy, Nguyễn Quốc Đạt tham gia đóng góp nội dung câu hỏi, expected answer và expected context.

