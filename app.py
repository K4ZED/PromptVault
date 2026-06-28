import re
import secrets
import time
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for
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
GENERATOR_OUTPUT_TYPES = ["Video Affiliate", "Image Prompt", "Image to Video", "Product Photo", "Service Ad"]
GENERATOR_PRODUCT_DOMAINS = ["Batik Fashion", "Gadget Product", "Gadget Service"]
GENERATOR_MODEL_TYPES = [
    "female_influencer",
    "male_influencer",
    "couple_influencers",
    "hand_model",
    "tech_reviewer",
    "technician",
    "customer",
    "none",
]
GENERATOR_PRODUCT_TYPES = ["kemeja batik", "blouse batik", "dress batik", "outer batik", "kain batik", "custom"]
GENERATOR_GADGET_TYPES = ["iPhone", "iPad", "MacBook", "Apple Watch", "AirPods", "Android phone", "Android tablet", "Windows laptop", "custom"]
GENERATOR_GADGET_BRANDS = ["Apple", "Samsung", "Xiaomi", "OPPO", "vivo", "ASUS", "Lenovo", "HP", "Dell", "Other"]
GENERATOR_SERVICE_TYPES = [
    "screen replacement",
    "battery replacement",
    "camera repair",
    "speaker or microphone repair",
    "charging port repair",
    "software troubleshooting",
    "data backup and transfer",
    "cleaning and maintenance",
    "diagnostic check",
    "custom",
]
GENERATOR_GADGET_CONDITIONS = ["brand new", "like new", "pre-owned excellent condition", "minor wear", "damaged before repair", "after repair"]
GENERATOR_DELIVERY_MODES = ["silent_showcase", "talking_script"]
GENERATOR_PROMOTION_INTENTS = ["affiliate", "semi_affiliate", "showcase_only"]
GENERATOR_WEAR_MODES = ["worn_by_talent", "not_worn_product_display", "auto"]
GENERATOR_LOCATIONS = ["studio", "living room", "outdoor", "boutique", "office", "custom"]
GENERATOR_PLACE_REFERENCES = [
    "minimalist warm studio",
    "Jakarta apartment living room",
    "Yogyakarta heritage boutique",
    "artisan batik workshop",
    "modern office lobby",
    "tropical outdoor walkway",
    "premium fashion fitting room",
    "clean marketplace product corner",
    "Apple-style clean tech desk",
    "premium gadget showroom",
    "trusted repair service counter",
    "technician workbench",
    "modern phone accessories shop",
    "resort corridor with natural light",
    "custom",
]
GENERATOR_PLACE_REFERENCE_DETAILS = {
    "minimalist warm studio": "a minimalist warm-toned studio with neutral walls, simple props, soft shadows, and a clean commercial fashion setup",
    "Jakarta apartment living room": "a modern Jakarta apartment living room with warm wood furniture, tidy decor, soft window light, and a relatable premium home atmosphere",
    "Yogyakarta heritage boutique": "a Yogyakarta-inspired heritage boutique with subtle wooden accents, handcrafted decor, muted earthy colors, and an elegant Indonesian fashion retail mood",
    "artisan batik workshop": "an artisan batik workshop atmosphere with tidy fabric rolls, wooden tables, handcrafted textile details, and a refined behind-the-scenes production feel",
    "modern office lobby": "a polished modern office lobby with clean lines, muted warm surfaces, natural light, and a professional daily-wear context",
    "tropical outdoor walkway": "a tropical outdoor walkway with greenery, soft daylight, warm stone or wood textures, and a relaxed lifestyle fashion mood",
    "premium fashion fitting room": "a premium fashion fitting room with a full-length mirror, warm boutique lighting, clean walls, and a curated styling environment",
    "clean marketplace product corner": "a clean marketplace product corner with a neutral backdrop, tidy product display, soft shadow, and clear e-commerce product visibility",
    "Apple-style clean tech desk": "a minimalist Apple-style tech desk with a neutral background, clean surface, soft reflections, tidy cable management, and premium product presentation",
    "premium gadget showroom": "a premium gadget showroom with clean display tables, warm professional lighting, organized accessories, and a trustworthy retail atmosphere",
    "trusted repair service counter": "a trusted gadget repair service counter with organized tools, clean documentation, device trays, and a professional customer-service atmosphere",
    "technician workbench": "a neat technician workbench with precision tools, anti-static mat, soft task lighting, and a credible repair workflow",
    "modern phone accessories shop": "a modern phone accessories shop with tidy shelves, neutral display lighting, phone cases, chargers, and a clean retail setup",
    "resort corridor with natural light": "a resort corridor with natural light, warm architectural details, calm premium travel mood, and an elegant lifestyle setting",
}
GENERATOR_CONTENT_STYLES = ["affiliate", "cinematic", "casual", "premium", "product showcase", "editorial", "UGC testimonial"]
GENERATOR_CAMERA_MOVEMENTS = ["static", "slow push-in", "zoom in", "handheld", "orbit", "tracking shot"]
GENERATOR_DURATIONS = ["6s", "10s", "15s", "30s"]
GENERATOR_FRAMINGS = ["medium shot", "close-up", "full body", "detail macro", "medium to close-up", "wide establishing shot", "over-the-shoulder shot"]
GENERATOR_LIGHTINGS = ["soft warm natural light", "clean studio lighting", "window light", "premium boutique lighting", "soft morning light", "controlled commercial lighting"]
GENERATOR_MOODS = ["confident", "natural and friendly", "elegant", "premium minimal", "warm and relatable", "calm luxury", "fresh daily wear"]
GENERATOR_ACTIONS = [
    "adjusting the sleeves while showing the batik pattern",
    "walking slowly, then stopping and facing the camera",
    "touching the fabric detail and turning slightly",
    "posing naturally while showing the garment cut",
    "keeping the product still with a smooth transition into motif details",
    "holding the collar and smoothing the front panel",
    "showing before-and-after styling angles",
    "placing the product neatly on a hanger or display stand",
    "showing the product clearly with a clean commercial angle",
    "rotating the gadget slowly to show the screen, frame, camera, and ports",
    "showing the device in hand with a clean lifestyle angle",
    "placing the gadget on a clean desk beside its accessories",
    "a technician carefully inspecting the device with professional tools",
    "showing a before-and-after repair result with the device working normally",
]
GENERATOR_DETAIL_FOCUS = [
    "batik motif",
    "fabric texture",
    "garment cut",
    "stitching detail",
    "body fit",
    "product color",
    "collar shape",
    "sleeve detail",
    "fabric drape",
    "screen clarity",
    "camera module",
    "device frame",
    "ports and buttons",
    "keyboard and trackpad",
    "accessories",
    "repair tools",
    "before-after condition",
]
GENERATOR_QUALITY_LEVELS = ["clean commercial", "premium fashion campaign", "high-converting affiliate creative", "realistic marketplace visual", "cinematic social ad"]
GENERATOR_PRODUCT_TRANSLATIONS = {
    "kemeja batik": "premium batik shirt",
    "blouse batik": "premium batik blouse",
    "dress batik": "premium batik dress",
    "outer batik": "premium batik outerwear",
    "kain batik": "batik fabric",
}
GENERATOR_DOMAIN_DETAIL_DEFAULTS = {
    "Batik Fashion": ["batik motif", "fabric texture", "garment cut"],
    "Gadget Product": ["screen clarity", "device frame", "camera module"],
    "Gadget Service": ["repair tools", "before-after condition", "ports and buttons"],
}
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
LOGIN_ATTEMPTS = {}
LOGIN_LIMIT = 5
LOGIN_WINDOW_SECONDS = 15 * 60


