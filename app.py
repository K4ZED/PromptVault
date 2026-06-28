from datetime import datetime

from flask import Flask, flash, redirect, render_template, request, url_for
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config
from models import ContentTask, Prompt, User, db


CATEGORIES = [
    "Foto Model Batik",
    "Video Affiliate",
    "Image to Video",
    "Product Close-up",
    "Studio Fashion",
    "Outdoor Lifestyle",
    "Male Influencer",
    "Female Influencer",
    "Couple Content",
    "Negative Prompt",
    "Other",
]

PLATFORMS = [
    "Gemini",
    "Muller AI",
    "Dreamina",
    "Kling",
    "Runway",
    "Midjourney",
    "ChatGPT",
    "Other",
]

TASK_STATUSES = ["Ide", "Prompt", "Generated", "Revisi", "Selesai", "Uploaded"]
CONTENT_TYPES = ["Image", "Video", "Image to Video", "Storyboard", "Caption"]
ASPECT_RATIOS = ["9:16", "1:1", "16:9", "4:5", "3:4"]
VISUAL_STYLES = ["realistic", "premium fashion", "clean commercial", "documentary style"]


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        raise RuntimeError("DATABASE_URL environment variable is required.")

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "login"
    login_manager.login_message = "Silakan login untuk melanjutkan."
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    with app.app_context():
        db.create_all()

    return app


app = create_app()


def parse_due_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def parse_rating(value):
    try:
        rating = int(value or 0)
    except ValueError:
        return 0
    return max(0, min(rating, 5))


def prompt_query_for_user(prompt_id):
    return Prompt.query.filter_by(id=prompt_id, user_id=current_user.id).first_or_404()


def task_query_for_user(task_id):
    return ContentTask.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()


def build_generated_prompt(form):
    model_labels = {
        "female": "Seorang model wanita dewasa tampil percaya diri",
        "male": "Seorang model pria dewasa tampil percaya diri",
        "couple": "Sepasang model dewasa tampil natural dan percaya diri",
        "none": "Produk batik ditampilkan sebagai fokus utama",
    }
    product_type = form.get("product_type") or "kemeja batik"
    if product_type == "custom":
        product_type = form.get("custom_product") or "produk batik custom"

    location = form.get("location") or "studio"
    if location == "custom":
        location = form.get("custom_location") or "lokasi custom"

    model_text = model_labels.get(form.get("model_type"), model_labels["none"])
    content_style = form.get("content_style") or "affiliate"
    camera_movement = form.get("camera_movement") or "slow push-in"
    duration = form.get("duration") or "15s"
    aspect_ratio = form.get("aspect_ratio") or "9:16"
    visual_style = form.get("visual_style") or "clean commercial"
    selling_point = (form.get("selling_point") or "").strip()
    additional_instruction = (form.get("additional_instruction") or "").strip()

    prompt = (
        f"Buat video {content_style} fashion batik vertikal {aspect_ratio} berdurasi {duration}. "
        f"{model_text} mengenakan {product_type} di {location} dengan pencahayaan hangat dan natural. "
        f"Kamera bergerak {camera_movement} untuk menampilkan motif kain, tekstur, cutting pakaian, "
        "detail jahitan, dan kesan produk yang rapi. "
    )
    if selling_point:
        prompt += f"Tonjolkan selling point: {selling_point}. "
    prompt += (
        f"Visual {visual_style}, profesional, bersih, tanpa teks, tanpa watermark, tanpa logo."
    )
    if additional_instruction:
        prompt += f" Instruksi tambahan: {additional_instruction}."

    negative_prompt = (
        "hindari wajah terlalu AI, tangan aneh, jari berlebih, motif batik berubah, baju rusak, "
        "proporsi tubuh tidak natural, pencahayaan berlebihan, background berantakan, teks, logo, "
        "watermark, blur berlebihan, warna neon, efek glow, gradient."
    )
    return prompt, negative_prompt


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not username or not email or not password:
            flash("Username, email, dan password wajib diisi.", "error")
        elif password != confirm_password:
            flash("Konfirmasi password tidak cocok.", "error")
        elif User.query.filter((User.email == email) | (User.username == username)).first():
            flash("Username atau email sudah terdaftar.", "error")
        else:
            user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password),
            )
            db.session.add(user)
            db.session.commit()
            flash("Akun berhasil dibuat. Silakan login.", "success")
            return redirect(url_for("login"))

    return render_template("auth/register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash("Login berhasil.", "success")
            return redirect(url_for("dashboard"))
        flash("Email atau password salah.", "error")

    return render_template("auth/login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Kamu sudah logout.", "success")
    return redirect(url_for("login"))


@app.route("/")
@login_required
def dashboard():
    prompts = Prompt.query.filter_by(user_id=current_user.id)
    tasks = ContentTask.query.filter_by(user_id=current_user.id)
    top_prompt = prompts.order_by(Prompt.rating.desc(), Prompt.updated_at.desc()).first()
    recent_prompts = prompts.order_by(Prompt.updated_at.desc()).limit(5).all()
    recent_tasks = tasks.order_by(ContentTask.updated_at.desc()).limit(5).all()

    return render_template(
        "dashboard.html",
        total_prompts=prompts.count(),
        total_tasks=tasks.count(),
        completed_tasks=tasks.filter(ContentTask.status.in_(["Selesai", "Uploaded"])).count(),
        top_prompt=top_prompt,
        recent_prompts=recent_prompts,
        recent_tasks=recent_tasks,
    )


@app.route("/prompts")
@login_required
def prompts_index():
    search = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    platform = request.args.get("platform", "").strip()
    query = Prompt.query.filter_by(user_id=current_user.id)

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            (Prompt.title.ilike(pattern))
            | (Prompt.category.ilike(pattern))
            | (Prompt.platform.ilike(pattern))
        )
    if category:
        query = query.filter_by(category=category)
    if platform:
        query = query.filter_by(platform=platform)

    prompts = query.order_by(Prompt.updated_at.desc()).all()
    return render_template(
        "prompts/index.html",
        prompts=prompts,
        categories=CATEGORIES,
        platforms=PLATFORMS,
        search=search,
        selected_category=category,
        selected_platform=platform,
    )


