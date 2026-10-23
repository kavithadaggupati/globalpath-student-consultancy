

import os
import re
import sqlite3
from functools import wraps
from datetime import datetime, date

import uuid
from pathlib import Path

from flask import send_from_directory
from werkzeug.utils import secure_filename
from database import (
    # Keep all your existing imports.
    initialize_courses_table,
)

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
)
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import (
    generate_password_hash,
    check_password_hash,
)

from database import (
    initialize_database,
    create_student,
    get_student_by_email,
    get_student_by_id,
    initialize_profile_table,
    get_student_profile,
    save_student_profile,
    initialize_consultancy_table,
    create_consultancy_request,
    get_requests_by_student,
    initialize_admin_table,
    get_admin_by_email,
    get_all_consultancy_requests,
    update_consultancy_status,
    initialize_documents_table,
    save_student_document,
    get_documents_by_student,
    get_student_document,
    initialize_notifications_table,
    create_notification,
    get_notifications_by_student,
    get_unread_notification_count,
    mark_notification_as_read,
    get_consultancy_request_by_id,
    get_admin_statistics,
    search_universities,
    search_students,
    filter_consultancy_requests,
    initialize_universities_table,
    upgrade_universities_table,
    get_all_universities,
    get_university_details,
    update_university_details,
    initialize_courses_table,
    initialize_courses_table,
    search_courses,
    add_course,
    get_all_universities,
    get_course_by_id,
    update_course_verification,
    get_all_courses,
    initialize_course_applications_table,
    create_course_application,
    get_all_courses,
    get_course_applications_by_student,
    get_all_course_applications,
    update_course_application_status,
    get_course_application_by_id,


)


app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "uploads"
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

ALLOWED_EXTENSIONS = {"pdf", "jpg", "jpeg", "png"}


# Set SECRET_KEY in your environment before deployment.
# The fallback is for local development only.
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "dev-only-change-this-secret-key-before-deployment"
)

# Protect POST forms against cross-site request forgery.
csrf = CSRFProtect(app)



# Create the database table when the app starts.
initialize_database()
initialize_profile_table()
initialize_consultancy_table()
initialize_admin_table()
initialize_documents_table()
initialize_notifications_table()
initialize_universities_table()
upgrade_universities_table()
initialize_courses_table()
initialize_course_applications_table()


def login_required(view_function):
    """Allow a page only when a student is signed in."""

    @wraps(view_function)
    def wrapped_view(*args, **kwargs):
        if "student_id" not in session:
            flash("Please log in to access that page.", "error")
            return redirect(url_for("login"))

        # Also check that the account still exists.
        student = get_student_by_id(session["student_id"])

        if student is None:
            session.clear()
            flash("Please log in again.", "error")
            return redirect(url_for("login"))

        return view_function(*args, **kwargs)

    return wrapped_view


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if "student_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        full_name = request.form.get(
            "full_name", ""
        ).strip()

        email = request.form.get(
            "email", ""
        ).strip().lower()

        password = request.form.get("password", "")
        confirm_password = request.form.get(
            "confirm_password", ""
        )

        # Validate the submitted information.
        if not full_name or len(full_name) > 100:
            flash(
                "Enter a name between 1 and 100 characters.",
                "error"
            )

        elif not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            flash("Enter a valid email address.", "error")

        elif len(email) > 254:
            flash("Email address is too long.", "error")

        elif len(password) < 8:
            flash(
                "Password must contain at least 8 characters.",
                "error"
            )

        elif len(password) > 128:
            flash("Password must not exceed 128 characters.", "error")

        elif password != confirm_password:
            flash("The passwords do not match.", "error")

        else:
            existing_student = get_student_by_email(email)

            if existing_student:
                flash(
                    "An account with this email already exists.",
                    "error"
                )
            else:
                # Hash the password before storing it.
                password_hash = generate_password_hash(password)

                try:
                    create_student(
                        full_name,
                        email,
                        password_hash
                    )
                    flash(
                        "Registration successful. Please log in.",
                        "success"
                    )
                    return redirect(url_for("login"))

                except sqlite3.IntegrityError:
                    # Handles a duplicate email submitted at
                    # almost the same time by another request.
                    flash(
                        "That email is already registered.",
                        "error"
                    )

        return render_template("register.html")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if "student_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get(
            "email", ""
        ).strip().lower()

        password = request.form.get("password", "")

        student = get_student_by_email(email)

        if (
            student is not None
            and check_password_hash(
                student["password_hash"], password
            )
        ):
            # Start a fresh authenticated session.
            session.clear()
            session["student_id"] = student["id"]
            session.permanent = True

            flash("Welcome back!", "success")
            return redirect(url_for("dashboard"))

        flash(
            "Invalid email address or password.",
            "error"
        )

    return render_template("login.html")


