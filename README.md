# Guestbook - Lập trình web với Python (Flask)

Ứng dụng sổ lưu bút cho phép xem, thêm và xóa lời nhắn (phạm vi Buổi 1). Lời nhắn được lưu trong một list Python toàn cục, nên dữ liệu sẽ mất khi tắt chương trình.

Repo có hai phiên bản với cùng chức năng:

| | `ban-code-tay/` | `ban-vibecode/` |
|---|---|---|
| Mục tiêu | Dễ đọc, dễ giải thích | Tổ chức như một dự án Flask thực tế, giao diện chỉn chu |
| Cấu trúc | Một file `app.py` | Package `guestbook/` chia thành nhiều module |
| Dữ liệu | List `entries` gồm các dict | List `entries` gồm các `Entry` (dataclass), có lock |
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
├── app.py              # toàn bộ route + list entries
└── templates/          # index.html, add.html
```

Lời nhắn được lưu trong list toàn cục `entries`, mỗi phần tử là một dict `{"id", "name", "message"}`. Biến `next_id` cấp ID tăng dần, nên ID của lời nhắn đã xóa không được dùng lại. Thêm thì `append` vào list, xóa thì duyệt list tìm đúng ID rồi `remove`.

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
│   ├── storage.py      # list entries toàn cục + các hàm thêm/xóa/liệt kê, có lock
│   ├── routes.py       # Blueprint chứa các route
│   ├── static/         # style.css, app.js
│   └── templates/      # base.html, index.html, add.html
└── tests/test_app.py
```

App được tạo bằng hàm `create_app()` và các route nằm trong một Blueprint. `storage.py` giữ list toàn cục `entries` và cấp ID bằng `itertools.count`, nên ID của lời nhắn đã xóa không được dùng lại. Mọi thao tác trên list đều nằm trong `threading.Lock` vì Flask có thể xử lý nhiều request cùng lúc. Test gọi `storage.reset()` trước mỗi test để list luôn bắt đầu rỗng.

Form không cho để trống và giới hạn độ dài tên, lời nhắn. Nếu dữ liệu sai, server trả về mã 400, hiện lại form, giữ nguyên nội dung đã nhập và báo lỗi ngay dưới ô bị sai. Sau khi thêm hoặc xóa, trang chủ hiện thông báo dạng toast (flash message). Jinja tự escape nội dung người dùng nhập, còn JavaScript chỉ gán bằng `textContent`, nên không bị chèn mã HTML/JS.

Giao diện:

- Lời nhắn hiện dạng thẻ xếp so le (masonry), mới nhất trước, avatar màu suy ra từ tên và thời gian dạng "5 phút trước".
- Tìm lời nhắn theo tên hoặc nội dung ngay trên trang (phím `/` để nhảy tới ô tìm kiếm).
- Trang viết lời nhắn có bộ đếm ký tự, khung xem trước cập nhật khi gõ, và `Ctrl + Enter` để gửi.
- Tự theo chế độ sáng/tối của máy, có nút chuyển và nhớ lựa chọn; hiển thị tốt trên điện thoại.
- Khi tắt JavaScript, trang vẫn dùng được đầy đủ: xem, thêm, xóa.

Khi triển khai thật, đặt secret key qua biến môi trường `GUESTBOOK_SECRET_KEY`.

Phiên bản có SQLite và trang thống kê `/stats` (Buổi 2) vẫn còn trong lịch sử git, ở commit `f9156c3`.

## Các route

| Route | Method | Chức năng |
|---|---|---|
| `/` | GET | Hiển thị tất cả lời nhắn |
| `/add` | GET | Hiện form gồm `name` và `message` |
| `/add` | POST | Nếu hợp lệ thì lưu rồi chuyển về `/`, nếu để trống thì hiện lại form kèm thông báo lỗi |
| `/delete/<int:id>` | POST | Xóa lời nhắn theo ID rồi chuyển về `/` |
