from typing import Dict, List, TypedDict

class StandardFieldDefinition(TypedDict):
    name: str
    label: str
    expected_type: str
    aliases: List[str]

STANDARD_FIELD_GROUPS: Dict[str, List[StandardFieldDefinition]] = {
    "Identity": [
        {"name": "volunteer_id", "label": "Volunteer ID", "expected_type": "identifier", "aliases": ["volunteer id", "id", "identifier", "record id", "uuid"]},
        {"name": "external_id", "label": "External ID", "expected_type": "identifier", "aliases": ["external id", "reference id"]},
    ],
    "Person": [
        {"name": "full_name", "label": "Full Name", "expected_type": "text", "aliases": ["volunteer name", "name", "full name"]},
        {"name": "first_name", "label": "First Name", "expected_type": "text", "aliases": ["first name", "given name"]},
        {"name": "last_name", "label": "Last Name", "expected_type": "text", "aliases": ["last name", "surname", "family name"]},
        {"name": "email", "label": "Email Address", "expected_type": "text", "aliases": ["email address", "email", "e-mail"]},
        {"name": "phone", "label": "Phone Number", "expected_type": "text", "aliases": ["mobile number", "phone", "phone number", "mobile", "contact number"]},
        {"name": "gender", "label": "Gender", "expected_type": "categorical", "aliases": ["gender", "sex"]},
        {"name": "date_of_birth", "label": "Date of Birth", "expected_type": "datetime", "aliases": ["dob", "date of birth", "birth date"]},
    ],
    "Location": [
        {"name": "address", "label": "Address", "expected_type": "text", "aliases": ["address", "street", "street address"]},
        {"name": "city", "label": "City", "expected_type": "text", "aliases": ["city", "town"]},
        {"name": "state", "label": "State/Province", "expected_type": "text", "aliases": ["state", "province", "region"]},
        {"name": "country", "label": "Country", "expected_type": "text", "aliases": ["country"]},
        {"name": "zip_code", "label": "Zip/Postal Code", "expected_type": "text", "aliases": ["zip", "zip code", "postal code", "postcode"]},
    ],
    "Volunteer": [
        {"name": "join_date", "label": "Join Date", "expected_type": "datetime", "aliases": ["joining date", "join date", "date joined"]},
        {"name": "volunteer_status", "label": "Volunteer Status", "expected_type": "categorical", "aliases": ["volunteer status", "status"]},
        {"name": "hours_contributed", "label": "Hours Contributed", "expected_type": "float", "aliases": ["hours contributed", "participation hours", "hours logged", "volunteer hours", "hours"]},
        {"name": "skills", "label": "Skills", "expected_type": "text", "aliases": ["skills", "expertise"]},
    ],
    "Campaign/Event": [
        {"name": "campaign_name", "label": "Campaign Name", "expected_type": "text", "aliases": ["campaign", "campaign name"]},
        {"name": "event_name", "label": "Event Name", "expected_type": "text", "aliases": ["event", "event name"]},
        {"name": "start_date", "label": "Start Date", "expected_type": "datetime", "aliases": ["start date"]},
        {"name": "end_date", "label": "End Date", "expected_type": "datetime", "aliases": ["end date"]},
    ],
    "Donation": [
        {"name": "donation_amount", "label": "Donation Amount", "expected_type": "float", "aliases": ["amount donated", "donation", "donation amount", "amount"]},
        {"name": "donation_date", "label": "Donation Date", "expected_type": "datetime", "aliases": ["donation date", "date donated"]},
        {"name": "amount_raised", "label": "Amount Raised", "expected_type": "float", "aliases": ["funds raised", "amount raised"]},
        {"name": "donor_type", "label": "Donor Type", "expected_type": "categorical", "aliases": ["donor type", "donor category"]},
    ],
    "Internship": [
        {"name": "internship_role", "label": "Internship Role", "expected_type": "text", "aliases": ["role", "internship role", "position"]},
        {"name": "department", "label": "Department", "expected_type": "categorical", "aliases": ["department", "team"]},
        {"name": "performance_score", "label": "Performance Score", "expected_type": "float", "aliases": ["score", "performance score", "rating"]},
    ],
    "Feedback/Social": [
        {"name": "feedback_rating", "label": "Feedback Rating", "expected_type": "float", "aliases": ["rating", "feedback", "satisfaction"]},
        {"name": "social_handle", "label": "Social Handle", "expected_type": "text", "aliases": ["social", "twitter", "instagram", "linkedin", "handle"]},
    ],
    "Generic": [
        {"name": "notes", "label": "Notes", "expected_type": "text", "aliases": ["notes", "comments", "description"]},
    ]
}

def get_all_standard_fields() -> List[StandardFieldDefinition]:
    fields = []
    for group in STANDARD_FIELD_GROUPS.values():
        fields.extend(group)
    return fields

def get_field_by_name(name: str) -> StandardFieldDefinition | None:
    for field in get_all_standard_fields():
        if field["name"] == name:
            return field
    return None