def clean_text(value, max_length):
    return (value or "").strip()[:max_length]


def choice_or_default(value, allowed, default):
    return value if value in allowed else default


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        raise RuntimeError("DATABASE_URL environment variable is required.")
    if not app.config.get("SECRET_KEY"):
        raise RuntimeError("SECRET_KEY environment variable is required.")

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "login"
    login_manager.login_message = "Silakan login untuk melanjutkan."
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @app.before_request
    def protect_state_changing_requests():
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            submitted_token = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token")
            if not submitted_token or not secrets.compare_digest(submitted_token, get_csrf_token()):
                abort(400)

    @app.after_request
    def add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        return response

    if app.config.get("AUTO_CREATE_TABLES"):
        with app.app_context():
            db.create_all()

    return app


app = create_app()


def get_csrf_token():
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token


def login_rate_key():
    return f"{request.remote_addr or 'unknown'}:{clean_text(request.form.get('email'), 120).lower()}"


def login_is_limited():
    key = login_rate_key()
    now = time.time()
    attempts = [ts for ts in LOGIN_ATTEMPTS.get(key, []) if now - ts < LOGIN_WINDOW_SECONDS]
    LOGIN_ATTEMPTS[key] = attempts
    return len(attempts) >= LOGIN_LIMIT


def record_failed_login():
    key = login_rate_key()
    now = time.time()
    LOGIN_ATTEMPTS[key] = [ts for ts in LOGIN_ATTEMPTS.get(key, []) if now - ts < LOGIN_WINDOW_SECONDS] + [now]


