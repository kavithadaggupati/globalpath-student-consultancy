
import sqlite3
from pathlib import Path
from contextlib import contextmanager

# Store the database beside this Python file.
BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "student_consultancy.db"


def get_connection():
    """Open a connection to the SQLite database."""
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection

@contextmanager
def database_connection():
    connection = get_connection()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

def initialize_database():
    """Create the students table if it does not exist."""
    with database_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL COLLATE NOCASE UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


def create_student(full_name, email, password_hash):
    """Save a new student account."""
    with database_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO students (full_name, email, password_hash)
            VALUES (?, ?, ?)
            """,
            (full_name, email, password_hash)
        )
        return cursor.lastrowid


def get_student_by_email(email):
    """Find a student by email address."""
    with database_connection() as connection:
        return connection.execute(
            "SELECT * FROM students WHERE email = ?",
            (email,)
        ).fetchone()


def get_student_by_id(student_id):
    """Find a student by their database ID."""
    with database_connection() as connection:
        return connection.execute(
            "SELECT * FROM students WHERE id = ?",
            (student_id,)
        ).fetchone()


def initialize_profile_table():
    """Create the study-abroad profile table."""
    with database_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS student_profiles (
                student_id INTEGER PRIMARY KEY,
                qualification TEXT NOT NULL DEFAULT '',
                grades TEXT NOT NULL DEFAULT '',
                degree_level TEXT NOT NULL DEFAULT '',
                preferred_country TEXT NOT NULL DEFAULT '',
                preferred_course TEXT NOT NULL DEFAULT '',
                budget TEXT NOT NULL DEFAULT '',
                intake_year TEXT NOT NULL DEFAULT '',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id)
                    REFERENCES students(id)
                    ON DELETE CASCADE
            )
        """)


def get_student_profile(student_id):
    """Retrieve one student's profile."""
    with database_connection() as connection:
        return connection.execute(
            """
            SELECT * FROM student_profiles
            WHERE student_id = ?
            """,
            (student_id,)
        ).fetchone()


def save_student_profile(
    student_id,
    qualification,
    grades,
    degree_level,
    preferred_country,
    preferred_course,
    budget,
    intake_year
):
    """Create or update a student's profile."""
    with database_connection() as connection:
        connection.execute(
            """
            INSERT INTO student_profiles (
                student_id, qualification, grades,
                degree_level, preferred_country,
                preferred_course, budget, intake_year
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(student_id) DO UPDATE SET
                qualification = excluded.qualification,
                grades = excluded.grades,
                degree_level = excluded.degree_level,
                preferred_country = excluded.preferred_country,
                preferred_course = excluded.preferred_course,
                budget = excluded.budget,
                intake_year = excluded.intake_year,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                student_id, qualification, grades,
                degree_level, preferred_country,
                preferred_course, budget, intake_year
            )
        )


def initialize_consultancy_table():
    with database_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS consultancy_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                service_type TEXT NOT NULL,
                appointment_date TEXT NOT NULL,
                appointment_time TEXT NOT NULL,
                message TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'Pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id)
                    REFERENCES students(id)
                    ON DELETE CASCADE
            )
        """)


def create_consultancy_request(
    student_id, service_type, appointment_date,
    appointment_time, message
):
    with database_connection() as connection:
        cursor = connection.execute("""
            INSERT INTO consultancy_requests (
                student_id, service_type, appointment_date,
                appointment_time, message
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            student_id, service_type, appointment_date,
            appointment_time, message
        ))
        return cursor.lastrowid


def get_requests_by_student(student_id):
    with database_connection() as connection:
        return connection.execute("""
            SELECT *
            FROM consultancy_requests
            WHERE student_id = ?
            ORDER BY created_at DESC, id DESC
        """, (student_id,)).fetchall()

def initialize_admin_table():
    with database_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL COLLATE NOCASE UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


def create_admin(email, password_hash):
    with database_connection() as connection:
        connection.execute(
            """
            INSERT INTO admins (email, password_hash)
            VALUES (?, ?)
            """,
            (email.strip().lower(), password_hash)
        )


def get_admin_by_email(email):
    with database_connection() as connection:
        return connection.execute(
            "SELECT * FROM admins WHERE email = ?",
            (email.strip().lower(),)
        ).fetchone()


def get_all_consultancy_requests():
    with database_connection() as connection:
        return connection.execute("""
            SELECT
                cr.id,
                cr.student_id,
                cr.service_type,
                cr.appointment_date,
                cr.appointment_time,
                cr.message,
                cr.status,
                cr.created_at,
                s.full_name,
                s.email
            FROM consultancy_requests AS cr
            JOIN students AS s ON s.id = cr.student_id
            ORDER BY cr.created_at DESC, cr.id DESC
        """).fetchall()


def update_consultancy_status(request_id, status):
    with database_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE consultancy_requests
            SET status = ?
            WHERE id = ?
            """,
            (status, request_id)
        )
        return cursor.rowcount