@app.route("/prompts/new", methods=["GET", "POST"])
@login_required
def prompt_new():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        main_prompt = request.form.get("main_prompt", "").strip()
        if not title or not main_prompt:
            flash("Judul dan main prompt wajib diisi.", "error")
        else:
            prompt = Prompt(user_id=current_user.id)
            fill_prompt_from_form(prompt)
            db.session.add(prompt)
            db.session.commit()
            flash("Prompt berhasil ditambahkan.", "success")
            return redirect(url_for("prompt_detail", id=prompt.id))

    return render_template("prompts/form.html", prompt=None, categories=CATEGORIES, platforms=PLATFORMS)


@app.route("/prompts/<int:id>")
@login_required
def prompt_detail(id):
    prompt = prompt_query_for_user(id)
    return render_template("prompts/detail.html", prompt=prompt)


@app.route("/prompts/<int:id>/edit", methods=["GET", "POST"])
@login_required
def prompt_edit(id):
    prompt = prompt_query_for_user(id)
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        main_prompt = request.form.get("main_prompt", "").strip()
        if not title or not main_prompt:
            flash("Judul dan main prompt wajib diisi.", "error")
        else:
            fill_prompt_from_form(prompt)
            db.session.commit()
            flash("Prompt berhasil diperbarui.", "success")
            return redirect(url_for("prompt_detail", id=prompt.id))

    return render_template("prompts/form.html", prompt=prompt, categories=CATEGORIES, platforms=PLATFORMS)


@app.route("/prompts/<int:id>/delete", methods=["POST"])
@login_required
def prompt_delete(id):
    prompt = prompt_query_for_user(id)
    db.session.delete(prompt)
    db.session.commit()
    flash("Prompt berhasil dihapus.", "success")
    return redirect(url_for("prompts_index"))


def fill_prompt_from_form(prompt):
    prompt.title = request.form.get("title", "").strip()
    prompt.category = request.form.get("category", "Other")
    prompt.platform = request.form.get("platform", "Other")
    prompt.main_prompt = request.form.get("main_prompt", "").strip()
    prompt.negative_prompt = request.form.get("negative_prompt", "").strip()
    prompt.aspect_ratio = request.form.get("aspect_ratio", "").strip()
    prompt.visual_style = request.form.get("visual_style", "").strip()
    prompt.rating = parse_rating(request.form.get("rating"))
    prompt.notes = request.form.get("notes", "").strip()


@app.route("/generator", methods=["GET", "POST"])
@login_required
def generator():
    generated_prompt = None
    negative_prompt = None
    form_data = {}
    if request.method == "POST":
        form_data = request.form.to_dict()
        generated_prompt, negative_prompt = build_generated_prompt(request.form)

    return render_template(
        "generator.html",
        generated_prompt=generated_prompt,
        negative_prompt=negative_prompt,
        form_data=form_data,
        categories=CATEGORIES,
        platforms=PLATFORMS,
    )


