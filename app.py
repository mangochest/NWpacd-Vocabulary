from flask import Flask, render_template, request, redirect, session, flash, jsonify
from models import db, User, Vocabulary
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_

app = Flask(__name__)
app.config["SECRET_KEY"] = "nwpacd"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"

db.init_app(app)

with app.app_context():
    db.create_all()

# TRANG CHỦ (Đã chỉnh sửa theo giao diện pastel)
@app.route("/")
def home():
    return render_template("index.html")

# ĐĂNG KÝ
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        is_first_user = User.query.first() is None
        user_role = 'admin' if is_first_user else 'user'
        user = User(
            username=request.form["username"],
            email=request.form["email"],
            password=generate_password_hash(request.form["password"]),
            role=user_role
        )
        db.session.add(user)
        db.session.commit()
        session["user_id"] = user.id
        session["user_role"] = user.role
        return redirect("/profile")
    return render_template("register.html")

# ĐĂNG NHẬP
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(email=request.form["email"]).first()
        if user and check_password_hash(user.password, request.form["password"]):
            session["user_id"] = user.id
            session["user_role"] = user.role
            return redirect("/profile")
        flash("Email hoặc mật khẩu không chính xác!")
    return render_template("login.html")

# ĐĂNG XUẤT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# XEM DANH SÁCH TỪ VỰNGTHEO NGÔN NGỮ
@app.route("/word")
def words():
    if "user_id" not in session:
        return redirect("/login")

    languages = db.session.query(Vocabulary.language).filter(
        Vocabulary.user_id == session["user_id"]
    ).distinct().all()
    lang_list = [lang[0] for lang in languages]

    selected_lang = request.args.get("lang", "")
    keyword = request.args.get("keyword", "").strip()

    all_words = []
    if selected_lang:
        query = Vocabulary.query.filter(
            Vocabulary.user_id == session["user_id"],
            Vocabulary.language == selected_lang
        )
        if keyword:
            query = query.filter(
                or_(Vocabulary.word.contains(keyword), Vocabulary.meaning.contains(keyword))
            )
        all_words = query.all()

    return render_template(
        "word.html", 
        languages=lang_list, 
        selected_lang=selected_lang, 
        word=all_words, 
        keyword=keyword
    )

# THÊM TỪ VỰNG MỚI (Cập nhật 6 trường dữ liệu)
@app.route("/add", methods=["GET", "POST"])
def add_word():
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        new_word = Vocabulary(
            word=request.form["word"].strip(),
            pronunciation=request.form["pronunciation"].strip(),
            word_type=request.form["word_type"],
            meaning=request.form["meaning"].strip(),
            example_foreign=request.form["example_foreign"].strip(),
            example_vietnamese=request.form["example_vietnamese"].strip(),
            language=request.form["language"].strip(),
            is_memorized=False,
            user_id=session["user_id"]
        )
        db.session.add(new_word)
        db.session.commit()
        flash("Đã thêm từ mới thành công!")
        return redirect(f"/word?lang={new_word.language}")

    return render_template("add_word.html")

# SỬA TỪ VỰNG
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_word(id):
    if "user_id" not in session:
        return redirect("/login")

    word = Vocabulary.query.filter_by(id=id, user_id=session["user_id"]).first()
    if not word:
        flash("Từ vựng không tồn tại!")
        return redirect("/word")

    if request.method == "POST":
        word.word = request.form["word"].strip()
        word.pronunciation = request.form["pronunciation"].strip()
        word.word_type = request.form["word_type"]
        word.meaning = request.form["meaning"].strip()
        word.example_foreign = request.form["example_foreign"].strip()
        word.example_vietnamese = request.form["example_vietnamese"].strip()
        word.language = request.form["language"].strip()
        
        db.session.commit()
        flash("Đã cập nhật từ vựng!")
        return redirect(f"/word?lang={word.language}")

    return render_template("edit_word.html", word=word)

# XÓA MỘT TỪ VỰNG
@app.route("/delete/<int:id>")
def delete_word(id):
    if "user_id" not in session:
        return redirect("/login")

    word = Vocabulary.query.filter_by(id=id, user_id=session["user_id"]).first()
    if not word:
        return redirect("/word")

    lang = word.language
    db.session.delete(word)
    db.session.commit()
    return redirect(f"/word?lang={lang}")

# 4. CHỨC NĂNG XÓA CẢ MỘT BẢNG TỪ VỰNG (NGÔN NGỮ)
@app.route("/delete_language/<string:lang>")
def delete_language(lang):
    if "user_id" not in session:
        return redirect("/login")
        
    # Xóa tất cả các từ thuộc ngôn ngữ được chọn của user hiện tại
    Vocabulary.query.filter_by(user_id=session["user_id"], language=lang).delete()
    db.session.commit()
    flash(f"Đã xóa toàn bộ bảng từ vựng {lang}!")
    return redirect("/word")

# THAY ĐỔI TRẠNG THÁI THUỘC BÀI (API AJAX gọi từ Table / Flashcard)
@app.route("/toggle_memorized/<int:id>", methods=["POST"])
def toggle_memorized(id):
    if "user_id" not in session:
        return jsonify({"status": "error"}), 401
        
    word = Vocabulary.query.filter_by(id=id, user_id=session["user_id"]).first()
    if word:
        word.is_memorized = not word.is_memorized
        db.session.commit()
        return jsonify({"status": "success", "is_memorized": word.is_memorized})
    return jsonify({"status": "not_found"}), 404

# FLASHCARD
@app.route("/flashcard/<string:lang>")
def flashcard(lang):
    if "user_id" not in session:
        return redirect("/login")

    words_list = Vocabulary.query.filter_by(user_id=session["user_id"], language=lang).all()
    if not words_list:
        flash("Không có từ vựng nào để tạo Flashcard!")
        return redirect("/word")

    return render_template("flashcard.html", word=words_list, lang=lang)

# TRANG CÁ NHÂN
@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect("/login")
    user = User.query.get(session["user_id"])
    return render_template("profile.html", user=user)

# ADMIN
@app.route("/admin/dashboard")
def admin_dashboard():
    if "user_id" not in session or session.get("user_role") != "admin":
        return redirect("/")
    all_users = User.query.all()
    return render_template("admin_dashboard.html", users=all_users)

@app.route("/admin/delete_user/<int:user_id>")
def admin_delete_user(user_id):
    if "user_id" not in session or session.get("user_role") != "admin":
        return redirect("/")
    if user_id == session["user_id"]:
        return redirect("/admin/dashboard")
    User.query.filter_by(id=user_id).delete()
    Vocabulary.query.filter_by(user_id=user_id).delete()
    db.session.commit()
    return redirect("/admin/dashboard")

@app.route("/admin/reset_user/<int:user_id>")
def admin_reset_user(user_id):
    if "user_id" not in session or session.get("user_role") != "admin":
        return redirect("/")
    user = User.query.get(user_id)
    if user:
        user.password = generate_password_hash("123456")
        db.session.commit()
    return redirect("/admin/dashboard")

@app.route("/admin/promote_user/<int:user_id>")
def admin_promote_user(user_id):
    if "user_id" not in session or session.get("user_role") != "admin":
        return redirect("/")
    user = User.query.get(user_id)
    if user:
        user.role = 'admin'
        db.session.commit()
    return redirect("/admin/dashboard")

if __name__ == "__main__":
    app.run(debug=True)