def initialize_documents_table():
    with database_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS student_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                document_type TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                stored_filename TEXT NOT NULL UNIQUE,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id)
                    REFERENCES students(id)
                    ON DELETE CASCADE
            )
        """)


def save_student_document(
    student_id, document_type, original_filename, stored_filename
):
    with database_connection() as connection:
        cursor = connection.execute("""
            INSERT INTO student_documents (
                student_id, document_type,
                original_filename, stored_filename
            )
            VALUES (?, ?, ?, ?)
        """, (
            student_id,
            document_type,
            original_filename,
            stored_filename,
        ))
        return cursor.lastrowid


def get_documents_by_student(student_id):
    with database_connection() as connection:
        return connection.execute("""
            SELECT *
            FROM student_documents
            WHERE student_id = ?
            ORDER BY uploaded_at DESC, id DESC
        """, (student_id,)).fetchall()


def get_student_document(document_id, student_id):
    with database_connection() as connection:
        return connection.execute("""
            SELECT *
            FROM student_documents
            WHERE id = ? AND student_id = ?
        """, (document_id, student_id)).fetchone()

def initialize_notifications_table():
    with database_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                request_id INTEGER,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                is_read INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id)
                    REFERENCES students(id)
                    ON DELETE CASCADE,
                FOREIGN KEY (request_id)
                    REFERENCES consultancy_requests(id)
                    ON DELETE SET NULL
            )
        """)


def create_notification(
    student_id, request_id, title, message
):
    with database_connection() as connection:
        cursor = connection.execute("""
            INSERT INTO notifications (
                student_id, request_id, title, message
            )
            VALUES (?, ?, ?, ?)
        """, (
            student_id,
            request_id,
            title,
            message,
        ))
        return cursor.lastrowid


def get_notifications_by_student(student_id):
    with database_connection() as connection:
        return connection.execute("""
            SELECT *
            FROM notifications
            WHERE student_id = ?
            ORDER BY created_at DESC, id DESC
        """, (student_id,)).fetchall()


def get_unread_notification_count(student_id):
    with database_connection() as connection:
        result = connection.execute("""
            SELECT COUNT(*) AS total
            FROM notifications
            WHERE student_id = ? AND is_read = 0
        """, (student_id,)).fetchone()

        return result["total"]


def mark_notification_as_read(notification_id, student_id):
    with database_connection() as connection:
        cursor = connection.execute("""
            UPDATE notifications
            SET is_read = 1
            WHERE id = ? AND student_id = ?
        """, (notification_id, student_id))

        return cursor.rowcount

def get_consultancy_request_by_id(request_id):
    with database_connection() as connection:
        return connection.execute("""
            SELECT id, student_id, status
            FROM consultancy_requests
            WHERE id = ?
        """, (request_id,)).fetchone()

def initialize_universities_table():
    with database_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS universities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                country TEXT NOT NULL,
                course TEXT NOT NULL,
                degree_level TEXT NOT NULL,
                annual_tuition INTEGER NOT NULL,
                official_website TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT ''
            )
        """)


def add_university(
    name, country, course, degree_level,
    annual_tuition, official_website, description
):
    with database_connection() as connection:
        connection.execute("""
            INSERT INTO universities (
                name, country, course, degree_level,
                annual_tuition, official_website, description
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            name, country, course, degree_level,
            annual_tuition, official_website, description
        ))