def clear_failed_logins():
    LOGIN_ATTEMPTS.pop(login_rate_key(), None)


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


def get_app_timezone():
    try:
        return ZoneInfo(app.config.get("APP_TIMEZONE", "Asia/Jakarta"))
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")


def today_bounds_utc_naive():
    app_timezone = get_app_timezone()
    start_local = datetime.now(app_timezone).replace(hour=0, minute=0, second=0, microsecond=0)
    end_local = start_local + timedelta(days=1)
    start_utc = start_local.astimezone(timezone.utc).replace(tzinfo=None)
    end_utc = end_local.astimezone(timezone.utc).replace(tzinfo=None)
    return start_utc, end_utc


def reset_old_tasks_for_current_user(show_flash=False):
    if not current_user.is_authenticated or not app.config.get("RESET_CONTENT_TASKS_DAILY"):
        return 0

    today_start_utc, _ = today_bounds_utc_naive()
    deleted_count = ContentTask.query.filter(
        ContentTask.user_id == current_user.id,
        ContentTask.created_at < today_start_utc,
    ).delete(synchronize_session=False)

    if deleted_count:
        db.session.commit()
        if show_flash:
            flash(f"{deleted_count} task lama sudah di-reset untuk hari ini.", "success")
    return deleted_count


def build_generated_prompt(form):
    model_labels = {
        "female_influencer": "an adult female influencer with a confident, friendly, natural on-camera presence",
        "male_influencer": "an adult male influencer with a confident, friendly, natural on-camera presence",
        "couple_influencers": "a stylish adult couple acting as lifestyle influencers with natural chemistry",
        "hand_model": "a clean hand model presenting the product with careful, premium hand movements",
        "tech_reviewer": "a trustworthy tech reviewer presenting the device naturally, as if making a short social commerce review",
        "technician": "a professional technician demonstrating the service process with clean, careful, trustworthy handling",
        "customer": "a satisfied customer receiving or testing the product/service with a natural testimonial expression",
        "none": "the product or service result as the main subject without a human model",
    }
    output_type = choice_or_default(form.get("output_type"), GENERATOR_OUTPUT_TYPES, "Video Affiliate")
    product_domain = choice_or_default(form.get("product_domain"), GENERATOR_PRODUCT_DOMAINS, "Batik Fashion")
    promotion_intent = choice_or_default(form.get("promotion_intent"), GENERATOR_PROMOTION_INTENTS, "affiliate")
    wear_mode = choice_or_default(form.get("wear_mode"), GENERATOR_WEAR_MODES, "auto")
    product_type = choice_or_default(form.get("product_type"), GENERATOR_PRODUCT_TYPES, "kemeja batik")
    gadget_type = choice_or_default(form.get("gadget_type"), GENERATOR_GADGET_TYPES, "iPhone")
    gadget_brand = choice_or_default(form.get("gadget_brand"), GENERATOR_GADGET_BRANDS, "Apple")
    service_type = choice_or_default(form.get("service_type"), GENERATOR_SERVICE_TYPES, "screen replacement")
    gadget_condition = choice_or_default(form.get("gadget_condition"), GENERATOR_GADGET_CONDITIONS, "like new")
    custom_product = clean_text(form.get("custom_product"), 120)
    custom_gadget = clean_text(form.get("custom_gadget"), 120)
    custom_service = clean_text(form.get("custom_service"), 100)
    model_type_default = {
        "Batik Fashion": "female_influencer",
        "Gadget Product": "tech_reviewer",
        "Gadget Service": "technician",
    }.get(product_domain, "female_influencer")
    model_type = choice_or_default(form.get("model_type"), GENERATOR_MODEL_TYPES, model_type_default)
    model_text = model_labels.get(model_type, model_labels[model_type_default])
    intent_labels = {
        "affiliate": "direct affiliate sales creative",
        "semi_affiliate": "soft-sell semi-affiliate creative",
        "showcase_only": "non-selling product showcase",
    }
    intent_direction = {
        "affiliate": "Make the content persuasive and conversion-focused, clearly highlighting benefits and encouraging interest without using text overlays.",
        "semi_affiliate": "Make the content feel like a soft recommendation: informative, natural, lightly persuasive, and not too salesy.",
        "showcase_only": "Do not make it feel like an ad or sales pitch; focus only on aesthetic product presentation, usage context, texture, quality, and realistic details.",
    }

    if product_domain == "Batik Fashion":
        if product_type == "custom":
            product_subject = custom_product or "custom batik product"
        else:
            product_subject = GENERATOR_PRODUCT_TRANSLATIONS.get(product_type, product_type)
            if custom_product:
                product_subject = f"{product_subject} ({custom_product})"
        campaign_subject = "batik fashion affiliate/product campaign"
        if wear_mode == "not_worn_product_display":
            subject_sentence = f"Feature {product_subject} as the hero product not worn by anyone, displayed neatly on a hanger, mannequin-free rack, table layout, or clean product stand"
        elif model_type == "none":
            subject_sentence = f"Feature {product_subject} as the hero product in a premium fashion setup"
        else:
            subject_sentence = f"Feature {model_text} wearing or presenting {product_subject} with natural influencer energy"
        preservation_sentence = "For image-to-video, preserve the same face identity, garment shape, batik motif, fabric texture, and product color from the first frame to the final frame."
        product_photo_sentence = "Treat the product as the hero object, make the fabric surface and silhouette clearly visible, and avoid adding a talent unless explicitly needed."
    elif product_domain == "Gadget Product":
        if gadget_type == "custom":
            gadget_label = custom_gadget or "custom gadget"
        else:
            gadget_label = gadget_type
            if custom_gadget:
                gadget_label = f"{gadget_label} ({custom_gadget})"
        product_subject = f"{gadget_brand} {gadget_label}" if gadget_brand != "Other" else gadget_label
        campaign_subject = "gadget product affiliate/product campaign"
        if model_type == "none":
            subject_sentence = f"Feature {product_subject} in {gadget_condition} condition as the hero product"
        else:
            subject_sentence = f"Feature {model_text} showcasing {product_subject} in {gadget_condition} condition"
        preservation_sentence = "For image-to-video, preserve the exact device shape, screen content style, camera layout, frame color, ports, and accessory placement from the first frame to the final frame."
        product_photo_sentence = "Treat the gadget as the hero object, make the screen, frame, camera module, buttons, ports, and accessories clearly visible, and avoid adding hands unless explicitly needed."
    else:
        if gadget_type == "custom":
            gadget_label = custom_gadget or "customer gadget"
        else:
            gadget_label = gadget_type
            if custom_gadget:
                gadget_label = f"{gadget_label} ({custom_gadget})"
        service_label = service_type
        if custom_service:
            service_label = f"{service_label} ({custom_service})"
        product_subject = f"{service_label} for {gadget_brand} {gadget_label}" if gadget_brand != "Other" else f"{service_label} for {gadget_label}"
        campaign_subject = "gadget repair and service campaign"
        if model_type == "none":
            subject_sentence = f"Show a trustworthy {product_subject} service scenario with a clean before-and-after result"
        else:
            subject_sentence = f"Feature {model_text} in a trustworthy {product_subject} service scenario with a clean before-and-after result"
        preservation_sentence = "For image-to-video, preserve the exact device shape, repair context, tool placement, screen condition, and before-after continuity from the first frame to the final frame."
        product_photo_sentence = "Treat the repaired device and service result as the hero object, making the issue, repair quality, and final working condition visually clear."

    location = choice_or_default(form.get("location"), GENERATOR_LOCATIONS, "studio")
    if location == "custom":
        location = clean_text(form.get("custom_location"), 80) or "custom location"
    place_reference = choice_or_default(
        form.get("place_reference"),
        GENERATOR_PLACE_REFERENCES,
        "minimalist warm studio",
    )
    if place_reference == "custom":
        place_reference_text = clean_text(form.get("custom_place_reference"), 220) or "a custom reference location with a clean, warm, professional fashion atmosphere"
    else:
        place_reference_text = GENERATOR_PLACE_REFERENCE_DETAILS.get(place_reference, place_reference)

    content_style = choice_or_default(form.get("content_style"), GENERATOR_CONTENT_STYLES, "affiliate")
    camera_movement = choice_or_default(form.get("camera_movement"), GENERATOR_CAMERA_MOVEMENTS, "slow push-in")
    duration = choice_or_default(form.get("duration"), GENERATOR_DURATIONS, "15s")
    aspect_ratio = choice_or_default(form.get("aspect_ratio"), ["9:16", "1:1", "16:9"], "9:16")
    visual_style = choice_or_default(form.get("visual_style"), VISUAL_STYLES, "clean commercial")
    framing = choice_or_default(form.get("framing"), GENERATOR_FRAMINGS, "medium to close-up")
    lighting = choice_or_default(form.get("lighting"), GENERATOR_LIGHTINGS, "soft warm natural light")
    mood = choice_or_default(form.get("mood"), GENERATOR_MOODS, "confident")
    quality_level = choice_or_default(form.get("quality_level"), GENERATOR_QUALITY_LEVELS, "high-converting affiliate creative")
    model_action = choice_or_default(
        form.get("model_action"),
        GENERATOR_ACTIONS,
        "adjusting the sleeves while showing the batik pattern",
    )
    detail_focus = form.getlist("detail_focus")
    detail_focus = [item for item in detail_focus if item in GENERATOR_DETAIL_FOCUS]
    if not detail_focus:
        detail_focus = GENERATOR_DOMAIN_DETAIL_DEFAULTS.get(product_domain, ["product color"])
    detail_text = ", ".join(detail_focus)
    selling_point = clean_text(form.get("selling_point"), 500)
    additional_instruction = clean_text(form.get("additional_instruction"), 500)
    hook = clean_text(form.get("hook"), 180)
    cta = clean_text(form.get("cta"), 160)
    delivery_mode = choice_or_default(form.get("delivery_mode"), GENERATOR_DELIVERY_MODES, "silent_showcase")
    script_segments = []
    script_indexes = sorted(
        {
            int(key.rsplit("_", 1)[1])
            for key in form.keys()
            if key.startswith("script_time_") and key.rsplit("_", 1)[1].isdigit()
        }
    )
    for index in script_indexes:
        time_range = clean_text(form.get(f"script_time_{index}"), 24)
        line = clean_text(form.get(f"script_line_{index}"), 240)
        if time_range and line:
            script_segments.append(f'{time_range} "{line}"')

    objective = f"Create a {output_type.lower()} for a {intent_labels[promotion_intent]} in a {campaign_subject}, {content_style} style, aspect ratio {aspect_ratio}"
    if output_type != "Image Prompt" and output_type != "Product Photo":
        objective += f", duration {duration}"
    objective += "."

    movement_sentence = f"Use {framing} as the main framing and apply a {camera_movement} camera movement"
    if output_type in ["Image Prompt", "Product Photo"]:
        movement_sentence = f"Use {framing} as the main composition with a clear product-first layout"

    prompt_parts = [
        objective,
        f"{subject_sentence}, with a {mood} mood, natural micro-expressions, realistic pacing, and a polished but believable styling direction.",
        f"Set the scene in a {location}, using the place reference: {place_reference_text}.",
        f"Use {lighting}, warm natural color tones, clean composition, subtle depth, soft shadows, and a professional {quality_level} finish.",
        f"{movement_sentence}, with stable cinematic motion, no awkward zooms, and product details staying sharp, readable, and visually dominant throughout the frame.",
        f"The main action is {model_action}, performed naturally like a real creator shot, with clear attention to {detail_text}.",
        intent_direction[promotion_intent],
    ]
    if delivery_mode == "talking_script":
        if script_segments:
            prompt_parts.append(
                "The talent speaks directly to camera with clean lip-sync, natural Indonesian delivery, friendly pacing, and this exact timeline script: "
                + "; ".join(script_segments)
                + "."
            )
        else:
            prompt_parts.append(
                "The talent speaks directly to camera with clean lip-sync, natural Indonesian delivery, and friendly pacing while explaining the product/service benefits."
            )
    else:
        prompt_parts.append(
            "Silent product showcase mode: no talking, no dialogue, no lip movement, no voice-over; communicate everything through visuals, gestures, product handling, and clean camera movement."
        )
    if hook:
        prompt_parts.append(f"Opening visual hook: {hook}.")
    if selling_point:
        prompt_parts.append(f"Highlight these selling points naturally: {selling_point}.")
    if cta:
        prompt_parts.append(f"End direction or visual CTA: {cta}.")
    if output_type == "Image to Video":
        prompt_parts.append(preservation_sentence)
    if output_type == "Product Photo":
        prompt_parts.append(product_photo_sentence)
    if promotion_intent == "showcase_only":
        prompt_parts.append("Make it realistic, premium, calm, observational, brand-safe, and suitable for a polished product visual; no sales gesture, no price cue, no text overlay, no watermark, no neon elements, no glow effects, no gradients.")
    else:
        prompt_parts.append("Make it realistic, premium, conversion-aware, brand-safe, and suitable for a polished social commerce ad; no text overlay, no watermark, no neon elements, no glow effects, no gradients.")
    if additional_instruction:
        prompt_parts.append(f"Additional instruction: {additional_instruction}.")

    negative_items = [
        "AI-looking face",
        "plastic skin",
        "distorted hands",
        "extra fingers",
        "unnatural body proportions",
        "changed product color",
        "cluttered background",
        "harsh lighting",
        "overexposed",
        "excessive blur",
        "text",
        "logo",
        "watermark",
        "subtitle text",
        "caption overlay",
        "neon colors",
        "glow effects",
        "gradient",
    ]
    if product_domain == "Batik Fashion":
        negative_items.extend(["warped or melting batik motif", "damaged clothing", "messy stitching"])
    elif product_domain == "Gadget Product":
        negative_items.extend([
            "warped device shape",
            "incorrect camera layout",
            "broken screen unless requested",
            "fake brand logo",
            "unreadable screen reflection",
            "bent laptop body",
            "messy cables",
        ])
    else:
        negative_items.extend([
            "unsafe repair handling",
            "dirty repair table",
            "unprofessional tools",
            "sparks",
            "smoke",
            "broken screen after repair",
            "fake brand logo",
            "customer data visible on screen",
        ])
    if output_type in ["Video Affiliate", "Image to Video"]:
        negative_items.extend(["jittery motion", "flicker", "heavy motion blur", "face changing between frames"])
    if delivery_mode == "silent_showcase":
        negative_items.extend(["talking mouth", "lip movement", "voice-over", "dialogue"])
    else:
        negative_items.extend(["bad lip-sync", "mismatched mouth movement", "robotic speech expression"])
    if model_type == "none" or output_type == "Product Photo":
        negative_items.extend(["human model", "human hands entering the frame"])
        if product_domain == "Batik Fashion":
            negative_items.append("broken mannequin")
    if promotion_intent == "showcase_only":
        negative_items.extend(["hard selling", "salesy gesture", "price tag focus", "aggressive call to action"])
    negative_prompt = "Negative prompt: avoid " + ", ".join(negative_items) + "."
    prompt = " ".join(prompt_parts + [negative_prompt])
    return prompt, negative_prompt


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = clean_text(request.form.get("username"), 80)
        email = clean_text(request.form.get("email"), 120).lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not username or not email or not password:
            flash("Username, email, dan password wajib diisi.", "error")
        elif not EMAIL_RE.match(email):
            flash("Format email tidak valid.", "error")
        elif len(password) < 8:
            flash("Password minimal 8 karakter.", "error")
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
        email = clean_text(request.form.get("email"), 120).lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()

        if login_is_limited():
            flash("Terlalu banyak percobaan login. Coba lagi beberapa menit lagi.", "error")
        elif user and check_password_hash(user.password_hash, password):
            session.clear()
            login_user(user)
            get_csrf_token()
            clear_failed_logins()
            flash("Login berhasil.", "success")
            return redirect(url_for("dashboard"))
        else:
            record_failed_login()
            flash("Email atau password salah.", "error")

    return render_template("auth/login.html")


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    session.clear()
    flash("Kamu sudah logout.", "success")
    return redirect(url_for("login"))


