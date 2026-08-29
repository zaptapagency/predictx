"""
The project's clock.

`datetime.utcnow()` is deprecated and slated for removal, but the obvious
replacement — `datetime.now(timezone.utc)` — is NOT a drop-in here. It returns
an aware datetime, while every DateTime column in this schema is naive (there
is not a single `DateTime(timezone=True)` in app/db). Mixing the two raises
"can't compare offset-naive and offset-aware datetimes" the first time a query
filters on a stored timestamp.

So `utcnow()` keeps the existing contract — the current UTC time, naive — and
just stops using the deprecated call to get there. Behaviour is unchanged;
only the deprecation goes away.

Making the schema timezone-aware would be a better end state, but it is a
migration over live data, not a search-and-replace, and it is not what this
change is for.
"""

from datetime import datetime, timezone


def utcnow() -> datetime:
    """Current UTC time as a naive datetime, matching the DB columns."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