def search_universities(
    country="", course="", degree_level="",
    max_tuition=None
):
    query = "SELECT * FROM universities WHERE 1=1"
    parameters = []

    if country:
        query += " AND country = ?"
        parameters.append(country)

    if course:
        query += " AND course LIKE ?"
        parameters.append(f"%{course}%")

    if degree_level:
        query += " AND degree_level = ?"
        parameters.append(degree_level)

    if max_tuition is not None:
        query += " AND annual_tuition <= ?"
        parameters.append(max_tuition)

    query += " ORDER BY annual_tuition ASC, name ASC"

    with database_connection() as connection:
        return connection.execute(
            query, parameters
        ).fetchall()


def get_university_by_id(university_id):
    with database_connection() as connection:
        return connection.execute("""
            SELECT *
            FROM universities
            WHERE id = ?
        """, (university_id,)).fetchone()


def count_universities():
    with database_connection() as connection:
        result = connection.execute(
            "SELECT COUNT(*) AS total FROM universities"
        ).fetchone()
        return result["total"]

def get_admin_statistics():
    with database_connection() as connection:

        total_students = connection.execute(
            "SELECT COUNT(*) AS total FROM students"
        ).fetchone()["total"]

        total_requests = connection.execute(
            "SELECT COUNT(*) AS total FROM consultancy_requests"
        ).fetchone()["total"]

        pending_requests = connection.execute(
            """
            SELECT COUNT(*) AS total
            FROM consultancy_requests
            WHERE status = 'Pending'
            """
        ).fetchone()["total"]

        approved_requests = connection.execute(
            """
            SELECT COUNT(*) AS total
            FROM consultancy_requests
            WHERE status = 'Approved'
            """
        ).fetchone()["total"]

        rejected_requests = connection.execute(
            """
            SELECT COUNT(*) AS total
            FROM consultancy_requests
            WHERE status = 'Rejected'
            """
        ).fetchone()["total"]

        total_documents = connection.execute(
            "SELECT COUNT(*) AS total FROM student_documents"
        ).fetchone()["total"]

        total_notifications = connection.execute(
            "SELECT COUNT(*) AS total FROM notifications"
        ).fetchone()["total"]

        total_universities = connection.execute(
            "SELECT COUNT(*) AS total FROM universities"
        ).fetchone()["total"]

        return {
            "total_students": total_students,
            "total_requests": total_requests,
            "pending_requests": pending_requests,
            "approved_requests": approved_requests,
            "rejected_requests": rejected_requests,
            "total_documents": total_documents,
            "total_notifications": total_notifications,
            "total_universities": total_universities,
        }


def search_students(search_text=""):
    query = """
        SELECT id, full_name, email
        FROM students
        WHERE full_name LIKE ? OR email LIKE ?
        ORDER BY full_name ASC
    """

    search_pattern = f"%{search_text}%"

    with database_connection() as connection:
        return connection.execute(
            query,
            (search_pattern, search_pattern)
        ).fetchall()


def filter_consultancy_requests(status=""):
    query = """
        SELECT
            cr.*,
            s.full_name AS student_name,
            s.email AS student_email
        FROM consultancy_requests AS cr
        JOIN students AS s ON cr.student_id = s.id
    """

    parameters = []

    if status in ("Pending", "Approved", "Rejected"):
        query += " WHERE cr.status = ?"
        parameters.append(status)

    query += " ORDER BY cr.id DESC"

    with database_connection() as connection:
        return connection.execute(
            query, parameters
        ).fetchall()

def upgrade_universities_table():
    new_columns = {
        "city": "TEXT NOT NULL DEFAULT ''",
        "tuition_currency": "TEXT NOT NULL DEFAULT 'INR'",
        "academic_year": "TEXT NOT NULL DEFAULT ''",
        "course_duration": "TEXT NOT NULL DEFAULT ''",
        "entry_requirements": "TEXT NOT NULL DEFAULT ''",
        "english_requirements": "TEXT NOT NULL DEFAULT ''",
        "international_eligibility": "TEXT NOT NULL DEFAULT 'Unconfirmed'",
        "source_url": "TEXT NOT NULL DEFAULT ''",
        "verification_status": "TEXT NOT NULL DEFAULT 'Unverified'",
        "last_verified": "TEXT NOT NULL DEFAULT ''",
    }

    with database_connection() as connection:
        existing_columns = {
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(universities)"
            ).fetchall()
        }

        for column_name, column_type in new_columns.items():
            if column_name not in existing_columns:
                connection.execute(
                    f"ALTER TABLE universities ADD COLUMN "
                    f"{column_name} {column_type}"
                )