@app.route("/")
@login_required
def dashboard():
    reset_old_tasks_for_current_user()
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
    search = clean_text(request.args.get("q"), 120)
    category = choice_or_default(request.args.get("category"), CATEGORIES, "")
    platform = choice_or_default(request.args.get("platform"), PLATFORMS, "")
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
    prompt.title = clean_text(request.form.get("title"), 160)
    prompt.category = choice_or_default(request.form.get("category"), CATEGORIES, "Other")
    prompt.platform = choice_or_default(request.form.get("platform"), PLATFORMS, "Other")
    prompt.main_prompt = clean_text(request.form.get("main_prompt"), 12000)
    prompt.negative_prompt = clean_text(request.form.get("negative_prompt"), 6000)
    prompt.aspect_ratio = clean_text(request.form.get("aspect_ratio"), 20)
    prompt.visual_style = clean_text(request.form.get("visual_style"), 80)
    prompt.rating = parse_rating(request.form.get("rating"))
    prompt.notes = clean_text(request.form.get("notes"), 4000)


@app.route("/generator", methods=["GET", "POST"])
@login_required
def generator():
    generated_prompt = None
    negative_prompt = None
    form_data = {}
    selected_detail_focus = ["batik motif", "fabric texture", "garment cut"]
    if request.method == "POST":
        form_data = request.form.to_dict()
        selected_detail_focus = request.form.getlist("detail_focus")
        generated_prompt, negative_prompt = build_generated_prompt(request.form)

    return render_template(
        "generator.html",
        generated_prompt=generated_prompt,
        negative_prompt=negative_prompt,
        form_data=form_data,
        selected_detail_focus=selected_detail_focus,
        categories=CATEGORIES,
        platforms=PLATFORMS,
    )