@app.route("/dashboard")
@login_required
def dashboard():
    student = get_student_by_id(session["student_id"])

    return render_template(
        "dashboard.html",
        student=student
    )


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    student_id = session["student_id"]
    current_year = date.today().year

    if request.method == "POST":
        qualification = request.form.get(
            "qualification", ""
        ).strip()

        grades = request.form.get("grades", "").strip()
        degree_level = request.form.get("degree_level", "").strip()
        preferred_country = request.form.get(
            "preferred_country", ""
        ).strip()
        preferred_course = request.form.get(
            "preferred_course", ""
        ).strip()
        budget = request.form.get("budget", "").strip()
        intake_year = request.form.get("intake_year", "").strip()

        # Allowed choices prevent arbitrary values for these fields.
        allowed_degrees = {
            "Bachelor's", "Master's", "PhD", "Diploma"
        }
        allowed_countries = {
            "USA", "UK", "Canada", "Australia", "Germany", "Other"
        }
        allowed_budgets = {
            "Under 10 lakh",
            "10-20 lakh",
            "20-35 lakh",
            "35 lakh or more"
        }

    
        allowed_intakes = {
            str(year) for year in range(current_year, current_year + 6)
        }

        if not qualification or len(qualification) > 100:
            flash("Enter your highest qualification.", "error")

        elif len(grades) > 50:
            flash("Grades or percentage must be 50 characters or fewer.", "error")

        elif degree_level not in allowed_degrees:
            flash("Choose a valid degree level.", "error")

        elif preferred_country not in allowed_countries:
            flash("Choose a valid destination.", "error")

        elif not preferred_course or len(preferred_course) > 100:
            flash("Enter your intended course.", "error")

        elif budget not in allowed_budgets:
            flash("Choose a valid budget range.", "error")

        elif intake_year not in allowed_intakes:
            flash("Choose a valid admission intake year.", "error")

        else:
            save_student_profile(
                student_id,
                qualification,
                grades,
                degree_level,
                preferred_country,
                preferred_course,
                budget,
                intake_year
            )
            flash("Your study-abroad profile has been saved.", "success")
            return redirect(url_for("profile"))

    saved_profile = get_student_profile(student_id)

    return render_template(
        "profile.html",
        profile=saved_profile,
        current_year=current_year
    )



@app.route("/consultancy", methods=["GET", "POST"])
@login_required
def consultancy():
    student_id = session["student_id"]
    today = date.today().isoformat()

    service_types = [
        "University Selection",
        "Course Selection",
        "Admission Guidance",
        "Visa Guidance",
        "Scholarship Guidance",
    ]

    if request.method == "POST":
        service_type = request.form.get(
            "service_type", ""
        ).strip()

        appointment_date = request.form.get(
            "appointment_date", ""
        ).strip()

        appointment_time = request.form.get(
            "appointment_time", ""
        ).strip()

        message = request.form.get(
            "message", ""
        ).strip()

        allowed_times = {
            "09:00", "10:00", "11:00", "12:00",
            "13:00", "14:00", "15:00", "16:00"
        }

        valid_date = False

        try:
            selected_date = datetime.strptime(
                appointment_date, "%Y-%m-%d"
            ).date()

            valid_date = (
                selected_date.isoformat() == appointment_date
                and selected_date >= date.today()
            )
        except ValueError:
            valid_date = False

        if service_type not in service_types:
            flash("Please select a valid service.", "error")

        elif not valid_date:
            flash(
                "Choose today or a future appointment date.",
                "error"
            )

        elif appointment_time not in allowed_times:
            flash("Please select a valid appointment time.", "error")

        elif len(message) > 1000:
            flash("Your message must be 1000 characters or fewer.", "error")

        else:
            create_consultancy_request(
                student_id,
                service_type,
                appointment_date,
                appointment_time,
                message,
            )

            flash(
                "Your consultancy request has been submitted!",
                "success"
            )

            return redirect(url_for("consultancy"))

    requests_list = get_requests_by_student(student_id)

    return render_template(
        "consultancy.html",
        service_types=service_types,
        requests_list=requests_list,
        today=today,
    )


