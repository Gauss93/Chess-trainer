from extensions import db
from datetime import datetime, timezone

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fen = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_finished = db.Column(db.Boolean, default=False)
    result = db.Column(db.String(20), nullable=True)

    def __repr__(self):
        return f"<Game {self.id}>"