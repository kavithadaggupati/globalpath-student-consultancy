
from database import (
    initialize_database,
    initialize_universities_table,
    add_university,
    count_universities,
)

initialize_database()
initialize_universities_table()

if count_universities() == 0:
    universities = [
        (
            "University of Example California",
            "USA",
            "Computer Science",
            "Master's",
            2500000,
            "https://www.example.com",
            "Sample university record for project demonstration."
        ),
        (
            "University of Example London",
            "UK",
            "Business Management",
            "Master's",
            2200000,
            "https://www.example.com",
            "Sample university record for project demonstration."
        ),
        (
            "University of Example Toronto",
            "Canada",
            "Computer Science",
            "Master's",
            1800000,
            "https://www.example.com",
            "Sample university record for project demonstration."
        ),
        (
            "University of Example Sydney",
            "Australia",
            "Information Technology",
            "Master's",
            2000000,
            "https://www.example.com",
            "Sample university record for project demonstration."
        ),
        (
            "University of Example Berlin",
            "Germany",
            "Computer Science",
            "Bachelor's",
            1200000,
            "https://www.example.com",
            "Sample university record for project demonstration."
        ),
        (
            "University of Example Dublin",
            "Ireland",
            "Data Science",
            "Master's",
            1700000,
            "https://www.example.com",
            "Sample university record for project demonstration."
        ),
    ]

    for university in universities:
        add_university(*university)

    print("Sample university records inserted successfully.")
else:
    print("University records already exist. No records were added.")

print("Total university records:", count_universities())