def admin_required(view_function):
    @wraps(view_function)
    def wrapped_view(*args, **kwargs):
        if "admin_id" not in session:
            flash("Please log in as an administrator.", "error")
            return redirect(url_for("admin_login"))

        return view_function(*args, **kwargs)

    return wrapped_view
@app.route("/admin/course-applications")
@admin_required
def admin_course_applications():
    applications = get_all_course_applications()

    return render_template(
        "admin_course_applications.html",
        applications=applications
    )



@app.route(
    "/admin/course-applications/<int:application_id>/status",
    methods=["POST"]
)
@admin_required
def admin_update_course_application_status(application_id):
    status = request.form.get("status", "").strip()

    # Get the application before updating its status.
    application = get_course_application_by_id(application_id)

    if application is None:
        flash("Course application was not found.", "error")
        return redirect(url_for("admin_course_applications"))

    previous_status = application["status"]

    try:
        update_course_application_status(application_id, status)

        # Notify the student only when the status changes.
        if previous_status != status:
            create_notification(
                student_id=application["student_id"],
                request_id=None,
                title="Course Application Status Updated",
                message=(
                    f"Your application for "
                    f"{application['course_name']} at "
                    f"{application['university_name']} "
                    f"has been updated to: {status}."
                )
            )

        flash(
            "Course application status updated successfully.",
            "success"
        )

    except ValueError as error:
        flash(str(error), "error")

    return redirect(url_for("admin_course_applications"))


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if "admin_id" in session:
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        admin = get_admin_by_email(email)

        if (
            admin is not None
            and check_password_hash(admin["password_hash"], password)
        ):
            session.clear()
            session["admin_id"] = admin["id"]
            session.permanent = True
            flash("Admin login successful.", "success")
            return redirect(url_for("admin_dashboard"))

        flash("Invalid admin email or password.", "error")

    return render_template("admin_login.html")


@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    requests_list = get_all_consultancy_requests()

    return render_template(
        "admin_dashboard.html",
        requests_list=requests_list,
    )





@app.route(
    "/admin/request/<int:request_id>/status",
    methods=["POST"]
)
@admin_required
def admin_update_status(request_id):
    status = request.form.get("status", "")

    if status not in {"Approved", "Rejected"}:
        flash("Invalid status selected.", "error")
        return redirect(url_for("admin_dashboard"))

    consultancy_request = get_consultancy_request_by_id(request_id)

    if consultancy_request is None:
        flash("Consultancy request not found.", "error")
        return redirect(url_for("admin_dashboard"))

    if consultancy_request["status"] != "Pending":
        flash(
            "Only pending requests can be updated.",
            "error"
        )
        return redirect(url_for("admin_dashboard"))

    updated = update_consultancy_status(request_id, status)

    if updated:
        student_id = consultancy_request["student_id"]

        if status == "Approved":
            title = "Appointment Approved"
            message = (
                f"Your consultancy request #{request_id} "
                "has been approved. Please check your "
                "appointment details on the consultancy page."
            )
        else:
            title = "Appointment Rejected"
            message = (
                f"Your consultancy request #{request_id} "
                "has been rejected. Please contact the "
                "consultancy team if you need assistance."
            )

        create_notification(
            student_id,
            request_id,
            title,
            message
        )

        flash(
            f"Request #{request_id} marked {status.lower()}.",
            "success"
        )
    else:
        flash(
            "The request could not be updated.",
            "error"
        )

    return redirect(url_for("admin_dashboard"))




