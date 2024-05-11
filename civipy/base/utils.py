from typing import TYPE_CHECKING
from civipy.exceptions import NoResultError, NonUniqueResultError, CiviProgrammingError

if TYPE_CHECKING:
    from civipy.interface import CiviValue, CiviResponse


def get_unique(response: "CiviResponse") -> "CiviValue":
    """Enforce that exactly one record was returned in `response` and return just the record."""
    if not response or "count" not in response or "values" not in response:
        raise CiviProgrammingError(f"Unexpected response {response}")
    record_id = next(iter(response["values"].keys())) if isinstance(response["values"], dict) else 0

    # Raise exception if `response` does not have exactly one record.
    count = response["count"]
    if count == 0:
        raise NoResultError("No results in response.")
    if count > 1 and not is_identical(response["values"]):
        raise NonUniqueResultError(f"Response is not unique, has {count} results.")

    return response["values"][record_id]


def is_identical(values: list["CiviValue"] | dict[str, "CiviValue"]) -> bool:
    """Check if multiple returned values are the same item and can be treated as unique."""
    # I have experienced the V4 REST API returning two instances of a record. The request was
    # `CiviContact.find(select=["*", "email_primary.email"], id=11722)`. This was likely due
    # to the join to the email table, so I'm treating this as an implicit "select distinct"
    if isinstance(values, dict):
        values = list(values.values())
    first = values[0]
    return all((value == first for value in values[1:]))
