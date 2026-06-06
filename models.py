from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='user', nullable=False)

class Vocabulary(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(100), nullable=False)
    pronunciation = db.Column(db.String(100)) # Phiên âm
    word_type = db.Column(db.String(50))      # Loại từ (Danh, động, tính...)
    meaning = db.Column(db.String(255), nullable=False)
    example_foreign = db.Column(db.Text)      # Ví dụ tiếng nước ngoài
    example_vietnamese = db.Column(db.Text)   # Dịch nghĩa ví dụ tiếng Việt
    language = db.Column(db.String(50), nullable=False)
    is_memorized = db.Column(db.Boolean, default=False) # True: Đã thuộc, False: Chưa thuộc
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)