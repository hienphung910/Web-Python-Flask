# Guestbook - Lập trình web với Python (Flask)

Ứng dụng sổ lưu bút cho phép xem, thêm và xóa lời nhắn.

Repo có hai phiên bản:

| | `ban-code-tay/` | `ban-vibecode/` |
|---|---|---|
| Mục tiêu | Dễ đọc, dễ giải thích | Tổ chức như một dự án Flask thực tế |
| Cấu trúc | Một file `app.py` | Package `guestbook/` chia thành nhiều module |
| Phạm vi | Buổi 1: xem, thêm, xóa | Đầy đủ: thêm trang `/stats` có biểu đồ Matplotlib |
| Dữ liệu | List Python toàn cục, mất khi tắt chương trình | SQLite qua lớp `SqliteStorage`, có lock, file DB nằm trong `instance/` |
| Giao diện | HTML thuần | Template kế thừa từ `base.html`, có CSS và dark mode |
| Xóa | GET hoặc POST | Chỉ POST, hỏi xác nhận trước khi xóa |
| Test | Không có | 15 test pytest |

## Cài đặt

Hai bản dùng chung một môi trường ảo:

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
```

## Cơ sở dữ liệu SQLite

Bản vibecode dùng module `sqlite3` có sẵn trong Python, không cần cài hay cấu hình server. Khi khởi động, app tự tạo file `ban-vibecode/instance/guestbook.db` và bảng `entries` nếu chưa có. File này đã được git ignore. Có thể mở để xem dữ liệu bằng DB Browser for SQLite hoặc một extension SQLite trong VS Code.

Bảng `entries`:

```sql
CREATE TABLE entries (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL,
    message    TEXT NOT NULL,
    created_at TEXT NOT NULL
);
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

Lời nhắn được lưu trong list toàn cục `entries`, mỗi phần tử là một dict `{"id", "name", "message"}`. Biến `next_id` cấp ID tăng dần, nên ID của lời nhắn đã xóa không được dùng lại. Thêm thì `append` vào list, xóa thì duyệt list tìm đúng ID rồi `remove`. Dữ liệu chỉ nằm trong bộ nhớ nên sẽ mất khi tắt chương trình.

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
│   ├── models.py       # Entry (dataclass)
│   ├── storage.py      # SqliteStorage: bảng entries, lock, mỗi thao tác một kết nối
│   ├── stats.py        # đếm theo người gửi (Counter), vẽ biểu đồ
│   ├── routes.py       # Blueprint chứa các route
│   ├── static/style.css
│   └── templates/      # base.html, index.html, add.html, stats.html
├── instance/guestbook.db  # file SQLite, tự sinh khi chạy (git ignore)
└── tests/test_app.py
```

App được tạo bằng hàm `create_app()` và các route nằm trong một Blueprint, nên khi test có thể tạo app với cấu hình riêng (mỗi test dùng một file SQLite mới trong thư mục tạm).

`SqliteStorage` tạo bảng `entries` ngay khi khởi tạo, và mỗi thao tác (`all`, `add`, `delete`) mở một kết nối riêng rồi commit, vì mặc định kết nối `sqlite3` không dùng chung được giữa các thread. `threading.Lock` giữ cho các request thêm hoặc xóa chạy tuần tự. Ảnh biểu đồ được ghi ra file tạm trước rồi `os.replace` thay file thật, nên không bao giờ bị hỏng một nửa. Biểu đồ được vẽ trực tiếp bằng `Figure` thay vì qua `pyplot`, cách này an toàn khi server chạy nhiều thread.

Form không cho để trống và giới hạn độ dài tên, lời nhắn. Nếu dữ liệu sai, server trả về mã 400 và hiện lại form kèm thông báo lỗi. Sau khi thêm hoặc xóa, trang chủ hiện một dòng thông báo (flash message). ID do SQLite cấp bằng `AUTOINCREMENT`, nên ID của lời nhắn đã xóa không được dùng lại.

Khi triển khai thật, đặt secret key qua biến môi trường `GUESTBOOK_SECRET_KEY`.

## Các route

Các route (bản code tay có ba route đầu, bản vibecode có đủ):

| Route | Method | Chức năng |
|---|---|---|
| `/` | GET | Hiển thị tất cả lời nhắn |
| `/add` | GET | Hiện form gồm `name` và `message` |
| `/add` | POST | Nếu hợp lệ thì lưu rồi chuyển về `/`, nếu để trống thì hiện lại form kèm thông báo lỗi |
| `/delete/<int:id>` | POST (bản đơn giản nhận cả GET) | Xóa lời nhắn theo ID rồi chuyển về `/` |
| `/stats` | GET | Tổng số lời nhắn, top 5 người gửi và biểu đồ cột (chỉ bản vibecode) |
