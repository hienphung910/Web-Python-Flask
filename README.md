# Guestbook - Lập trình web với Python (Flask)

Ứng dụng sổ lưu bút cho phép xem, thêm và xóa lời nhắn. Dữ liệu được lưu trong cơ sở dữ liệu MySQL, và trang thống kê có biểu đồ vẽ bằng Matplotlib.

Repo có hai phiên bản với cùng chức năng:

| | `ban-code-tay/` | `ban-vibecode/` |
|---|---|---|
| Mục tiêu | Dễ đọc, dễ giải thích | Tổ chức như một dự án Flask thực tế |
| Cấu trúc | Một file `app.py` | Package `guestbook/` chia thành nhiều module |
| Dữ liệu | MySQL qua `PyMySQL`, mỗi route tự mở kết nối và chạy SQL | Lớp `MysqlStorage` gói các câu SQL, có lock, cấu hình kết nối qua `instance/config.py` |
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

## Cơ sở dữ liệu MySQL

Cần có MySQL Server đang chạy (ví dụ MySQL 8.0 cài kèm MySQL Workbench). App tự tạo database `guestbook` và bảng `entries` khi khởi động, chỉ cần cung cấp tài khoản kết nối:

| Bản | File cấu hình | Mẫu |
|---|---|---|
| `ban-code-tay/` | `ban-code-tay/db_config.py` | `ban-code-tay/db_config.example.py` |
| `ban-vibecode/` | `ban-vibecode/instance/config.py` | `ban-vibecode/config.example.py` |

Sao chép file mẫu sang đúng tên rồi điền `DB_USER`, `DB_PASSWORD`. Hai file cấu hình thật đã được git ignore nên mật khẩu không bị đưa lên GitHub.

Bảng `entries`:

```sql
CREATE TABLE entries (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(100) NOT NULL,
    message    TEXT NOT NULL,
    created_at DATETIME NOT NULL
);
```

## Bản code tay

```bash
cd ban-code-tay
python app.py
```

```
ban-code-tay/
├── app.py              # toàn bộ route + truy vấn MySQL + vẽ biểu đồ
├── db_config.py        # tài khoản MySQL (git ignore), tạo từ db_config.example.py
├── static/stats.png    # tự sinh khi mở /stats
└── templates/          # index.html, add.html, stats.html
```

Khi khởi động, `init_db()` tạo database và bảng `entries(id, name, message, created_at)` nếu chưa có. Mỗi route mở kết nối bằng `get_db()` rồi chạy câu SQL tương ứng: `SELECT` để liệt kê, `INSERT` để thêm (ID do MySQL tự tăng), `DELETE ... WHERE id = %s` để xóa. `%s` là tham số truyền vào, giúp tránh SQL injection. Trang `/stats` dùng một dict để đếm số lời nhắn của từng người, sắp xếp giảm dần rồi lấy 5 người đầu.

Cần chạy lệnh từ trong thư mục `ban-code-tay`, vì `db_config.py` được import theo thư mục hiện tại và `static/stats.png` là đường dẫn tương đối.

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
│   ├── storage.py      # MysqlStorage: bảng entries, lock, mỗi thao tác một kết nối
│   ├── stats.py        # đếm theo người gửi (Counter), vẽ biểu đồ
│   ├── routes.py       # Blueprint chứa các route
│   ├── static/style.css
│   └── templates/      # base.html, index.html, add.html, stats.html
├── config.example.py   # mẫu cấu hình, sao chép thành instance/config.py
├── instance/config.py  # tài khoản MySQL của máy này (git ignore)
└── tests/test_app.py
```

App được tạo bằng hàm `create_app()` và các route nằm trong một Blueprint, nên khi test có thể tạo app với cấu hình riêng (test dùng database `guestbook_test` và xóa sạch bảng trước mỗi test).

`MysqlStorage` tạo database và bảng `entries` ngay khi khởi tạo, và mỗi thao tác (`all`, `add`, `delete`) mở một kết nối riêng rồi commit, vì kết nối PyMySQL không dùng chung được giữa các thread. `threading.Lock` giữ cho các request thêm hoặc xóa chạy tuần tự. Ảnh biểu đồ được ghi ra file tạm trước rồi `os.replace` thay file thật, nên không bao giờ bị hỏng một nửa. Biểu đồ được vẽ trực tiếp bằng `Figure` thay vì qua `pyplot`, cách này an toàn khi server chạy nhiều thread.

Form không cho để trống và giới hạn độ dài tên, lời nhắn. Nếu dữ liệu sai, server trả về mã 400 và hiện lại form kèm thông báo lỗi. Sau khi thêm hoặc xóa, trang chủ hiện một dòng thông báo (flash message). ID do MySQL cấp bằng `AUTO_INCREMENT`, nên ID của lời nhắn đã xóa không được dùng lại.

Khi triển khai thật, đặt secret key qua biến môi trường `GUESTBOOK_SECRET_KEY`.

## Các route

Cả hai bản có cùng các route:

| Route | Method | Chức năng |
|---|---|---|
| `/` | GET | Hiển thị tất cả lời nhắn |
| `/add` | GET | Hiện form gồm `name` và `message` |
| `/add` | POST | Nếu hợp lệ thì lưu rồi chuyển về `/`, nếu để trống thì hiện lại form kèm thông báo lỗi |
| `/delete/<int:id>` | POST (bản đơn giản nhận cả GET) | Xóa lời nhắn theo ID rồi chuyển về `/` |
| `/stats` | GET | Tổng số lời nhắn, top 5 người gửi và biểu đồ cột |
