from pathlib import Path


def test_app_no_concentra_esquema_sql_o_conexiones_sqlite():
    app_source = (Path(__file__).parents[1] / "app.py").read_text(
        encoding="utf-8"
    )

    assert "CREATE TABLE" not in app_source
    assert "sqlite3.connect" not in app_source