@app.route("/admin/logout", methods=["POST"])
@admin_required
def admin_logout():
    session.clear()
    flash("Admin logged out successfully.", "success")
    return redirect(url_for("admin_login"))


@app.route("/documents", methods=["GET", "POST"])
@login_required
def documents():
    student_id = session["student_id"]

    document_types = [
        "Passport",
        "Academic Transcript",
        "Degree Certificate",
        "English Language Test Result",
        "Statement of Purpose",
        "Other",
    ]

    if request.method == "POST":
        document_type = request.form.get(
            "document_type", ""
        ).strip()

        uploaded_file = request.files.get("document")

        if document_type not in document_types:
            flash("Please select a valid document type.", "error")

        elif uploaded_file is None or not uploaded_file.filename:
            flash("Please choose a file to upload.", "error")

        else:
            original_filename = secure_filename(
                uploaded_file.filename
            )

            extension = (
                original_filename.rsplit(".", 1)[-1].lower()
                if "." in original_filename
                else ""
            )

            if not original_filename:
                flash("The filename is invalid.", "error")

            elif extension not in ALLOWED_EXTENSIONS:
                flash(
                    "Only PDF, JPG, JPEG, and PNG files are allowed.",
                    "error",
                )

            else:
                stored_filename = (
                    f"{uuid.uuid4().hex}.{extension}"
                )

                try:
                    uploaded_file.save(
                        str(
                            Path(app.config["UPLOAD_FOLDER"])
                            / stored_filename
                        )
                    )

                    save_student_document(
                        student_id,
                        document_type,
                        original_filename,
                        stored_filename,
                    )

                    flash("Document uploaded successfully.", "success")
                    return redirect(url_for("documents"))

                except Exception:
                    saved_path = (
                        Path(app.config["UPLOAD_FOLDER"])
                        / stored_filename
                    )
                    saved_path.unlink(missing_ok=True)

                    app.logger.exception(
                        "Could not save student document."
                    )
                    flash(
                        "The document could not be saved. Please try again.",
                        "error",
                    )

    documents_list = get_documents_by_student(student_id)

    return render_template(
        "documents.html",
        document_types=document_types,
        documents_list=documents_list,
    )


@app.route("/documents/<int:document_id>/download")
@login_required
def download_document(document_id):
    student_id = session["student_id"]

    document = get_student_document(document_id, student_id)

    if document is None:
        flash("Document not found.", "error")
        return redirect(url_for("documents"))

    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        document["stored_filename"],
        as_attachment=True,
        download_name=document["original_filename"],
    )



@app.route("/notifications")
@login_required
def notifications():
    student_id = session["student_id"]

    notifications_list = get_notifications_by_student(student_id)
    unread_count = get_unread_notification_count(student_id)

    return render_template(
        "notifications.html",
        notifications_list=notifications_list,
        unread_count=unread_count,
    )


@app.route(
    "/notifications/<int:notification_id>/read",
    methods=["POST"]
)
@login_required
def mark_notification_read(notification_id):
    student_id = session["student_id"]

    updated = mark_notification_as_read(
        notification_id,
        student_id
    )

    if updated:
        flash("Notification marked as read.", "success")
    else:
        flash(
            "Notification not found or already marked as read.",
            "error"
        )

    return redirect(url_for("notifications"))


