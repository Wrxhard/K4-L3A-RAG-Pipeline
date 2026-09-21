# Giao diện NEU và chatbot

Trang chủ tham khảo bố cục NEU: logo 70 năm, menu trên ảnh nền tràn màn hình,
thanh thông báo xanh/đỏ, thông tin tuyển sinh và nút chat góc phải. Dùng ảnh nền
tĩnh của website gốc để tải nhanh. Đây là bản demo học phần, không phải website
chính thức. Nguồn ảnh được ghi ở `assets/README.md`.

## Chạy trên Windows

Tại thư mục repo, sau khi cài môi trường theo README:

```powershell
.venv\Scripts\python.exe -m streamlit run app.py
```

Mở `http://localhost:8501`. Nhấn **Hỏi đáp tuyển sinh** để vào chat. Có thể truy
cập trực tiếp `http://localhost:8501/?view=chat`.

Giao diện được kiểm tra với Streamlit 1.64.0; dependency tối thiểu được cập nhật
theo phiên bản đã kiểm tra. Không cần Node.js hoặc frontend server riêng.

## Kết nối RAG thật

- Cài đủ dependency của repo: `python -m pip install -e ".[dev]"`.
- Tạo `.env` từ `.env.example`, điền provider/model và API key cần dùng.
- Cấu hình embedding phải khớp model/dimension của Chroma index. Nếu thay model,
  tạo lại index bằng quy trình Task 4 của nhóm trước khi dùng chatbot.
- Khởi động lại Streamlit sau khi đổi cấu hình provider/model.

UI gọi trực tiếp `generate_with_citation()` qua `src/ui_chat.py`. Nếu chưa có key,
trang chủ vẫn hoạt động và chat hiển thị thông báo chưa kết nối. Nếu retrieval
lỗi, UI giữ lại lượt hỏi và hiển thị thông báo lỗi thân thiện, không trả lời giả.
Pipeline hiện trả cùng safe refusal khi thiếu evidence và khi LLM lỗi; UI không
suy diễn hai tình huống này thành một câu trả lời thành công.

## Hành vi hội thoại

- Bốn câu hỏi gợi ý, ô nhập câu hỏi, trạng thái chờ và tùy chọn số chunks.
- Lịch sử và nguồn được giữ khi chuyển trang trong cùng phiên. Tải lại trình
  duyệt có thể tạo phiên mới; dùng **Tải hội thoại (.json)** để lưu bản sao.
- **Cuộc trò chuyện mới** xóa lịch sử trong phiên hiện tại.
- Mỗi câu hỏi được retrieval độc lập theo backend hiện tại; lịch sử UI không
  được tự động đưa vào prompt. Nên ghi rõ năm và đối tượng xét tuyển.
- Expanders `[Document N]` hiển thị đoạn nguồn theo cùng hàm reorder mà Task 10
  dùng để đánh số context. Danh sách `sources` gốc vẫn giữ thứ tự score theo
  contract; `display_sources` chỉ là thứ tự hiển thị của UI.
- URL/tiêu đề news được đối chiếu với JSON landing khi metadata index chỉ có
  tên file. Nguồn legal có tên file và đoạn trích; không tự tạo URL.
- Chi tiết truy xuất hiển thị method, score, ID và thời gian của lượt hỏi.

## Kiểm thử

```powershell
.venv\Scripts\python.exe -m pytest tests/test_ui.py tests/test_acceptance.py -q
```

Kiểm thử UI dùng generation/reorder thật với retrieval và LLM được mock, không
gọi API. Bao gồm giữ lịch sử, reset, rerun không gọi lặp, câu hỏi gợi ý, top_k,
thiếu key, lỗi retrieval và đối chiếu số citation với context.

Kiểm tra trình duyệt (cần Playwright và Chromium):

```powershell
.venv\Scripts\python.exe -m playwright install chromium
.venv\Scripts\python.exe -m streamlit run app.py --server.port 8510
# Trong terminal thứ hai:
.venv\Scripts\python.exe scripts/check_ui_browser.py
```

Script kiểm tra trang chủ/chat ở 375, 768, 1024, 1440px, menu mobile, nút chat,
quay lại trang chủ, ảnh tải được và không tràn ngang. Ảnh chụp lưu tại
`artifacts/neu-ui/` (gitignored).

Kết quả ngày 2026-09-21: 11/11 test UI + acceptance đạt. Kiểm tra trình duyệt
đạt ở bốn kích thước. Chưa xác minh câu trả lời end-to-end với API thật vì môi
trường demo chưa có key và thiếu dependency backend. Các kết quả này không
thay thế bộ contract tests hoặc đánh giá A/B của pipeline.
