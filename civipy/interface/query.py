from typing import TYPE_CHECKING, Type, Optional
from civipy.interface import get_interface, Interface

if TYPE_CHECKING:
    from civipy.base.base import CiviCRMBase
    from civipy.interface import CiviValue


class BaseQuery:
    def __init__(self, model: Type["CiviCRMBase"]) -> None:
        self.model = model
        if model.__name__ in ("MetaCiviCRM", "CiviCRMBase"):
            self._entity: str | None = None
        else:
            self._entity = model.__name__[4:] if model.__name__[:4] == "Civi" else model.__name__
        self._select = None
        self._filter = None
        self._join = None
        self._limit = None
        self._order = None
        self._result_cache: list | None = None

    def __repr__(self) -> str:
        data = list(self[:21])
        if len(data) > 20:
            data[-1] = "...(remaining elements truncated)..."
        return f"<{self.__class__.__name__} {data}>"

    def __len__(self):
        self._fetch_all()
        return len(self._result_cache)

    def __iter__(self):
        self._fetch_all()
        return iter(self._result_cache)

    def __bool__(self):
        self._fetch_all()
        return bool(self._result_cache)

    def __getitem__(self, k: int | slice):
        """Retrieve an item or slice from the set of results."""
        if isinstance(k, int):
            if k < 0:
                raise ValueError("Negative indexing is not supported.")
            if self._result_cache is not None:
                return self._result_cache[k]
            query = self._chain()
            query._limit = {"offset": k, "limit": 1}
            query._fetch_all()
            return query._result_cache[0]

        if not isinstance(k, slice):
            raise TypeError(f"QuerySet indices must be integers or slices, not {type(k).__name__}.")
        if (k.start is not None and k.start < 0) or (k.stop is not None and k.stop < 0):
            raise ValueError("Negative indexing is not supported.")
        if self._result_cache is not None:
            return self._result_cache[k]
        query = self._chain()
        start, stop, step = [None if v is None else int(v) for v in (k.start, k.stop, k.step)]
        query._limit = {} if start is None else {"offset": start}
        query._limit["limit"] = stop - query._limit.get("offset", 0)
        return list(query)[::step] if step else query

    _interface_reference: Interface | None = None

    @classmethod
    def _interface(cls) -> Interface:
        """Instantiate the appropriate API interface and store it on the base Query class,
        so that it will be instantiated only once and available to all entity classes."""
        if BaseQuery._interface_reference is None:
            BaseQuery._interface_reference = get_interface()
        return BaseQuery._interface_reference

    def _chain(self):
        query = self.__class__(model=self.model)
        query._select = self._select
        query._filter = self._filter
        query._join = self._join
        query._limit = self._limit
        query._order = self._order
        return query

    def _compose(self, values: Optional["CiviValue"] = None) -> "CiviValue":
        """Create a query for the selected API version from the current attributes."""
        interface = self._interface()
        params = {}
        if self._select is not None:
            self._deep_update(params, interface.select(self._select))
        if self._join is not None:
            self._deep_update(params, interface.join(self._join))
        if self._filter is not None:
            where = interface.where(self._filter)
            if hasattr(self.model, "query_filter_hook"):
                where = self.model.query_filter_hook(interface.api_version, where)
            self._deep_update(params, where)
        if self._limit is not None:
            self._deep_update(params, interface.limit(self._limit["limit"]))
        if self._order is not None:
            self._deep_update(params, interface.sort(self._order))
        if values is not None:
            values = interface.values(values)
            if hasattr(self.model, "query_values_hook"):
                values = self.model.query_values_hook(interface.api_version, values)
            self._deep_update(params, values)
        return params

    def _deep_update(self, query: "CiviValue", other: "CiviValue") -> None:
        """Update `query` with the values in `other`, also updating contained dicts rather than overwriting them."""
        for key, val in other.items():
            if key in query and isinstance(query[key], dict) and isinstance(val, dict):
                self._deep_update(query[key], val)
                continue
            query[key] = val

    def _fetch_all(self):
        if self._result_cache is None:
            query = self._compose()
            results = self._interface().execute("get", self._entity, query)
            self._result_cache = list(map(self.model, results["values"]))


class Query(BaseQuery):
    def all(self):
        self._fetch_all()
        return self._result_cache

    def get(self, **kwargs):
        return self.filter(**kwargs)[0]

    def filter(self, **kwargs):
        query = self._chain()
        if query._filter:
            query._filter.update(kwargs)
        else:
            query._filter = kwargs
        return query

    def values(self, *args):
        query = self._chain()
        query._select = []
        for field in args:
            foreign_key, _, join_field = field.partition(".")
            if not join_field:
                query._select.append(field)
                continue
            if query._join is None:
                query._join = {}
            if foreign_key not in query._join:
                table = foreign_key[:-3]
                if table == "entity":
                    name, table = self.model._implicit_join
                else:
                    name = table.title()
                query._join[foreign_key] = (name, table)
            query._select.append(".".join((query._join[foreign_key][1], join_field)))
        return query

    def order_by(self, **kwargs):
        query = self._chain()
        query._order = kwargs
        return query

    def create(self, **kwargs):
        query = self._interface().values(kwargs)
        response = self._interface().execute("create", self._entity, query)
        return response

    def save(self, records: list[dict[str, str]], defaults: dict[str, str] | None = None, match: list[str] | None = None):
        query = {"records": records}
        if defaults is not None:
            query["defaults"] = defaults
        if match is not None:
            query["match"] = match
        response = self._interface().execute("save", self._entity, query)
        return response

    def delete(self):
        query = self._compose()
        response = self._interface().execute("delete", self._entity, query)
        return response

    def update(self, **kwargs):
        query = self._compose(kwargs)
        response = self._interface().execute("update", self._entity, query)
        return response