@app.route("/generator/save", methods=["POST"])
@login_required
def generator_save():
    title = clean_text(request.form.get("title"), 160) or "Generated Prompt Batik"
    main_prompt = clean_text(request.form.get("main_prompt"), 12000)
    if not main_prompt:
        flash("Generate prompt terlebih dahulu sebelum menyimpan.", "error")
        return redirect(url_for("generator"))

    prompt = Prompt(
        user_id=current_user.id,
        title=title,
        category=choice_or_default(request.form.get("category"), CATEGORIES, "Video Affiliate"),
        platform=choice_or_default(request.form.get("platform"), PLATFORMS, "Other"),
        main_prompt=main_prompt,
        negative_prompt=clean_text(request.form.get("negative_prompt"), 6000),
        aspect_ratio=clean_text(request.form.get("aspect_ratio"), 20) or "9:16",
        visual_style=clean_text(request.form.get("visual_style"), 80) or "clean commercial",
        rating=parse_rating(request.form.get("rating")),
        notes=clean_text(request.form.get("notes"), 4000),
    )
    db.session.add(prompt)
    db.session.commit()
    flash("Generated prompt berhasil disimpan ke library.", "success")
    return redirect(url_for("prompt_detail", id=prompt.id))


@app.route("/tasks")
@login_required
def tasks_index():
    reset_old_tasks_for_current_user(show_flash=True)
    status = choice_or_default(request.args.get("status"), TASK_STATUSES, "")
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
    task.title = clean_text(request.form.get("title"), 160)
    task.content_type = choice_or_default(request.form.get("content_type"), CONTENT_TYPES, "Image")
    task.status = choice_or_default(request.form.get("status"), TASK_STATUSES, "Ide")
    task.due_date = parse_due_date(request.form.get("due_date"))
    task.platform = choice_or_default(request.form.get("platform"), PLATFORMS, "Other")
    task.notes = clean_text(request.form.get("notes"), 4000)


