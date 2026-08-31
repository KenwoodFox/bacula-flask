import os

from flask import Blueprint, Response, abort, redirect, render_template, request, session, url_for

from .auth import SESSION_KEY, _safe_next, check_password, password_enabled

from .catalog import (
    fetch_dashboard_jobs,
    fetch_job_history,
    fetch_media_by_pool,
    fetch_volume,
    fetch_volumes_for_labels,
)
from .expiry_layout import build_expiry_groups
from .hidden_jobs import filter_dashboard_jobs
from .library_layout import build_vault_layout
from .labels import (
    build_tape_label,
    build_tape_label_sheet,
    build_vault_barcode,
    png_bytes,
)
from .time import format_timestamp

bp = Blueprint("main", __name__)

SHELF_COLS = int(os.environ.get("VAULT_SHELF_COLS", "8"))
LABELS_PREFIX = "/_internal/tape-labels"


def _labels_allowed():
    """Optional LABELS_SECRET query param; path is not linked in the UI."""
    secret = os.environ.get("LABELS_SECRET")
    if not secret:
        return True
    return request.args.get("key") == secret


@bp.route("/login", methods=["GET", "POST"])
def login():
    if not password_enabled():
        return redirect(url_for("main.index"))

    next_url = _safe_next(request.args.get("next")) or url_for("main.index")
    if request.method == "POST":
        if check_password(request.form.get("password", "")):
            session[SESSION_KEY] = True
            return redirect(_safe_next(request.args.get("next")) or url_for("main.index"))
        return render_template("login.html", error=True, next_url=next_url)

    return render_template("login.html", error=False, next_url=next_url)


@bp.route("/")
def index():
    jobs = filter_dashboard_jobs(fetch_dashboard_jobs())

    for job in jobs:
        if job.get("last_run_time"):
            job["formatted_time"] = format_timestamp(job["last_run_time"])
        else:
            job["formatted_time"] = "N/A"

    return render_template("index.html", jobs=jobs)


@bp.route("/vault")
def media_vault():
    view = request.args.get("view", "layout")
    if view not in ("layout", "expiry"):
        view = "layout"

    pools = fetch_media_by_pool()
    all_tapes = [tape for pool in pools for tape in pool["media"]]

    ctx = {
        "pools": pools,
        "shelf_cols": SHELF_COLS,
        "vault_view": view,
    }
    if view == "expiry":
        ctx.update(build_expiry_groups(all_tapes))
    else:
        ctx.update(build_vault_layout(all_tapes))

    return render_template("media_vault.html", **ctx)


@bp.route("/vault/barcode/<path:volumename>.png")
def vault_barcode_png(volumename):
    width = request.args.get("w", type=int) or 280
    height = request.args.get("h", type=int) or 76
    try:
        image = build_vault_barcode(volumename, width=width, height=height)
    except (ValueError, Exception):
        abort(404)
    return Response(
        png_bytes(image),
        mimetype="image/png",
        headers={"Cache-Control": "public, max-age=86400"},
    )


@bp.route("/job/<job_name>")
def job_details(job_name):
    job_history = fetch_job_history(job_name)
    return render_template(
        "job_details.html", job_name=job_name, job_history=job_history
    )


@bp.route("/volume/<volume_id>")
def volume_details(volume_id):
    volume_info = fetch_volume(volume_id)
    if volume_info is None:
        abort(404)

    return render_template(
        "volume_details.html", volume_id=volume_id, volume_info=volume_info
    )


@bp.route(f"{LABELS_PREFIX}/<volumename>.png")
def tape_label_png(volumename):
    if not _labels_allowed():
        abort(404)

    pool_name = request.args.get("pool")
    image = build_tape_label(volumename, pool_name)
    return Response(png_bytes(image), mimetype="image/png")


@bp.route(f"{LABELS_PREFIX}/sheet.png")
def tape_label_sheet_png():
    if not _labels_allowed():
        abort(404)

    pool_name = request.args.get("pool")
    volumes_arg = request.args.get("volumes")
    columns = request.args.get("cols", type=int) or 3

    if volumes_arg:
        entries = [(v.strip(), pool_name) for v in volumes_arg.split(",") if v.strip()]
    else:
        entries = fetch_volumes_for_labels(pool_name)

    if not entries:
        abort(404)

    image = build_tape_label_sheet(entries, columns=columns)
    return Response(png_bytes(image), mimetype="image/png")
