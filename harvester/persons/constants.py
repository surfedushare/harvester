SEED_DEFAULTS = {
    # Essential keys for functioning of the system
    "state": None,
    "set": None,
    "external_id": None,
    "provider": None,
    # Generic metadata
    "skills": [],
    "organizations": [],
    "is_employed": None,
    "job_title": None,
    # Author metadata
    # The author metadata is special in that it is required to fulfill contract agreements
    # between publishers and authors.
    # Publishers are bound by contract to publish content with mentioning the (pseudonym) author.
    # Therefor "consent" isn't the applicable GDPR legal base, but "contract".
    # See this document on page 13 for more details on the "contract" legal bases: https://www.dataprotection.ie/sites/default/files/uploads/2020-04/Guidance%20on%20Legal%20Bases.pdf  # noqa: E501
    "author": {
        "name": None,
        "first_name": None,
        "last_name": None,
        "prefix": None,
        "initials": None,
        "isni": None,
    },
    # Sensitive metadata that will require "consent". Note that this is assumed to be handled by (Publinova) contracts.
    "sensitive": {
        "description": None,  # free text field is here "just in case"
        "email": None,
        "phone": None,
        "photo_url": None,
        "socials": []
    },
    # Research based metadata
    "researcher": {
        "title": None,  # academic title
        "themes": [],
        # Below are identifiers that are used in the context of (pseudonym) authors, see author metadata for details
        "dai": None,
        "orcid": None,
    }
}
