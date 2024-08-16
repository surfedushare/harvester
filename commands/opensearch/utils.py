from search_client.opensearch import OpenSearchClientBuilder


def get_remote_search_client(conn, silent=False):
    """
    Returns the Open Search client connected through port forwarding settings
    """
    host = conn.config.opensearch.host
    http_auth = ("supersurf", conn.config.secrets.opensearch.password,)
    return OpenSearchClientBuilder.from_host(host, http_auth=http_auth).build(check_connection=not silent)
