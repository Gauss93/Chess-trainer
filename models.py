"""Modeles SQLAlchemy du projet Chess Trainer."""

from datetime import datetime, timezone

from extensions import db


class Game(db.Model):
    """Represente une partie d'echecs persistee en base.

    Le FEN stocke l'etat courant de l'echiquier. Les champs de chrono gardent
    le temps restant pour chaque joueur afin qu'une partie rapide survive a un
    rafraichissement de page ou a une reprise de session.
    """

    id = db.Column(db.Integer, primary_key=True)
    fen = db.Column(db.String(120), nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    is_finished = db.Column(db.Boolean, default=False)
    result = db.Column(db.String(20), nullable=True)
    white_time_left = db.Column(db.Integer, nullable=False, default=600)
    black_time_left = db.Column(db.Integer, nullable=False, default=600)
    last_move_at = db.Column(db.DateTime(timezone=True), nullable=True)
    time_control_minutes = db.Column(db.Integer, nullable=False, default=10)

    def __repr__(self):
        """Retourne une representation concise utile au debug.

        Returns:
            str: Identifiant de la partie pour les logs et traces Python.
        """

        return f"<Game {self.id}>"
