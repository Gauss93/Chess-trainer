"""Modeles SQLAlchemy du projet Chess Trainer."""

from datetime import datetime, timezone

from extensions import db


class Game(db.Model):
    """Represente une partie d'echecs persistee en base.

    Le FEN stocke l'etat courant de l'echiquier pour permettre a l'application
    de restaurer une partie depuis la base et de resynchroniser la session web.
    """

    id = db.Column(db.Integer, primary_key=True)
    fen = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    player_color = db.Column(db.String(5), default="white", nullable=False)
    white_time_left = db.Column(db.Integer, default=600, nullable=False)
    black_time_left = db.Column(db.Integer, default=600, nullable=False)
    active_color = db.Column(db.String(5), default="white", nullable=True)
    clock_last_updated_at = db.Column(db.Float, nullable=True)
    is_finished = db.Column(db.Boolean, default=False)
    result = db.Column(db.String(20), nullable=True)

    def __repr__(self):
        """Retourne une representation concise utile au debug.

        Returns:
            str: Identifiant de la partie pour les logs et traces Python.
        """

        return f"<Game {self.id}>"
