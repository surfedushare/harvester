class DeletePolicies:
    """
    Details: http://www.openarchives.org/OAI/openarchivesprotocol.html#DeletedRecords
    """
    NO = "no"
    PERSISTENT = "persistent"
    TRANSIENT = "transient"


DELETE_POLICY_CHOICES = [
    (value, attr.lower().capitalize())
    for attr, value in sorted(DeletePolicies.__dict__.items()) if not attr.startswith("_")
]


HIGHER_EDUCATION_LEVELS = {
    "HBO": 2,
    "WO": 3,
}

MBO_EDUCATIONAL_LEVELS = {
    "BVE",
    "MBO",
    "Beroepsonderwijs en Volwasseneneducatie",
    "Volwasseneneducatie",
}
