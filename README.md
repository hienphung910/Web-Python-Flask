# Guestbook: Lập trình web với Python (Flask)

Ứng dụng sổ lưu bút cho phép xem, thêm, xóa lời nhắn và xem thống kê kèm biểu đồ. Cả hai bản đều lưu lời nhắn trong SQLite, đồng thời ghi một bản sao ra file JSON (`data.json`) sau mỗi lần thêm/xóa, nên dữ liệu vẫn còn sau khi tắt chương trình.

Repo có hai phiên bản với cùng chức năng:

| | `ban-code-tay/` | `ban-vibecode/` |
|---|---|---|
| Mục tiêu | Dễ đọc, dễ giải thích | Tổ chức như một dự án Flask thực tế, giao diện chỉn chu |
| Cấu trúc | Một file `app.py` | Package `guestbook/` chia thành nhiều module |
| Dữ liệu | Bảng `entries` trong `guestbook.db` + bản sao `data.json` | Bảng `entries` trong `instance/guestbook.db` + bản sao `instance/data.json`, đọc ra thành `Entry` (dataclass) |
| Biểu đồ `/stats` | Biểu đồ cột Matplotlib mặc định | Biểu đồ cột ngang cùng tông màu trang, có ảnh riêng cho chế độ sáng và tối |
| Giao diện | HTML thuần | CSS + một chút JavaScript: dark mode, tìm kiếm, xem trước, hộp xác nhận xóa, toast |
| Xóa | Chỉ POST | Chỉ POST, hỏi xác nhận trước khi xóa |
| Test | Không có | 24 test pytest |

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
├── app.py              # toàn bộ route + kết nối SQLite + đọc/ghi JSON + vẽ biểu đồ
├── guestbook.db        # tự tạo khi chạy lần đầu (không đưa lên git)
├── data.json           # bản sao JSON, ghi lại sau mỗi lần thêm/xóa (không đưa lên git)
├── static/stats.png    # ảnh biểu đồ, vẽ lại mỗi lần mở /stats (không đưa lên git)
└── templates/          # index.html, add.html, stats.html
```

Lời nhắn được lưu trong bảng `entries (id, name, message)` của file `guestbook.db`. Khi khởi động, `init_db()` tạo bảng nếu chưa có. Cột `id` là `INTEGER PRIMARY KEY AUTOINCREMENT` nên SQLite tự cấp ID tăng dần và không dùng lại ID đã xóa. Thêm dùng `INSERT`, xóa dùng `DELETE ... WHERE id = ?`; dữ liệu người dùng luôn truyền qua dấu `?` để chống SQL injection. Có thể mở `guestbook.db` bằng extension SQLite Viewer của VS Code để xem dữ liệu.

**Lưu file JSON (Buổi 2).** Sau mỗi lần thêm hoặc xóa, `save_json()` đọc toàn bộ bảng rồi ghi ra `data.json` (dùng `ensure_ascii=False` để file giữ nguyên chữ tiếng Việt có dấu). Khi khởi động, `load_json()` kiểm tra: nếu database đang trống mà có `data.json` thì nạp lại toàn bộ lời nhắn từ file, giữ nguyên ID cũ. Vì vậy chỉ cần giữ `data.json` là khôi phục được dữ liệu, kể cả khi xóa mất `guestbook.db`. Sau khi nạp lại, ID mới tiếp tục từ ID lớn nhất có trong file (ID của lời nhắn cuối cùng đã bị xóa trước đó có thể được cấp lại).

**Thống kê `/stats`.** Một câu `SELECT name, COUNT(*) ... GROUP BY name ORDER BY count DESC` đếm số lời nhắn của từng người, sắp từ nhiều đến ít. Tổng số lời nhắn là tổng các số đếm, top 5 là 5 dòng đầu. Biểu đồ cột được vẽ bằng Matplotlib (`matplotlib.use("Agg")` để chỉ vẽ ra file, không mở cửa sổ) và lưu vào `static/stats.png`. Link ảnh có thêm `?v=<thời gian>` để trình duyệt luôn tải ảnh mới thay vì dùng ảnh cũ trong cache.

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
│   ├── models.py       # Entry, SenderStat (dataclass): chữ cái avatar, màu theo tên, thời gian tương đối
│   ├── storage.py      # kết nối SQLite, thêm/xóa/liệt kê/đếm, đồng bộ file JSON
│   ├── charts.py       # vẽ biểu đồ bằng Matplotlib
│   ├── routes.py       # Blueprint chứa các route
│   ├── static/         # style.css, app.js (+ stats.png, stats-dark.png sinh ra khi chạy)
│   └── templates/      # base.html, index.html, add.html, stats.html
├── instance/           # guestbook.db + data.json, tự tạo khi chạy (không đưa lên git)
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

**Lưu file JSON (Buổi 2).** Sau mỗi lần thêm hoặc xóa thành công, `storage` ghi toàn bộ lời nhắn ra `instance/data.json` (đường dẫn trong cấu hình `DATA_FILE`). File được ghi vào một file tạm rồi đổi tên, nên nếu chương trình dừng giữa chừng thì `data.json` cũ vẫn nguyên vẹn. Khi tạo app, nếu bảng còn trống mà có `data.json` thì lời nhắn được nạp lại từ file, giữ nguyên ID và thời gian gửi. Sau khi nạp lại, ID mới tiếp tục từ ID lớn nhất có trong file.

**Thống kê `/stats`.** Nút biểu đồ trên thanh trên cùng mở trang thống kê:

- Ba con số: tổng lời nhắn, số người gửi, số lời nhắn của người gửi nhiều nhất.
- Bảng xếp hạng top 5 người gửi, có avatar cùng màu với trang chủ và tỉ lệ phần trăm.
- Biểu đồ cột ngang vẽ bằng Matplotlib: người gửi nhiều nhất ở trên, số lời nhắn ghi ở đầu mỗi cột. Quá 10 người thì phần còn lại gộp thành cột xám "Khác (n người)".

`charts.py` dùng thẳng `matplotlib.figure.Figure` thay vì `pyplot` nên không phải chọn backend và an toàn khi nhiều request vẽ cùng lúc. Mỗi lần mở `/stats` vẽ hai ảnh nền trong suốt, `stats.png` cho giao diện sáng và `stats-dark.png` cho giao diện tối; CSS hiện ảnh hợp với theme đang dùng. Màu cột trùng màu điểm nhấn của trang và đã kiểm tra đủ tương phản trên cả hai nền. Thư mục lưu ảnh nằm trong cấu hình `CHART_DIR`, nên test ghi ảnh vào thư mục tạm.

## Các route

| Route | Method | Chức năng |
|---|---|---|
| `/` | GET | Hiển thị tất cả lời nhắn |
| `/add` | GET | Hiện form gồm `name` và `message` |
| `/add` | POST | Nếu hợp lệ thì lưu rồi chuyển về `/`, nếu để trống thì hiện lại form kèm thông báo lỗi |
| `/delete/<int:id>` | POST | Xóa lời nhắn theo ID rồi chuyển về `/` |
| `/stats` | GET | Tổng số lời nhắn, top 5 người gửi nhiều nhất và biểu đồ cột số lời nhắn theo người gửi |
