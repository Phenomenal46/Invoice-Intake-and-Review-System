"""Simple MongoDB helpers used across the app.

This module creates a single shared :class:`MongoClient` instance on
first use and exposes convenience functions to get the configured
database and the ``documents`` collection the app uses.

The comments below explain the slightly tricky pieces (global
variable, lazy initialization, subscription-style access like
``client[db_name]``) in an easy-to-read way.
"""

from pymongo import MongoClient

from app.config import settings

# Module-level cache for the MongoClient. Start as None to indicate
# "no client has been created yet".
# Type annotation: either a MongoClient instance or None.
_client: MongoClient | None = None


def get_client() -> MongoClient:
    """Return a shared MongoClient instance.

    - Uses a global variable so the same client is reused across calls.
        - The first call constructs the client using the resolved URI from
            ``settings.resolved_mongodb_uri`` (this is called "lazy initialization").
    - Reusing the client is important: MongoClient manages a pool of
      network connections and is intended to be created once and used
      throughout the app's lifetime.

    Example:
        client = get_client()
        # Now you can use `client` to get a database or collection.
    """
    global _client  # allows assignment to the module-level variable
    if _client is None:
        # Create the client only once. If the URI is invalid or the
        # server is unreachable, creating or using the client later
        # may raise exceptions — higher-level code should handle that.
        _client = MongoClient(settings.resolved_mongodb_uri)
    return _client


def get_db():
    """Return the configured :class:`Database` object.

    ``get_client()`` returns a MongoClient. Indexing the client like
    ``client[db_name]`` returns a Database object for that name. This
    is a convenient shorthand instead of calling
    ``client.get_database(db_name)``.

    Example:
        db = get_db()
        # Use `db` to access collections: db['documents']
    """
    return get_client()[settings.mongodb_db]


def get_documents_collection():
    """Return the documents collection used by the app."""
    db = get_db()
    return db["documents"]