@app.context_processor
def inject_options():
    return {
        "categories": CATEGORIES,
        "platforms": PLATFORMS,
        "task_statuses": TASK_STATUSES,
        "content_types": CONTENT_TYPES,
        "aspect_ratios": ASPECT_RATIOS,
        "visual_styles": VISUAL_STYLES,
        "generator_output_types": GENERATOR_OUTPUT_TYPES,
        "generator_product_domains": GENERATOR_PRODUCT_DOMAINS,
        "generator_model_types": GENERATOR_MODEL_TYPES,
        "generator_product_types": GENERATOR_PRODUCT_TYPES,
        "generator_gadget_types": GENERATOR_GADGET_TYPES,
        "generator_gadget_brands": GENERATOR_GADGET_BRANDS,
        "generator_service_types": GENERATOR_SERVICE_TYPES,
        "generator_gadget_conditions": GENERATOR_GADGET_CONDITIONS,
        "generator_delivery_modes": GENERATOR_DELIVERY_MODES,
        "generator_promotion_intents": GENERATOR_PROMOTION_INTENTS,
        "generator_wear_modes": GENERATOR_WEAR_MODES,
        "generator_locations": GENERATOR_LOCATIONS,
        "generator_place_references": GENERATOR_PLACE_REFERENCES,
        "generator_content_styles": GENERATOR_CONTENT_STYLES,
        "generator_camera_movements": GENERATOR_CAMERA_MOVEMENTS,
        "generator_durations": GENERATOR_DURATIONS,
        "generator_framings": GENERATOR_FRAMINGS,
        "generator_lightings": GENERATOR_LIGHTINGS,
        "generator_moods": GENERATOR_MOODS,
        "generator_actions": GENERATOR_ACTIONS,
        "generator_detail_focus": GENERATOR_DETAIL_FOCUS,
        "generator_quality_levels": GENERATOR_QUALITY_LEVELS,
        "csrf_token": get_csrf_token,
    }


if __name__ == "__main__":
    app.run(debug=True)