@app.route("/universities")
@login_required
def universities():
    allowed_countries = [
        "USA", "UK", "Canada", "Australia",
        "Germany", "Ireland", "Other"
    ]

    allowed_degrees = [
        "Bachelor's", "Master's", "PhD", "Diploma"
    ]

    country = request.args.get("country", "").strip()
    course = request.args.get("course", "").strip()
    degree_level = request.args.get("degree_level", "").strip()
    budget_text = request.args.get("max_tuition", "").strip()

    if country and country not in allowed_countries:
        country = ""

    if degree_level and degree_level not in allowed_degrees:
        degree_level = ""

    if len(course) > 100:
        course = course[:100]

    max_tuition = None
    budget_error = None

    if budget_text:
        try:
            max_tuition = int(budget_text)
            if not 0 <= max_tuition <= 100000000:
                raise ValueError
        except ValueError:
            max_tuition = None
            budget_error = (
                "Enter a valid tuition budget between "
                "0 and 100,000,000 INR."
            )

    results = search_universities(
        country=country,
        course=course,
        degree_level=degree_level,
        max_tuition=max_tuition,
    )

    if budget_error:
        flash(budget_error, "error")

    return render_template(
        "universities.html",
        universities=results,
        countries=allowed_countries,
        degree_levels=allowed_degrees,
        selected_country=country,
        selected_course=course,
        selected_degree=degree_level,
        selected_budget=budget_text,
    )


@app.route("/admin/reports")
@admin_required
def admin_reports():
    statistics = get_admin_statistics()

    return render_template(
        "admin_reports.html",
        statistics=statistics
    )

@app.route("/admin/students")
@admin_required
def admin_students():
    search_text = request.args.get("search", "").strip()

    # Limit the search input length.
    search_text = search_text[:100]

    students = search_students(search_text)

    return render_template(
        "admin_students.html",
        students=students,
        search_text=search_text
    )


@app.route("/admin/requests")
@admin_required
def admin_filtered_requests():
    allowed_statuses = ["Pending", "Approved", "Rejected"]

    status = request.args.get("status", "").strip()

    if status not in allowed_statuses:
        status = ""

    requests_list = filter_consultancy_requests(status)

    return render_template(
        "admin_filtered_requests.html",
        requests_list=requests_list,
        selected_status=status,
        statuses=allowed_statuses
    )


@app.route(
    "/admin/universities/<int:university_id>/verify",
    methods=["GET", "POST"]
)
@admin_required
def admin_verify_university(university_id):
    university = get_university_details(university_id)

    if university is None:
        flash("University record not found.", "error")
        return redirect(url_for("admin_universities"))

    if request.method == "POST":
        city = request.form.get("city", "").strip()
        tuition_currency = request.form.get(
            "tuition_currency", ""
        ).strip().upper()
        academic_year = request.form.get(
            "academic_year", ""
        ).strip()
        course_duration = request.form.get(
            "course_duration", ""
        ).strip()
        entry_requirements = request.form.get(
            "entry_requirements", ""
        ).strip()
        english_requirements = request.form.get(
            "english_requirements", ""
        ).strip()
        eligibility = request.form.get(
            "international_eligibility", "Unconfirmed"
        ).strip()
        source_url = request.form.get("source_url", "").strip()
        verification_status = request.form.get(
            "verification_status", "Unverified"
        ).strip()

        allowed_eligibility = {
            "Eligible", "Not eligible", "Unconfirmed"
        }
        allowed_verification = {"Verified", "Unverified"}

        if eligibility not in allowed_eligibility:
            flash("Invalid eligibility status.", "error")
        elif verification_status not in allowed_verification:
            flash("Invalid verification status.", "error")
        elif verification_status == "Verified" and not source_url.startswith(
            ("https://", "http://")
        ):
            flash(
                "Enter an official source URL before verification.",
                "error"
            )
        else:
            from datetime import date

            last_verified = (
                date.today().isoformat()
                if verification_status == "Verified"
                else ""
            )

            update_university_details(
                university_id=university_id,
                city=city,
                tuition_currency=tuition_currency,
                academic_year=academic_year,
                course_duration=course_duration,
                entry_requirements=entry_requirements,
                english_requirements=english_requirements,
                international_eligibility=eligibility,
                source_url=source_url,
                verification_status=verification_status,
                last_verified=last_verified
            )

            flash("University details updated.", "success")
            return redirect(
                url_for(
                    "admin_verify_university",
                    university_id=university_id
                )
            )

    university = get_university_details(university_id)

    return render_template(
        "admin_university_verify.html",
        university=university
    )


