from django.conf import settings
from django.contrib.auth.hashers import make_password


def insert_django_user_statement(username, raw_password, api_key, configure_settings=True):
    # Determine user status and username based on input
    if username.endswith("/superuser"):
        is_superuser = True
        username = username.replace("/superuser", "")
    else:
        is_superuser = username == "supersurf"
    is_staff = "@surf.nl" in username or "@zooma.nl" in username or is_superuser
    email = username if "@" in username else ""
    # Configure Django during first run to be able to generate passwords hashes
    if configure_settings:
        settings.configure()
    # Generate password hashes
    hash_password = make_password(raw_password)
    escaped_password = hash_password.replace("$", r"\$")
    # Insert user and token into correct table
    user_insert = (
        "INSERT INTO auth_user "
        "(password, is_superuser, is_staff, is_active, username, first_name, last_name, email, date_joined) "
        f"VALUES ('{escaped_password}', {is_superuser}, {is_staff}, true, '{username}', '', '', '{email}', NOW())"
    )
    return (
        "WITH user_insert AS ("
        f"  {user_insert}"
        "   RETURNING id"
        ")"
        f"INSERT INTO authtoken_token "
        " (key, created, user_id) "
        f"VALUES ('{api_key}', NOW(), (SELECT id FROM user_insert))"

    )


def setup_database_statements(database_name, root_user, application_user, application_password, allow_tests=False):
    global_statements = [
        # Kill all database connections
        f"SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE "
        f"pg_stat_activity.datname = '{database_name}'",
        # Remove pre-existing objects
        f"DROP DATABASE {database_name}",
        f"DROP OWNED BY {application_user}",
        f"DROP USER {application_user}",
        # Create objects
        "CREATE SCHEMA IF NOT EXISTS public",
        f"CREATE DATABASE {database_name}",
        f"CREATE USER {application_user} WITH ENCRYPTED PASSWORD \'{application_password}\'",
    ]
    if allow_tests:
        global_statements.append(f"ALTER USER {application_user} CREATEDB")
    database_statements = [
        # Set permissions
        f"GRANT CONNECT ON DATABASE {database_name} TO {application_user}",
        f"GRANT USAGE ON SCHEMA public TO {application_user}",
        (f"ALTER DEFAULT PRIVILEGES FOR USER {root_user} IN SCHEMA public "
         f"GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {application_user}"),
        (f"ALTER DEFAULT PRIVILEGES FOR USER {root_user} IN SCHEMA public "
         f"GRANT SELECT, UPDATE, USAGE ON SEQUENCES TO {application_user}"),
    ]
    return global_statements, database_statements