def update_university_details(
    university_id,
    city="",
    tuition_currency="",
    academic_year="",
    course_duration="",
    entry_requirements="",
    english_requirements="",
    international_eligibility="Unconfirmed",
    source_url="",
    verification_status="Unverified",
    last_verified=""
):
    allowed_statuses = {"Verified", "Unverified"}

    if verification_status not in allowed_statuses:
        raise ValueError("Invalid verification status.")

    if international_eligibility not in {
        "Eligible", "Not eligible", "Unconfirmed"
    }:
        raise ValueError("Invalid eligibility status.")

    with database_connection() as connection:
        connection.execute(
            """
            UPDATE universities
            SET city = ?,
                tuition_currency = ?,
                academic_year = ?,
                course_duration = ?,
                entry_requirements = ?,
                english_requirements = ?,
                international_eligibility = ?,
                source_url = ?,
                verification_status = ?,
                last_verified = ?
            WHERE id = ?
            """,
            (
                city,
                tuition_currency,
                academic_year,
                course_duration,
                entry_requirements,
                english_requirements,
                international_eligibility,
                source_url,
                verification_status,
                last_verified,
                university_id
            )
        )


def get_all_universities():
    with database_connection() as connection:
        return connection.execute(
            """
            SELECT *
            FROM universities
            ORDER BY country, name
            """
        ).fetchall()


def get_university_details(university_id):
    with database_connection() as connection:
        return connection.execute(
            """
            SELECT *
            FROM universities
            WHERE id = ?
            """,
            (university_id,)
        ).fetchone()

def initialize_courses_table():
    """Create a separate table for university courses."""

    with database_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                university_id INTEGER NOT NULL,
                course_name TEXT NOT NULL,
                degree_level TEXT NOT NULL,
                annual_tuition REAL,
                tuition_currency TEXT NOT NULL DEFAULT 'INR',
                academic_year TEXT NOT NULL DEFAULT '',
                course_duration TEXT NOT NULL DEFAULT '',
                entry_requirements TEXT NOT NULL DEFAULT '',
                english_requirements TEXT NOT NULL DEFAULT '',
                international_eligibility TEXT NOT NULL
                    DEFAULT 'Unconfirmed',
                source_url TEXT NOT NULL DEFAULT '',
                verification_status TEXT NOT NULL
                    DEFAULT 'Unverified',
                last_verified TEXT NOT NULL DEFAULT '',
                FOREIGN KEY (university_id)
                    REFERENCES universities(id)
                    ON DELETE CASCADE
            )
        """)


def get_all_courses():
    """Return courses with their university information."""

    with database_connection() as connection:
        return connection.execute("""
            SELECT
                courses.*,
                universities.name AS university_name,
                universities.country AS university_country
            FROM courses
            JOIN universities
                ON courses.university_id = universities.id
            ORDER BY universities.country, universities.name,
                     courses.course_name
        """).fetchall()


def search_courses(country="", course_name="", degree_level=""):
    """Search courses by country, name, and degree level."""

    query = """
        SELECT
            courses.*,
            universities.name AS university_name,
            universities.country AS university_country
        FROM courses
        JOIN universities
            ON courses.university_id = universities.id
        WHERE 1 = 1
    """

    parameters = []

    if country:
        query += " AND universities.country = ?"
        parameters.append(country)

    if course_name:
        query += " AND courses.course_name LIKE ?"
        parameters.append("%" + course_name + "%")

    if degree_level:
        query += " AND courses.degree_level = ?"
        parameters.append(degree_level)

    query += """
        ORDER BY universities.country, universities.name,
                 courses.course_name
    """

    with database_connection() as connection:
        return connection.execute(query, parameters).fetchall()

def add_course(
    university_id,
    course_name,
    degree_level,
    annual_tuition=None,
    tuition_currency="INR",
    academic_year="",
    course_duration="",
    entry_requirements="",
    english_requirements="",
    international_eligibility="Unconfirmed",
    source_url="",
    verification_status="Unverified",
):
    """Save a course linked to an existing university."""

    allowed_degrees = {
        "Bachelor's", "Master's", "PhD", "Diploma"
    }

    allowed_eligibility = {
        "Eligible", "Not eligible", "Unconfirmed"
    }

    # New records must start unverified.
    if verification_status != "Unverified":
        raise ValueError(
            "New courses must be marked Unverified."
        )

    if degree_level not in allowed_degrees:
        raise ValueError("Invalid degree level.")

    if international_eligibility not in allowed_eligibility:
        raise ValueError("Invalid eligibility status.")

    if not course_name.strip():
        raise ValueError("Course name is required.")

    if not tuition_currency.strip():
        raise ValueError("Tuition currency is required.")

    if annual_tuition is not None and annual_tuition < 0:
        raise ValueError("Tuition cannot be negative.")

    with database_connection() as connection:
        university = connection.execute(
            "SELECT id FROM universities WHERE id = ?",
            (university_id,)
        ).fetchone()

        if university is None:
            raise ValueError("Please select a valid university.")

        connection.execute(
            """
            INSERT INTO courses (
                university_id,
                course_name,
                degree_level,
                annual_tuition,
                tuition_currency,
                academic_year,
                course_duration,
                entry_requirements,
                english_requirements,
                international_eligibility,
                source_url,
                verification_status,
                last_verified
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                university_id,
                course_name.strip(),
                degree_level,
                annual_tuition,
                tuition_currency.strip().upper(),
                academic_year.strip(),
                course_duration.strip(),
                entry_requirements.strip(),
                english_requirements.strip(),
                international_eligibility,
                source_url.strip(),
                "Unverified",
                ""
            )
        )