@app.route("/admin/universities")
@admin_required
def admin_universities():
    universities = get_all_universities()

    return render_template(
        "admin_universities.html",
        universities=universities
    )


   
@app.route("/admin/courses/add", methods=["GET", "POST"])
@admin_required
def admin_add_course():
    universities = get_all_universities()

    if request.method == "POST":
        try:
            university_id = int(
                request.form.get("university_id", "")
            )

            course_name = request.form.get(
                "course_name", ""
            ).strip()

            degree_level = request.form.get(
                "degree_level", ""
            ).strip()

            tuition_text = request.form.get(
                "annual_tuition", ""
            ).strip()

            if tuition_text:
                annual_tuition = float(tuition_text)
            else:
                annual_tuition = None

            tuition_currency = request.form.get(
                "tuition_currency", "INR"
            ).strip().upper()

            academic_year = request.form.get(
                "academic_year", ""
            ).strip()

            course_duration = request.form.get(
                "course_duration", ""
            ).strip()

            entry_requirements = request.form.get(
                "entry_requirements", ""
            ).strip()

            english_requirements = request.form.get(
                "english_requirements", ""
            ).strip()

            international_eligibility = request.form.get(
                "international_eligibility", "Unconfirmed"
            ).strip()

            if len(tuition_currency) != 3 or not tuition_currency.isalpha():
                raise ValueError(
                    "Enter a three-letter currency code, such as INR, USD, GBP, CAD, or AUD."
                )

            add_course(
                university_id=university_id,
                course_name=course_name,
                degree_level=degree_level,
                annual_tuition=annual_tuition,
                tuition_currency=tuition_currency,
                academic_year=academic_year,
                course_duration=course_duration,
                entry_requirements=entry_requirements,
                english_requirements=english_requirements,
                international_eligibility=international_eligibility,
            )

            flash(
                "Course added successfully. Its status is Unverified.",
                "success"
            )

            return redirect(url_for("admin_add_course"))

        except (ValueError, TypeError) as error:
            flash(str(error), "error")

    return render_template(
        "admin_add_course.html",
        universities=universities
    )

@app.route(
    "/admin/courses/<int:course_id>/edit",
    methods=["GET", "POST"]
)
@admin_required
def admin_edit_course(course_id):
    course = get_course_by_id(course_id)

    if course is None:
        flash("Course not found.", "error")
        return redirect(url_for("admin_courses"))

    if request.method == "POST":
        annual_tuition = request.form.get(
            "annual_tuition", type=float
        )
        tuition_currency = request.form.get(
            "tuition_currency", "INR"
        ).strip()
        academic_year = request.form.get(
            "academic_year", ""
        ).strip()
        course_duration = request.form.get(
            "course_duration", ""
        ).strip()
        entry_requirements = request.form.get(
            "entry_requirements", ""
        ).strip()
        english_requirements = request.form.get(
            "english_requirements", ""
        ).strip()
        international_eligibility = request.form.get(
            "international_eligibility", "Unconfirmed"
        ).strip()
        source_url = request.form.get(
            "source_url", ""
        ).strip()
        verification_status = request.form.get(
            "verification_status", "Unverified"
        ).strip()

        try:
            update_course_verification(
                course_id=course_id,
                annual_tuition=annual_tuition,
                tuition_currency=tuition_currency,
                academic_year=academic_year,
                course_duration=course_duration,
                entry_requirements=entry_requirements,
                english_requirements=english_requirements,
                international_eligibility=international_eligibility,
                source_url=source_url,
                verification_status=verification_status
            )

            flash("Course details updated successfully.", "success")
            return redirect(url_for("admin_courses"))

        except ValueError as error:
            flash(str(error), "error")

        course = get_course_by_id(course_id)

    return render_template(
        "admin_course_edit.html",
        course=course
    )

 
