from typing import TypedDict, Literal, Callable

CiviValue = dict[str, int | str]
CiviV3Request = CiviValue


class CiviV3ResponseOptional(TypedDict, total=False):
    id: int
    error_message: str
    undefined_fields: list[str]


class CiviV3Response(CiviV3ResponseOptional):
    is_error: Literal[0, 1]
    version: Literal[3]
    count: int
    values: list[CiviValue] | dict[str, CiviValue] | CiviValue


class CiviV4Request(TypedDict, total=False):
    select: list[str]
    join: list[list[str | list[str]]]
    translationMode: Literal["fuzzy", "strict"]
    where: list[list[str | int]]
    values: list[CiviValue]
    orderBy: dict[str, Literal["ASC", "DESC"]]
    limit: int
    offset: int
    language: str
    chain: dict[str, list["str | CiviV4Request"]]
    groupBy: list[str]
    having: list[list[str | int]]
    debug: bool


class CiviV4ResponseOptional(TypedDict, total=False):
    error_code: int
    error_message: str
    debug: dict[str, str | list[str]]


class CiviV4Response(CiviV4ResponseOptional):
    entity: str
    action: str
    version: Literal[4]
    count: int
    countFetched: int
    values: list[CiviValue]


CiviResponse = CiviV3Response | CiviV4Response


class BaseInterface:
    """Interface manages communication with the CiviCRM API

    Call the Interface instance with `action`, `entity`, and `params` values to submit an API request.

    The `search_query` method is a helper function to generate query parameters.
    The `values` method is a helper function to generate parameters for create/update.
    """

    def __init__(self):
        self.func: Callable[[str, str, CiviValue], CiviResponse] | None = None

    def __call__(self, action: str, entity: str, params: CiviValue) -> CiviResponse:
        raise NotImplementedError

    @staticmethod
    def limit(value: int) -> CiviValue | CiviV4Request:
        raise NotImplementedError

    @staticmethod
    def where(kwargs: CiviValue) -> CiviValue | CiviV4Request:
        raise NotImplementedError

    @staticmethod
    def values(kwargs: CiviValue) -> CiviValue | CiviV4Request:
        raise NotImplementedError


__all__ = ["BaseInterface", "CiviValue", "CiviV3Response", "CiviV4Request", "CiviV4Response", "CiviResponse"]
