from datetime import datetime, timezone
from app.extensions import db


def iso_utc(value):
    # SQLite drops timezone information. All stored times are UTC.
    return value.replace(tzinfo=timezone.utc).isoformat()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100))
    role = db.Column(db.String(50), nullable=False, default="user", server_default="user")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False,
                           default=lambda: datetime.now(timezone.utc))
    shifts = db.relationship("Shift", back_populates="user", cascade="all, delete-orphan",
                             passive_deletes=True)

    def to_dict(self):
        return {"id": self.id, "email": self.email, "full_name": self.full_name,
                "created_at": iso_utc(self.created_at)}
