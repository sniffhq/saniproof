"""
SOP (Standard Operating Procedure) document library: view and upload the
documents that back each recurring task. Crews and QA both need to be
able to find "what's the actual procedure for this task" -- this is
where that lives.

File storage here is the same local-disk stub used for task photos (see
app/routes/tasks.py) -- fine for testing, NOT persistent on Railway
across redeploys. Swap for Supabase Storage or S3 before this holds
real, only-copy-of documents.
"""
import os
import uuid

from flask import Blueprint, render_template, request, redirect, url_for, current_app, flash
from werkzeug.utils import secure_filename

from app.auth import staff_required
from app.extensions import db
from app.models import Company, SopDocument, MssTask

sops_bp = Blueprint("sops", __name__)


def _get_company_sop_or_404(company_id, sop_id):
    return SopDocument.query.filter_by(id=sop_id, company_id=company_id).first_or_404()


@sops_bp.route("/company/<uuid:company_id>/sops")
@staff_required
def sop_list(company_id):
    company = Company.query.get_or_404(company_id)
    sops = (
        SopDocument.query.filter_by(company_id=company_id)
        .order_by(SopDocument.category, SopDocument.title)
        .all()
    )
    return render_template(
        "sops_list.html", company=company, sops=sops, show_sidebar=True, active_nav="sops"
    )


@sops_bp.route("/company/<uuid:company_id>/sops/new", methods=["GET", "POST"])
@staff_required
def sop_new(company_id):
    company = Company.query.get_or_404(company_id)

    if request.method == "POST":
        file_url = None
        doc = request.files.get("file")
        if doc and doc.filename:
            filename = f"{uuid.uuid4()}_{secure_filename(doc.filename)}"
            doc.save(os.path.join(current_app.config["SOP_UPLOAD_FOLDER"], filename))
            file_url = f"/static/sops/{filename}"

        sop = SopDocument(
            company_id=company_id,
            title=request.form["title"],
            description=request.form.get("description"),
            category=request.form.get("category") or None,
            version=request.form.get("version") or None,
            file_url=file_url,
        )
        db.session.add(sop)
        db.session.commit()
        flash(f'SOP "{sop.title}" added.')
        return redirect(url_for("sops.sop_list", company_id=company_id))

    return render_template(
        "sop_form.html", company=company, sop=None, show_sidebar=True, active_nav="sops"
    )


@sops_bp.route("/company/<uuid:company_id>/sops/<uuid:sop_id>/edit", methods=["GET", "POST"])
@staff_required
def sop_edit(company_id, sop_id):
    company = Company.query.get_or_404(company_id)
    sop = _get_company_sop_or_404(company_id, sop_id)

    if request.method == "POST":
        sop.title = request.form["title"]
        sop.description = request.form.get("description")
        sop.category = request.form.get("category") or None
        sop.version = request.form.get("version") or None

        doc = request.files.get("file")
        if doc and doc.filename:
            filename = f"{uuid.uuid4()}_{secure_filename(doc.filename)}"
            doc.save(os.path.join(current_app.config["SOP_UPLOAD_FOLDER"], filename))
            sop.file_url = f"/static/sops/{filename}"

        db.session.commit()
        flash(f'"{sop.title}" updated.')
        return redirect(url_for("sops.sop_list", company_id=company_id))

    return render_template(
        "sop_form.html", company=company, sop=sop, show_sidebar=True, active_nav="sops"
    )


@sops_bp.route("/company/<uuid:company_id>/sops/<uuid:sop_id>/delete", methods=["POST"])
@staff_required
def sop_delete(company_id, sop_id):
    sop = _get_company_sop_or_404(company_id, sop_id)

    # Unlink any tasks pointing at this SOP before deleting it, rather than
    # letting the FK constraint block the delete.
    MssTask.query.filter_by(sop_document_id=sop.id).update({"sop_document_id": None})
    title = sop.title
    db.session.delete(sop)
    db.session.commit()
    flash(f'"{title}" deleted.')
    return redirect(url_for("sops.sop_list", company_id=company_id))
