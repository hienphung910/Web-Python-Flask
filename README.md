# Guestbook - Lập trình web với Python (Flask)

Ứng dụng sổ lưu bút cho phép xem, thêm và xóa lời nhắn. Dữ liệu được lưu vào file JSON, và trang thống kê có biểu đồ vẽ bằng Matplotlib.

Repo có hai phiên bản với cùng chức năng:

| | `ban-code-tay/` | `ban-vibecode/` |
|---|---|---|
| Mục tiêu | Dễ đọc, dễ giải thích | Tổ chức như một dự án Flask thực tế |
| Cấu trúc | Một file `app.py` | Package `guestbook/` chia thành nhiều module |
| Dữ liệu | List toàn cục, lưu vào `data.json` | Lớp `JsonStorage` quản lý list, có lock và ghi file an toàn |
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

## Bản đơn giản

```bash
cd ban-code-tay
python app.py
```

```
ban-code-tay/
├── app.py              # toàn bộ route + đọc/ghi JSON + vẽ biểu đồ
├── data.json           # tự tạo khi thêm lời nhắn đầu tiên
├── static/stats.png    # tự sinh khi mở /stats
└── templates/          # index.html, add.html, stats.html
```

Khi khởi động, `load_data()` đọc dữ liệu từ `data.json`. Sau mỗi lần thêm hoặc xóa, `save_data()` ghi lại file này. Trang `/stats` dùng một dict để đếm số lời nhắn của từng người, sắp xếp giảm dần rồi lấy 5 người đầu.

Cần chạy lệnh từ trong thư mục `ban-code-tay`, vì đường dẫn tới `data.json` và `static/stats.png` là đường dẫn tương đối.

## Bản nâng cao

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
│   ├── storage.py      # JsonStorage: list lời nhắn, lock, ghi file atomic
│   ├── stats.py        # đếm theo người gửi (Counter), vẽ biểu đồ
│   ├── routes.py       # Blueprint chứa các route
│   ├── static/style.css
│   └── templates/      # base.html, index.html, add.html, stats.html
├── instance/data.json  # dữ liệu, tự tạo
└── tests/test_app.py
```

App được tạo bằng hàm `create_app()` và các route nằm trong một Blueprint, nên khi test có thể tạo app với cấu hình riêng (ví dụ file dữ liệu tạm).

Dữ liệu được ghi ra file tạm trước, sau đó `os.replace` mới thay file thật. Nhờ vậy, nếu chương trình bị tắt giữa chừng thì `data.json` cũ vẫn còn nguyên. `JsonStorage` dùng `threading.Lock` để nhiều request thêm hoặc xóa cùng lúc không ghi đè lên nhau. Biểu đồ được vẽ trực tiếp bằng `Figure` thay vì qua `pyplot`, cách này an toàn khi server chạy nhiều thread.

Form không cho để trống và giới hạn độ dài tên, lời nhắn. Nếu dữ liệu sai, server trả về mã 400 và hiện lại form kèm thông báo lỗi. Sau khi thêm hoặc xóa, trang chủ hiện một dòng thông báo (flash message). ID của lời nhắn đã xóa không được dùng lại.

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
