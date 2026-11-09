"""
Smoke test to verify test environment and basic configuration.
"""

def test_config_loads():
    from app.config import settings
    assert settings.backend_port == 8000
    assert settings.similarity_threshold_strong == 0.75
    assert settings.similarity_threshold_partial == 0.50

def test_database_init():
    from app.db.database import init_db, get_connection
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='analyses'")
    table = cursor.fetchone()
    conn.close()
    assert table is not None
