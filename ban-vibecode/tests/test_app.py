from datetime import datetime, timedelta

import pytest

from guestbook import create_app, storage
from guestbook.models import Entry


@pytest.fixture
def app():
    # List toàn cục dùng chung cho mọi app, nên phải xóa sạch trước mỗi test
    storage.reset()
    return create_app({"TESTING": True})


@pytest.fixture
def client(app):
    return app.test_client()


def add(client, name, message="Xin chào"):
    return client.post("/add", data={"name": name, "message": message})


def test_index_empty(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Chưa có lời nhắn nào" in response.get_data(as_text=True)


def test_add_shows_form(client):
    page = client.get("/add").get_data(as_text=True)
    assert 'name="name"' in page
    assert 'name="message"' in page


def test_add_valid_redirects_and_saves_to_list(client):
    response = add(client, "An", "Chào cả lớp")
    assert response.status_code == 302
    assert response.headers["Location"] == "/"

    assert len(storage.entries) == 1
    entry = storage.entries[0]
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
def test_add_rejects_empty_fields(client, name, message, error):
    response = add(client, name, message)
    assert response.status_code == 400
    assert error in response.get_data(as_text=True)
    assert storage.entries == []


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


def test_delete(client):
    add(client, "An")
    add(client, "Bình")
    assert client.post("/delete/1").status_code == 302
    assert [e.name for e in storage.entries] == ["Bình"]


def test_delete_missing_id(client):
    response = client.post("/delete/999", follow_redirects=True)
    assert "Không tìm thấy" in response.get_data(as_text=True)


def test_delete_requires_post(client):
    add(client, "An")
    assert client.get("/delete/1").status_code == 405
    assert len(storage.entries) == 1


def test_ids_are_not_reused(client):
    add(client, "An")
    add(client, "Bình")
    client.post("/delete/2")
    add(client, "Chi")
    # id 2 đã xóa không được cấp lại, "Chi" nhận id 3
    assert [e.id for e in storage.entries] == [1, 3]


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
