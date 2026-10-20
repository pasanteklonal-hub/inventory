import pytest

from app import create_app


@pytest.mark.parametrize('database_url', [
    'postgres://user:pass@db:5432/mydb',
    'postgresql://user:pass@db:5432/mydb',
])
def test_postgres_urls_use_installed_psycopg2_driver(monkeypatch, database_url):
    monkeypatch.setenv('DATABASE_URL', database_url)

    app = create_app()

    assert app.config['SQLALCHEMY_DATABASE_URI'] == (
        'postgresql+psycopg2://user:pass@db:5432/mydb'
    )
