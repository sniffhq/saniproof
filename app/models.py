"""
SQLAlchemy models mapped to the tables already created in Supabase.
These mirror the `saniproof_initial_schema` migration exactly -- do not
rename columns/tables here without also migrating the database.
"""
import uuid

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.extensions import db


def gen_uuid():
    return uuid.uuid4()


class Company(db.Model):
    __tablename__ = "companies"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    name = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    staff = db.relationship("Staff", backref="company", lazy=True)
    clients = db.relationship("Client", backref="company", lazy=True)
    chemicals = db.relationship("Chemical", backref="company", lazy=True)
    certifications = db.relationship("Certification", backref="company", lazy=True)


class Staff(db.Model):
    __tablename__ = "staff"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    company_id = db.Column(UUID(as_uuid=True), db.ForeignKey("companies.id"), nullable=False)
    name = db.Column(db.Text, nullable=False)
    email = db.Column(db.Text, nullable=False, unique=True)
    role = db.Column(db.Text, nullable=False)  # 'admin' | 'crew'
    phone = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())


class Certification(db.Model):
    __tablename__ = "certifications"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    company_id = db.Column(UUID(as_uuid=True), db.ForeignKey("companies.id"), nullable=False)
    name = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())


class StaffCertification(db.Model):
    __tablename__ = "staff_certifications"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    staff_id = db.Column(UUID(as_uuid=True), db.ForeignKey("staff.id"), nullable=False)
    certification_id = db.Column(UUID(as_uuid=True), db.ForeignKey("certifications.id"), nullable=False)
    issued_date = db.Column(db.Date)
    expires_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())


class Client(db.Model):
    __tablename__ = "clients"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    company_id = db.Column(UUID(as_uuid=True), db.ForeignKey("companies.id"), nullable=False)
    name = db.Column(db.Text, nullable=False)
    address = db.Column(db.Text)
    contact_name = db.Column(db.Text)
    contact_email = db.Column(db.Text)
    contact_phone = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    zones = db.relationship("Zone", backref="client", lazy=True)
    client_users = db.relationship("ClientUser", backref="client", lazy=True)


class ClientUser(db.Model):
    __tablename__ = "client_users"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    client_id = db.Column(UUID(as_uuid=True), db.ForeignKey("clients.id"), nullable=False)
    name = db.Column(db.Text, nullable=False)
    email = db.Column(db.Text, nullable=False, unique=True)
    role = db.Column(db.Text, nullable=False, default="viewer")  # 'viewer' | 'admin'
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())


class Zone(db.Model):
    __tablename__ = "zones"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    client_id = db.Column(UUID(as_uuid=True), db.ForeignKey("clients.id"), nullable=False)
    name = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    mss_tasks = db.relationship("MssTask", backref="zone", lazy=True)


class Chemical(db.Model):
    __tablename__ = "chemicals"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    company_id = db.Column(UUID(as_uuid=True), db.ForeignKey("companies.id"), nullable=False)
    name = db.Column(db.Text, nullable=False)
    sds_url = db.Column(db.Text)
    default_dilution = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())


class SopDocument(db.Model):
    __tablename__ = "sop_documents"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    company_id = db.Column(UUID(as_uuid=True), db.ForeignKey("companies.id"), nullable=False)
    title = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.Text)
    file_url = db.Column(db.Text)
    version = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())


class MssTask(db.Model):
    __tablename__ = "mss_tasks"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    zone_id = db.Column(UUID(as_uuid=True), db.ForeignKey("zones.id"), nullable=False)
    name = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    frequency = db.Column(db.Text, nullable=False)  # daily | weekly | monthly | quarterly | custom
    default_chemical_id = db.Column(UUID(as_uuid=True), db.ForeignKey("chemicals.id"))
    sop_document_id = db.Column(UUID(as_uuid=True), db.ForeignKey("sop_documents.id"))
    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    default_chemical = db.relationship("Chemical")
    sop_document = db.relationship("SopDocument")
    assignments = db.relationship("TaskAssignment", backref="mss_task", lazy=True)


class Shift(db.Model):
    __tablename__ = "shifts"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    company_id = db.Column(UUID(as_uuid=True), db.ForeignKey("companies.id"), nullable=False)
    client_id = db.Column(UUID(as_uuid=True), db.ForeignKey("clients.id"), nullable=False)
    shift_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.DateTime(timezone=True))
    end_time = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    client = db.relationship("Client")
    assignments = db.relationship("TaskAssignment", backref="shift", lazy=True)


class TaskAssignment(db.Model):
    __tablename__ = "task_assignments"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    mss_task_id = db.Column(UUID(as_uuid=True), db.ForeignKey("mss_tasks.id"), nullable=False)
    shift_id = db.Column(UUID(as_uuid=True), db.ForeignKey("shifts.id"), nullable=False)
    assigned_staff_id = db.Column(UUID(as_uuid=True), db.ForeignKey("staff.id"))
    status = db.Column(db.Text, nullable=False, default="pending")
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    assigned_staff = db.relationship("Staff")
    completions = db.relationship("Completion", backref="task_assignment", lazy=True)
    issues = db.relationship("Issue", backref="task_assignment", lazy=True)


class Completion(db.Model):
    __tablename__ = "completions"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    task_assignment_id = db.Column(UUID(as_uuid=True), db.ForeignKey("task_assignments.id"), nullable=False)
    completed_by = db.Column(UUID(as_uuid=True), db.ForeignKey("staff.id"))
    completed_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    photo_url = db.Column(db.Text)
    chemical_id = db.Column(UUID(as_uuid=True), db.ForeignKey("chemicals.id"))
    dilution_used = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    completed_by_staff = db.relationship("Staff")
    chemical = db.relationship("Chemical")


class Issue(db.Model):
    __tablename__ = "issues"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    task_assignment_id = db.Column(UUID(as_uuid=True), db.ForeignKey("task_assignments.id"))
    completion_id = db.Column(UUID(as_uuid=True), db.ForeignKey("completions.id"))
    reported_by = db.Column(UUID(as_uuid=True), db.ForeignKey("staff.id"))
    description = db.Column(db.Text, nullable=False)
    severity = db.Column(db.Text, nullable=False, default="medium")
    status = db.Column(db.Text, nullable=False, default="open")
    corrective_action = db.Column(db.Text)
    resolved_by = db.Column(UUID(as_uuid=True), db.ForeignKey("staff.id"))
    resolved_at = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
