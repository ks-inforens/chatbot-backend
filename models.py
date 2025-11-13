from db import db
from sqlalchemy.dialects.postgresql import JSONB

class Query(db.Model):
    __tablename__ = "queries"

    id = db.Column(db.BigInteger, primary_key=True)
    asked_at = db.Column(db.TIMESTAMP(timezone=True), server_default=db.func.now(), nullable=False)
    session_id = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Text, nullable=True)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=True)
    model = db.Column(db.Text, nullable=True)
    latency_ms = db.Column(db.Integer, nullable=True)
    success = db.Column(db.Boolean, default=True)
    error = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.Text, nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    thumbs_up = db.Column(db.Boolean, default=False)
    thumbs_down = db.Column(db.Boolean, default=False)
    feedback = db.Column(db.Text, nullable=True)

class CVUpload(db.Model):
    __tablename__ = "cv_uploads"

    id = db.Column(db.BigInteger, primary_key=True)
    uploaded_at = db.Column(db.TIMESTAMP(timezone=True), server_default=db.func.now(), nullable=False)
    session_id = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Text, nullable=True)
    json_response = db.Column(JSONB, nullable=False)