@app.route("/generator/save", methods=["POST"])
@login_required
def generator_save():
    title = request.form.get("title", "").strip() or "Generated Prompt Batik"
    main_prompt = request.form.get("main_prompt", "").strip()
    if not main_prompt:
        flash("Generate prompt terlebih dahulu sebelum menyimpan.", "error")
        return redirect(url_for("generator"))

    prompt = Prompt(
        user_id=current_user.id,
        title=title,
        category=request.form.get("category", "Video Affiliate"),
        platform=request.form.get("platform", "Other"),
        main_prompt=main_prompt,
        negative_prompt=request.form.get("negative_prompt", "").strip(),
        aspect_ratio=request.form.get("aspect_ratio", "9:16"),
        visual_style=request.form.get("visual_style", "clean commercial"),
        rating=parse_rating(request.form.get("rating")),
        notes=request.form.get("notes", "").strip(),
    )
    db.session.add(prompt)
    db.session.commit()
    flash("Generated prompt berhasil disimpan ke library.", "success")
    return redirect(url_for("prompt_detail", id=prompt.id))


@app.route("/tasks")
@login_required
def tasks_index():
    status = request.args.get("status", "").strip()
    query = ContentTask.query.filter_by(user_id=current_user.id)
    if status:
        query = query.filter_by(status=status)
    tasks = query.order_by(ContentTask.updated_at.desc()).all()
    return render_template("tasks/index.html", tasks=tasks, statuses=TASK_STATUSES, selected_status=status)


@app.route("/tasks/new", methods=["GET", "POST"])
@login_required
def task_new():
    prompts = Prompt.query.filter_by(user_id=current_user.id).order_by(Prompt.title.asc()).all()
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if not title:
            flash("Judul task wajib diisi.", "error")
        else:
            task = ContentTask(user_id=current_user.id)
            fill_task_from_form(task)
            db.session.add(task)
            db.session.commit()
            flash("Task berhasil ditambahkan.", "success")
            return redirect(url_for("tasks_index"))

    return render_template(
        "tasks/form.html",
        task=None,
        prompts=prompts,
        statuses=TASK_STATUSES,
        content_types=CONTENT_TYPES,
        platforms=PLATFORMS,
    )


@app.route("/tasks/<int:id>/edit", methods=["GET", "POST"])
@login_required
def task_edit(id):
    task = task_query_for_user(id)
    prompts = Prompt.query.filter_by(user_id=current_user.id).order_by(Prompt.title.asc()).all()
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        if not title:
            flash("Judul task wajib diisi.", "error")
        else:
            fill_task_from_form(task)
            db.session.commit()
            flash("Task berhasil diperbarui.", "success")
            return redirect(url_for("tasks_index"))

    return render_template(
        "tasks/form.html",
        task=task,
        prompts=prompts,
        statuses=TASK_STATUSES,
        content_types=CONTENT_TYPES,
        platforms=PLATFORMS,
    )


@app.route("/tasks/<int:id>/delete", methods=["POST"])
@login_required
def task_delete(id):
    task = task_query_for_user(id)
    db.session.delete(task)
    db.session.commit()
    flash("Task berhasil dihapus.", "success")
    return redirect(url_for("tasks_index"))


def fill_task_from_form(task):
    prompt_id = request.form.get("prompt_id")
    task.prompt_id = None
    if prompt_id:
        try:
            prompt_id = int(prompt_id)
        except ValueError:
            prompt_id = None
        prompt = Prompt.query.filter_by(id=prompt_id, user_id=current_user.id).first() if prompt_id else None
        task.prompt_id = prompt.id if prompt else None
    task.title = request.form.get("title", "").strip()
    task.content_type = request.form.get("content_type", "Image")
    task.status = request.form.get("status", "Ide")
    task.due_date = parse_due_date(request.form.get("due_date"))
    task.platform = request.form.get("platform", "Other")
    task.notes = request.form.get("notes", "").strip()


@app.context_processor
def inject_options():
    return {
        "categories": CATEGORIES,
        "platforms": PLATFORMS,
        "task_statuses": TASK_STATUSES,
        "content_types": CONTENT_TYPES,
        "aspect_ratios": ASPECT_RATIOS,
        "visual_styles": VISUAL_STYLES,
    }


if __name__ == "__main__":
    app.run(debug=True)
