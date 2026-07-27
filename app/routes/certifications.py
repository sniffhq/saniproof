"""
Certification tracking: define the certification types a company cares
about (e.g. "HACCP", "Chemical Handling"), assign them to staff with an
issue/expiry date, and surface anything expired or expiring soon so it
doesn't get missed during an audit.
"""
from datetime import date, timedelta

from flask import Blueprint, render_template, request, redirect, url_for, flash

from app.auth import staff_required
from app.extensions import db
from app.models import Company, Certification, StaffCertification, Staff

certifications_bp = Blueprint("certifications", __name__)

EXPIRING_SOON_DAYS = 30


def _status_for(expires_date):
    if not expires_date:
        return "none"
    today = date.today()
    if expires_date < today:
        return "expired"
    if expires_date <= today + timedelta(days=EXPIRING_SOON_DAYS):
        return "expiring"
    return "valid"


@certifications_bp.route("/company/<uuid:company_id>/certifications")
@staff_required
def cert_list(company_id):
    company = Company.query.get_or_404(company_id)
    cert_types = Certification.query.filter_by(company_id=company_id).order_by(Certification.name).all()
    staff = Staff.query.filter_by(company_id=company_id).order_by(Staff.name).all()

    records = (
        StaffCertification.query.join(Staff)
        .filter(Staff.company_id == company_id)
        .order_by(StaffCertification.expires_date.asc().nullslast())
        .all()
    )
    for record in records:
        record.status = _status_for(record.expires_date)

    return render_template(
        "certifications_list.html",
        company=company,
        cert_types=cert_types,
        staff=staff,
        records=records,
        show_sidebar=True,
        active_nav="certifications",
    )


@certifications_bp.route("/company/<uuid:company_id>/certifications/types/new", methods=["POST"])
@staff_required
def cert_type_new(company_id):
    Company.query.get_or_404(company_id)
    name = request.form.get("name", "").strip()
    if not name:
        flash("Certification name is required.", "error")
        return redirect(url_for("certifications.cert_list", company_id=company_id))

    cert = Certification(
        company_id=company_id,
        name=name,
        description=request.form.get("description") or None,
    )
    db.session.add(cert)
    db.session.commit()
    flash(f'Certification type "{cert.name}" added.')
    return redirect(url_for("certifications.cert_list", company_id=company_id))


@certifications_bp.route("/company/<uuid:company_id>/certifications/assign", methods=["POST"])
@staff_required
def staff_cert_new(company_id):
    Company.query.get_or_404(company_id)
    staff_id = request.form.get("staff_id")
    certification_id = request.form.get("certification_id")

    staff_member = Staff.query.filter_by(id=staff_id, company_id=company_id).first()
    cert_type = Certification.query.filter_by(id=certification_id, company_id=company_id).first()
    if not staff_member or not cert_type:
        flash("Choose a staff member and a certification type.", "error")
        return redirect(url_for("certifications.cert_list", company_id=company_id))

    record = StaffCertification(
        staff_id=staff_member.id,
        certification_id=cert_type.id,
        issued_date=request.form.get("issued_date") or None,
        expires_date=request.form.get("expires_date") or None,
    )
    db.session.add(record)
    db.session.commit()
    flash(f"{cert_type.name} assigned to {staff_member.name}.")
    return redirect(url_for("certifications.cert_list", company_id=company_id))


@certifications_bp.route(
    "/company/<uuid:company_id>/certifications/<uuid:record_id>/delete", methods=["POST"]
)
@staff_required
def staff_cert_delete(company_id, record_id):
    Company.query.get_or_404(company_id)
    record = (
        StaffCertification.query.join(Staff)
        .filter(StaffCertification.id == record_id, Staff.company_id == company_id)
        .first_or_404()
    )
    db.session.delete(record)
    db.session.commit()
    flash("Certification record removed.")
    return redirect(url_for("certifications.cert_list", company_id=company_id))
