import os


class Config:
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
    MAX_CONTENT_LENGTH = 1024 * 1024


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True


class ProductionConfig(Config):
    DEBUG = False


config_by_name = {
    "default": DevelopmentConfig,
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def environment_config(name):
    database_url = os.getenv("DATABASE_URL", "sqlite:///shifts_dev.db")
    for prefix in ("postgres://", "postgresql://"):
        if database_url.startswith(prefix):
            database_url = database_url.replace(prefix, "postgresql+psycopg://", 1)
    secret = os.getenv("JWT_SECRET", "")
    if name != "testing" and (len(secret) < 32 or secret.startswith("replace-")):
        raise ValueError("Set JWT_SECRET to a random secret with at least 32 characters.")
    if name == "production" and not os.getenv("DATABASE_URL"):
        raise ValueError("Production requires DATABASE_URL.")
    lifetime = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_SECONDS", "3600"))
    if lifetime < 1:
        raise ValueError("JWT lifetime must be positive.")
    return {
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:" if name == "testing" else database_url,
        "JWT_SECRET": secret or "testing-secret-that-is-at-least-32-characters",
        "JWT_ACCESS_TOKEN_EXPIRES_SECONDS": lifetime,
        "APP_NAME": os.getenv("APP_NAME", "Shift Manager"),
    }
