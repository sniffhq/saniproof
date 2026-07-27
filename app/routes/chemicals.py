"""
Chemical library: list, create, and edit the chemicals a company uses,
each with an optional SDS (Safety Data Sheet) file. There was previously
no UI for this at all -- chemicals could only be seeded via SQL, even
though tasks and completions already referenced them.

File storage is the same local-disk stub used for SOPs/photos -- fine for
testing, not persistent on Railway across redeploys.
"""
import os
import uuid

from flask import Blueprint, render_template, request, redirect, url_for, current_app, flash
from werkzeug.utils import secure_filename

from app.auth import staff_required
from app.extensions import db
from app.models import Company, Chemical

chemicals_bp = Blueprint("chemicals", __name__)


def _get_company_chemical_or_404(company_id, chemical_id):
    return Chemical.query.filter_by(id=chemical_id, company_id=company_id).first_or_404()


@chemicals_bp.route("/company/<uuid:company_id>/chemicals")
@staff_required
def chemical_list(company_id):
    company = Company.query.get_or_404(company_id)
    chemicals = Chemical.query.filter_by(company_id=company_id).order_by(Chemical.name).all()
    return render_template(
        "chemicals_list.html", company=company, chemicals=chemicals, show_sidebar=True, active_nav="chemicals"
    )


@chemicals_bp.route("/company/<uuid:company_id>/chemicals/new", methods=["GET", "POST"])
@staff_required
def chemical_new(company_id):
    company = Company.query.get_or_404(company_id)

    if request.method == "POST":
        sds_url = _save_sds_upload(request.files.get("sds_file"))
        chemical = Chemical(
            company_id=company_id,
            name=request.form["name"],
            default_dilution=request.form.get("default_dilution") or None,
            sds_url=sds_url,
        )
        db.session.add(chemical)
        db.session.commit()
        flash(f'Chemical "{chemical.name}" added.')
        return redirect(url_for("chemicals.chemical_list", company_id=company_id))

    return render_template(
        "chemical_form.html", company=company, chemical=None, show_sidebar=True, active_nav="chemicals"
    )


@chemicals_bp.route("/company/<uuid:company_id>/chemicals/<uuid:chemical_id>/edit", methods=["GET", "POST"])
@staff_required
def chemical_edit(company_id, chemical_id):
    company = Company.query.get_or_404(company_id)
    chemical = _get_company_chemical_or_404(company_id, chemical_id)

    if request.method == "POST":
        chemical.name = request.form["name"]
        chemical.default_dilution = request.form.get("default_dilution") or None

        new_sds_url = _save_sds_upload(request.files.get("sds_file"))
        if new_sds_url:
            chemical.sds_url = new_sds_url

        db.session.commit()
        flash(f'"{chemical.name}" updated.')
        return redirect(url_for("chemicals.chemical_list", company_id=company_id))

    return render_template(
        "chemical_form.html", company=company, chemical=chemical, show_sidebar=True, active_nav="chemicals"
    )


def _save_sds_upload(file_storage):
    if not file_storage or not file_storage.filename:
        return None
    filename = f"{uuid.uuid4()}_{secure_filename(file_storage.filename)}"
    file_storage.save(os.path.join(current_app.config["SDS_UPLOAD_FOLDER"], filename))
    return f"/static/sds/{filename}"
