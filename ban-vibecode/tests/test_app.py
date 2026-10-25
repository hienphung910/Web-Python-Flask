import json
from datetime import datetime, timedelta

import pytest

from guestbook import create_app, storage
from guestbook.charts import fold_tail
from guestbook.models import Entry


def make_app(tmp_path):
    # Mọi file (SQLite, JSON, ảnh biểu đồ) nằm trong thư mục tạm của test
    return create_app({
        "TESTING": True,
        "DATABASE": str(tmp_path / "test.db"),
        "DATA_FILE": str(tmp_path / "data.json"),
        "CHART_DIR": str(tmp_path / "charts"),
    })


@pytest.fixture
def app(tmp_path):
    # Mỗi test bắt đầu với database rỗng
    return make_app(tmp_path)


@pytest.fixture
def client(app):
    return app.test_client()


def add(client, name, message="Xin chào"):
    return client.post("/add", data={"name": name, "message": message})


def saved(app):
    """Các lời nhắn đang có trong database."""
    with app.app_context():
        return storage.list_entries()


def test_index_empty(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Chưa có lời nhắn nào" in response.get_data(as_text=True)


def test_add_shows_form(client):
    page = client.get("/add").get_data(as_text=True)
    assert 'name="name"' in page
    assert 'name="message"' in page


def test_add_valid_redirects_and_saves_to_db(app, client):
    response = add(client, "An", "Chào cả lớp")
    assert response.status_code == 302
    assert response.headers["Location"] == "/"

    entries = saved(app)
    assert len(entries) == 1
    entry = entries[0]
    assert (entry.id, entry.name, entry.message) == (1, "An", "Chào cả lớp")


def test_index_lists_entries_newest_first(client):
    add(client, "An")
    add(client, "Bình")
    page = client.get("/").get_data(as_text=True)
    assert page.index("Bình") < page.index("An")


@pytest.mark.parametrize(
    "name, message, error",
    [
        ("", "abc", "Vui lòng nhập tên"),
        ("An", "", "Vui lòng nhập lời nhắn"),
        ("   ", "   ", "Vui lòng nhập tên"),
    ],
)
def test_add_rejects_empty_fields(app, client, name, message, error):
    response = add(client, name, message)
    assert response.status_code == 400
    assert error in response.get_data(as_text=True)
    assert saved(app) == []


def test_add_keeps_input_after_error(client):
    page = add(client, "An", "").get_data(as_text=True)
    assert 'value="An"' in page


def test_add_rejects_too_long_name(client):
    assert add(client, "x" * 51).status_code == 400


def test_html_is_escaped(client):
    add(client, "Hacker", "<script>alert(1)</script>")
    page = client.get("/").get_data(as_text=True)
    assert "<script>alert(1)</script>" not in page
    assert "&lt;script&gt;" in page


def test_delete(app, client):
    add(client, "An")
    add(client, "Bình")
    assert client.post("/delete/1").status_code == 302
    assert [e.name for e in saved(app)] == ["Bình"]


def test_delete_missing_id(client):
    response = client.post("/delete/999", follow_redirects=True)
    assert "Không tìm thấy" in response.get_data(as_text=True)


def test_delete_requires_post(app, client):
    add(client, "An")
    assert client.get("/delete/1").status_code == 405
    assert len(saved(app)) == 1


def test_ids_are_not_reused(app, client):
    add(client, "An")
    add(client, "Bình")
    client.post("/delete/2")
    add(client, "Chi")
    # id 2 đã xóa không được cấp lại, "Chi" nhận id 3
    assert [e.id for e in saved(app)] == [1, 3]


def test_flash_after_add_and_delete(client):
    page = client.post("/add", data={"name": "An", "message": "hi"}, follow_redirects=True)
    assert "Đã thêm lời nhắn #1" in page.get_data(as_text=True)
    page = client.post("/delete/1", follow_redirects=True)
    assert "Đã xóa lời nhắn #1" in page.get_data(as_text=True)


def test_entry_helpers():
    now = datetime(2026, 10, 20, 12, 0, 0)
    entry = Entry(1, "Nguyễn Văn An", "hi", now - timedelta(minutes=5))
    assert entry.initials == "NA"
    assert Entry(2, "An", "hi").initials == "A"
    assert entry.hue == Entry(3, "nguyễn văn an", "x").hue  # cùng tên thì cùng màu
    assert entry.created_relative(now) == "5 phút trước"
    assert entry.created_relative(now - timedelta(minutes=5)) == "vừa xong"
    assert Entry(4, "An", "hi", datetime(2026, 1, 2, 8, 30)).created_relative(now) == "02/01/2026 08:30"


# ---------- Lưu ra file JSON ----------

def read_json(tmp_path):
    return json.loads((tmp_path / "data.json").read_text(encoding="utf-8"))


def test_json_written_after_add_and_delete(client, tmp_path):
    add(client, "An", "Chào")
    add(client, "Bình")
    assert [(e["id"], e["name"], e["message"]) for e in read_json(tmp_path)] == [
        (1, "An", "Chào"),
        (2, "Bình", "Xin chào"),
    ]
    client.post("/delete/1")
    assert [e["name"] for e in read_json(tmp_path)] == ["Bình"]


def test_json_loaded_on_startup_when_db_is_empty(tmp_path):
    (tmp_path / "data.json").write_text(json.dumps([
        {"id": 3, "name": "An", "message": "Từ file", "created_at": "2026-10-20T08:00:00"},
        {"id": 7, "name": "Chi", "message": "Cũng từ file", "created_at": "2026-10-21T09:30:00"},
    ]), encoding="utf-8")
    app = make_app(tmp_path)
    entries = saved(app)
    assert [(e.id, e.name) for e in entries] == [(3, "An"), (7, "Chi")]
    assert entries[1].created_at == datetime(2026, 10, 21, 9, 30)

    # ID mới tiếp tục sau ID lớn nhất đã nạp
    add(app.test_client(), "Dũng")
    assert saved(app)[-1].id == 8


def test_json_not_loaded_when_db_has_data(tmp_path):
    app = make_app(tmp_path)
    add(app.test_client(), "An")
    (tmp_path / "data.json").write_text("[]", encoding="utf-8")
    assert [e.name for e in saved(make_app(tmp_path))] == ["An"]


# ---------- Thống kê ----------

def test_stats_empty(client, tmp_path):
    page = client.get("/stats").get_data(as_text=True)
    assert "Chưa có gì để thống kê" in page
    assert not (tmp_path / "charts").exists()


def test_stats_total_and_top5(client):
    for name, times in [("An", 3), ("Bình", 1), ("Chi", 2), ("Dũng", 4), ("Hà", 1), ("Giang", 1)]:
        for _ in range(times):
            add(client, name)
    page = client.get("/stats").get_data(as_text=True)
    assert "<dd>12</dd>" in page  # tổng số lời nhắn
    ranking = page[page.index('class="ranking"'):page.index("</ol>")]
    # Nhiều nhất trước, bằng nhau thì theo tên; người thứ 6 (Hà) bị cắt
    order = ["Dũng", "An", "Chi", "Bình", "Giang"]
    assert [ranking.index(f">{name}<") for name in order] == sorted(ranking.index(f">{name}<") for name in order)
    assert ">Hà<" not in ranking


def test_stats_draws_chart_png(client, tmp_path):
    add(client, "An")
    page = client.get("/stats").get_data(as_text=True)
    for filename in ("stats.png", "stats-dark.png"):
        assert (tmp_path / "charts" / filename).read_bytes()[1:4] == b"PNG"
        assert f"/static/{filename}?v=" in page


def test_nav_links_to_stats(client):
    assert 'href="/stats"' in client.get("/").get_data(as_text=True)


def test_fold_tail():
    counts = [(f"Người {i}", 20 - i) for i in range(12)]
    folded = fold_tail(counts, limit=10)
    assert len(folded) == 10
    assert folded[:9] == counts[:9]
    assert folded[-1] == ("Khác (3 người)", 11 + 10 + 9)
    assert fold_tail(counts[:3]) == counts[:3]
