# Guestbook - Lập trình web với Python (Flask)

Ứng dụng sổ lưu bút cho phép xem, thêm và xóa lời nhắn. Cả hai bản đều lưu lời nhắn trong SQLite nên dữ liệu vẫn còn sau khi tắt chương trình.

Repo có hai phiên bản với cùng chức năng:

| | `ban-code-tay/` | `ban-vibecode/` |
|---|---|---|
| Mục tiêu | Dễ đọc, dễ giải thích | Tổ chức như một dự án Flask thực tế, giao diện chỉn chu |
| Cấu trúc | Một file `app.py` | Package `guestbook/` chia thành nhiều module |
| Dữ liệu | Bảng `entries` trong file SQLite `guestbook.db` | Bảng `entries` trong `instance/guestbook.db`, đọc ra thành `Entry` (dataclass) |
| Giao diện | HTML thuần | CSS + một chút JavaScript: dark mode, tìm kiếm, xem trước, hộp xác nhận xóa, toast |
| Xóa | Chỉ POST | Chỉ POST, hỏi xác nhận trước khi xóa |
| Test | Không có | 16 test pytest |

## Cài đặt

Hai bản dùng chung một môi trường ảo:

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
```

## Bản code tay

```bash
cd ban-code-tay
python app.py
```

```
ban-code-tay/
├── app.py              # toàn bộ route + kết nối SQLite
├── guestbook.db        # tự tạo khi chạy lần đầu (không đưa lên git)
└── templates/          # index.html, add.html
```

Lời nhắn được lưu trong bảng `entries (id, name, message)` của file `guestbook.db`. Khi khởi động, `init_db()` tạo bảng nếu chưa có. Cột `id` là `INTEGER PRIMARY KEY AUTOINCREMENT` nên SQLite tự cấp ID tăng dần và không dùng lại ID đã xóa. Thêm dùng `INSERT`, xóa dùng `DELETE ... WHERE id = ?`; dữ liệu người dùng luôn truyền qua dấu `?` để chống SQL injection. Có thể mở `guestbook.db` bằng extension SQLite Viewer của VS Code để xem dữ liệu.

## Bản vibecode

```bash
cd ban-vibecode
python run.py           # chạy web
python -m pytest        # chạy test
```

```
ban-vibecode/
├── run.py
├── pyproject.toml
├── guestbook/
│   ├── __init__.py     # create_app(): application factory, cấu hình
│   ├── models.py       # Entry (dataclass): chữ cái avatar, màu theo tên, thời gian tương đối
│   ├── storage.py      # kết nối SQLite + các hàm thêm/xóa/liệt kê
│   ├── routes.py       # Blueprint chứa các route
│   ├── static/         # style.css, app.js
│   └── templates/      # base.html, index.html, add.html
├── instance/guestbook.db   # tự tạo khi chạy lần đầu (không đưa lên git)
└── tests/test_app.py
```

App được tạo bằng hàm `create_app()` và các route nằm trong một Blueprint. Khi tạo app, `storage.init_app()` tạo bảng `entries (id, name, message, created_at)` nếu chưa có. Mỗi request mở một kết nối SQLite riêng (lưu trong `g`) và đóng khi request kết thúc. Cột `id` dùng `AUTOINCREMENT` nên ID của lời nhắn đã xóa không được dùng lại; dữ liệu người dùng luôn truyền qua dấu `?` để chống SQL injection. Đường dẫn file database nằm trong cấu hình `DATABASE`; mỗi test dùng một file SQLite riêng trong thư mục tạm nên luôn bắt đầu rỗng.

Form không cho để trống và giới hạn độ dài tên, lời nhắn. Nếu dữ liệu sai, server trả về mã 400, hiện lại form, giữ nguyên nội dung đã nhập và báo lỗi ngay dưới ô bị sai. Sau khi thêm hoặc xóa, trang chủ hiện thông báo dạng toast (flash message). Jinja tự escape nội dung người dùng nhập, còn JavaScript chỉ gán bằng `textContent`, nên không bị chèn mã HTML/JS.

Giao diện:

- Lời nhắn hiện dạng thẻ xếp so le (masonry), mới nhất trước, avatar màu suy ra từ tên và thời gian dạng "5 phút trước".
- Tìm lời nhắn theo tên hoặc nội dung ngay trên trang (phím `/` để nhảy tới ô tìm kiếm).
- Trang viết lời nhắn có bộ đếm ký tự, khung xem trước cập nhật khi gõ, và `Ctrl + Enter` để gửi.
- Tự theo chế độ sáng/tối của máy, có nút chuyển và nhớ lựa chọn; hiển thị tốt trên điện thoại.
- Khi tắt JavaScript, trang vẫn dùng được đầy đủ: xem, thêm, xóa.

Khi triển khai thật, đặt secret key qua biến môi trường `GUESTBOOK_SECRET_KEY`.

Phiên bản cũ có thêm trang thống kê `/stats` (Buổi 2) vẫn còn trong lịch sử git, ở commit `f9156c3`.

## Các route

| Route | Method | Chức năng |
|---|---|---|
| `/` | GET | Hiển thị tất cả lời nhắn |
| `/add` | GET | Hiện form gồm `name` và `message` |
| `/add` | POST | Nếu hợp lệ thì lưu rồi chuyển về `/`, nếu để trống thì hiện lại form kèm thông báo lỗi |
| `/delete/<int:id>` | POST | Xóa lời nhắn theo ID rồi chuyển về `/` |
