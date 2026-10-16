import json

import pytest

from guestbook import create_app


@pytest.fixture
def app(tmp_path):
    return create_app({
        "TESTING": True,
        "DATA_FILE": tmp_path / "data.json",
        "CHART_FILE": tmp_path / "stats.png",
    })


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
    assert client.get("/add").status_code == 200


def test_add_valid_redirects_and_persists(client, app):
    response = add(client, "An", "Chào cả lớp")
    assert response.status_code == 302
    assert response.headers["Location"] == "/"

    saved = json.loads(app.config["DATA_FILE"].read_text(encoding="utf-8"))
    assert saved[0]["name"] == "An"
    assert saved[0]["message"] == "Chào cả lớp"


@pytest.mark.parametrize("name, message", [("", "abc"), ("An", ""), ("   ", "   ")])
def test_add_rejects_empty_fields(client, name, message):
    response = add(client, name, message)
    assert response.status_code == 400
    assert "Vui lòng nhập đầy đủ" in response.get_data(as_text=True)


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

    page = client.get("/").get_data(as_text=True)
    assert "Bình" in page
    assert ">An<" not in page


def test_delete_missing_id(client):
    response = client.post("/delete/999", follow_redirects=True)
    assert "Không tìm thấy" in response.get_data(as_text=True)


def test_ids_are_not_reused(client, app):
    add(client, "An")
    add(client, "Bình")
    client.post("/delete/2")
    add(client, "Chi")
    saved = json.loads(app.config["DATA_FILE"].read_text(encoding="utf-8"))
    assert [e["id"] for e in saved] == [1, 2]


def test_data_survives_restart(app, client, tmp_path):
    add(client, "An")
    restarted = create_app({"TESTING": True, "DATA_FILE": tmp_path / "data.json",
                            "CHART_FILE": tmp_path / "stats.png"})
    assert "An" in restarted.test_client().get("/").get_data(as_text=True)


def test_corrupted_data_file_starts_empty(tmp_path):
    data_file = tmp_path / "data.json"
    data_file.write_text("{không phải json", encoding="utf-8")
    app = create_app({"TESTING": True, "DATA_FILE": data_file})
    assert app.test_client().get("/").status_code == 200


def test_stats(client, app):
    for name in ["An", "Bình", "An", "Chi", "An", "Bình", "Dũng", "Em", "Giang"]:
        add(client, name)

    response = client.get("/stats")
    page = response.get_data(as_text=True)
    assert response.status_code == 200
    assert '<span class="tile-value">9</span>' in page
    assert page.index("An") < page.index("Bình") < page.index("Chi")
    assert "Giang" not in page.split("Biểu đồ")[0]  # chỉ hiện top 5
    assert app.config["CHART_FILE"].stat().st_size > 0


def test_stats_empty(client, app):
    response = client.get("/stats")
    assert response.status_code == 200
    assert not app.config["CHART_FILE"].exists()
