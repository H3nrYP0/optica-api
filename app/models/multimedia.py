from app.database import db

class Multimedia(db.Model):
    __tablename__ = 'multimedia'
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    categoria_id = db.Column(db.Integer, nullable=True)
    pedido_id = db.Column(db.Integer, nullable=True)
    tipo = db.Column(db.String(20), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'url': self.url,
            'categoria_id': self.categoria_id,
            'pedido_id': self.pedido_id,
            'tipo': self.tipo
        }