@app.route("/course-applications", methods=["GET", "POST"])
@login_required
def course_applications():
    student_id = session.get("student_id")

    if not student_id:
        flash("Please log in to apply for a course.", "error")
        return redirect(url_for("login"))

    if request.method == "POST":
        course_id = request.form.get("course_id", type=int)
        application_notes = request.form.get(
            "application_notes", ""
        ).strip()

        if not course_id:
            flash("Please select a valid course.", "error")
            return redirect(url_for("course_applications"))

        try:
            create_course_application(
                student_id=student_id,
                course_id=course_id,
                application_notes=application_notes
            )

            flash(
                "Your course application was submitted successfully.",
                "success"
            )

            return redirect(url_for("my_course_applications"))

        except ValueError as error:
            flash(str(error), "error")

    courses = get_all_courses()

    selected_course_id = request.args.get("course_id", type=int)

    valid_course_ids = {course["id"] for course in courses}

    if selected_course_id not in valid_course_ids:
        selected_course_id = None

    return render_template(
        "course_applications.html",
        courses=courses,
        selected_course_id=selected_course_id
    )


@app.route("/my-course-applications")
@login_required
def my_course_applications():
    student_id = session.get("student_id")

    if not student_id:
        flash("Please log in to view your applications.", "error")
        return redirect(url_for("login"))

    applications = get_course_applications_by_student(student_id)

    return render_template(
        "my_course_applications.html",
        applications=applications
    )

@app.route("/admin/courses")
@admin_required
def admin_courses():
    country = request.args.get("country", "").strip()
    course_name = request.args.get("course_name", "").strip()
    degree_level = request.args.get("degree_level", "").strip()
    verification_status = request.args.get(
        "verification_status", ""
    ).strip()

    allowed_countries = [
        "USA", "UK", "Canada", "Australia",
        "Germany", "Ireland", "Other"
    ]

    allowed_degrees = [
        "Bachelor's", "Master's", "PhD", "Diploma"
    ]

    allowed_statuses = ["Verified", "Unverified"]

    if country and country not in allowed_countries:
        country = ""

    if degree_level and degree_level not in allowed_degrees:
        degree_level = ""

    if verification_status not in allowed_statuses:
        verification_status = ""

    courses = search_courses(
        country=country,
        course_name=course_name,
        degree_level=degree_level,
    )

    # Apply the verification filter to the returned course records.
    if verification_status:
        courses = [
            course for course in courses
            if course["verification_status"] == verification_status
        ]

    return render_template(
        "admin_courses.html",
        courses=courses,
        countries=allowed_countries,
        degree_levels=allowed_degrees,
        selected_country=country,
        selected_course=course_name,
        selected_degree=degree_level,
        selected_status=verification_status,
    )

@app.route("/courses")
def courses():
    country = request.args.get("country", "").strip()
    course_name = request.args.get("course_name", "").strip()
    degree_level = request.args.get("degree_level", "").strip()
    verification_status = request.args.get(
        "verification_status", ""
    ).strip()

    allowed_countries = [
        "USA", "UK", "Canada", "Australia",
        "Germany", "Ireland", "Other"
    ]

    allowed_degrees = [
        "Bachelor's", "Master's", "PhD", "Diploma"
    ]

    allowed_statuses = ["Verified", "Unverified"]

    if country and country not in allowed_countries:
        country = ""

    if degree_level and degree_level not in allowed_degrees:
        degree_level = ""

    if verification_status not in allowed_statuses:
        verification_status = ""

    courses = search_courses(
        country=country,
        course_name=course_name,
        degree_level=degree_level,
    )

    if verification_status:
        courses = [
            course for course in courses
            if course["verification_status"] == verification_status
        ]

    return render_template(
        "courses.html",
        courses=courses,
        countries=allowed_countries,
        degree_levels=allowed_degrees,
        selected_country=country,
        selected_course=course_name,
        selected_degree=degree_level,
        selected_status=verification_status,
    )


if __name__ == "__main__":
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.run(debug=True)