def get_course_by_id(course_id):
    """Get one course with its university details."""

    with database_connection() as connection:
        return connection.execute(
            """
            SELECT
                courses.*,
                universities.name AS university_name,
                universities.country AS university_country
            FROM courses
            JOIN universities
                ON courses.university_id = universities.id
            WHERE courses.id = ?
            """,
            (course_id,)
        ).fetchone()


def update_course_verification(
    course_id,
    annual_tuition,
    tuition_currency,
    academic_year,
    course_duration,
    entry_requirements,
    english_requirements,
    international_eligibility,
    source_url,
    verification_status,
):
    """Update programme details and verification status."""

    allowed_eligibility = {
        "Eligible", "Not eligible", "Unconfirmed"
    }

    allowed_statuses = {"Verified", "Unverified"}

    if international_eligibility not in allowed_eligibility:
        raise ValueError("Invalid eligibility status.")

    if verification_status not in allowed_statuses:
        raise ValueError("Invalid verification status.")

    if annual_tuition is not None and annual_tuition < 0:
        raise ValueError("Tuition cannot be negative.")

    if not tuition_currency or len(tuition_currency) != 3:
        raise ValueError("Enter a valid three-letter currency code.")

    source_url = source_url.strip()

    if verification_status == "Verified":
        if not source_url.startswith(("https://", "http://")):
            raise ValueError(
                "A programme source URL is required for verification."
            )

        if international_eligibility == "Unconfirmed":
            raise ValueError(
                "Confirm international eligibility before verification."
            )

    from datetime import date

    last_verified = (
        date.today().isoformat()
        if verification_status == "Verified"
        else ""
    )

    with database_connection() as connection:
        connection.execute(
            """
            UPDATE courses
            SET annual_tuition = ?,
                tuition_currency = ?,
                academic_year = ?,
                course_duration = ?,
                entry_requirements = ?,
                english_requirements = ?,
                international_eligibility = ?,
                source_url = ?,
                verification_status = ?,
                last_verified = ?
            WHERE id = ?
            """,
            (
                annual_tuition,
                tuition_currency.upper(),
                academic_year.strip(),
                course_duration.strip(),
                entry_requirements.strip(),
                english_requirements.strip(),
                international_eligibility,
                source_url,
                verification_status,
                last_verified,
                course_id,
            )
        )


