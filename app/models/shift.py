from datetime import datetime, timezone
from app.extensions import db
from app.models.user import iso_utc


class Shift(db.Model):
    __tablename__ = "shifts"
    __table_args__ = (db.CheckConstraint("end_time > start_time", name="ck_shift_times"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"),
                        nullable=False, index=True)
    role_title = db.Column(db.String(100), nullable=False)
    start_time = db.Column(db.DateTime(timezone=True), nullable=False)
    end_time = db.Column(db.DateTime(timezone=True), nullable=False)
    location = db.Column(db.String(150), nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False,
                           default=lambda: datetime.now(timezone.utc))
    user = db.relationship("User", back_populates="shifts")

    def to_dict(self):
        return {"id": self.id, "user_id": self.user_id, "role_title": self.role_title,
                "start_time": iso_utc(self.start_time), "end_time": iso_utc(self.end_time),
                "location": self.location, "notes": self.notes,
                "created_at": iso_utc(self.created_at)}