def initialize_course_applications_table():
    """Create the student course applications table."""

    with database_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS course_applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                course_id INTEGER NOT NULL,
                application_notes TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'Submitted',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (student_id)
                    REFERENCES students(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (course_id)
                    REFERENCES courses(id)
                    ON DELETE CASCADE
            )
        """)

def create_course_application(student_id, course_id, application_notes=""):
    """Create a course application for a student."""

    with database_connection() as connection:
        # Check whether the student exists.
        student = connection.execute(
            "SELECT id FROM students WHERE id = ?",
            (student_id,)
        ).fetchone()

        if student is None:
            raise ValueError("Student account was not found.")

        # Check whether the course exists.
        course = connection.execute(
            "SELECT id FROM courses WHERE id = ?",
            (course_id,)
        ).fetchone()

        if course is None:
            raise ValueError("The selected course was not found.")

        # Prevent duplicate applications for the same course.
        existing_application = connection.execute(
            """
            SELECT id
            FROM course_applications
            WHERE student_id = ? AND course_id = ?
            """,
            (student_id, course_id)
        ).fetchone()

        if existing_application is not None:
            raise ValueError(
                "You have already applied for this course."
            )

        # Save the application.
        cursor = connection.execute(
            """
            INSERT INTO course_applications (
                student_id,
                course_id,
                application_notes,
                status
            )
            VALUES (?, ?, ?, 'Submitted')
            """,
            (
                student_id,
                course_id,
                application_notes.strip()
            )
        )

        return cursor.lastrowid


def get_course_applications_by_student(student_id):
    """Retrieve all course applications submitted by a student."""

    with database_connection() as connection:
        applications = connection.execute(
            """
            SELECT
                ca.id,
                ca.student_id,
                ca.course_id,
                ca.application_notes,
                ca.status,
                ca.created_at,
                ca.updated_at,
                c.course_name,
                c.degree_level,
                c.annual_tuition,
                c.tuition_currency,
                c.course_duration,
                c.verification_status,
                u.name AS university_name,
                u.country AS university_country
            FROM course_applications AS ca
            JOIN courses AS c
                ON ca.course_id = c.id
            JOIN universities AS u
                ON c.university_id = u.id
            WHERE ca.student_id = ?
            ORDER BY ca.created_at DESC, ca.id DESC
            """,
            (student_id,)
        ).fetchall()

        return applications



def get_all_course_applications():
    """Retrieve all course applications for the admin dashboard."""

    with database_connection() as connection:
        applications = connection.execute(
            """
            SELECT
                ca.id,
                ca.student_id,
                ca.course_id,
                ca.application_notes,
                ca.status,
                ca.created_at,
                ca.updated_at,
                c.course_name,
                c.degree_level,
                u.name AS university_name,
                u.country AS university_country
            FROM course_applications AS ca
            JOIN courses AS c
                ON ca.course_id = c.id
            JOIN universities AS u
                ON c.university_id = u.id
            ORDER BY ca.created_at DESC, ca.id DESC
            """
        ).fetchall()

        return applications

def update_course_application_status(application_id, status):
    """Update the status of a student's course application."""

    allowed_statuses = {
        "Submitted",
        "Under Review",
        "Accepted",
        "Rejected",
    }

    if status not in allowed_statuses:
        raise ValueError("Invalid course application status.")

    with database_connection() as connection:
        application = connection.execute(
            """
            SELECT id
            FROM course_applications
            WHERE id = ?
            """,
            (application_id,)
        ).fetchone()

        if application is None:
            raise ValueError("Course application was not found.")

        connection.execute(
            """
            UPDATE course_applications
            SET status = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (status, application_id)
        )

def get_course_application_by_id(application_id):
    """Retrieve a course application and its student details."""

    with database_connection() as connection:
        application = connection.execute(
            """
            SELECT
                ca.id,
                ca.student_id,
                ca.course_id,
                ca.status,
                c.course_name,
                u.name AS university_name
            FROM course_applications AS ca
            JOIN courses AS c
                ON ca.course_id = c.id
            JOIN universities AS u
                ON c.university_id = u.id
            WHERE ca.id = ?
            """,
            (application_id,)
        ).fetchone()

        return application
