import json
import subprocess
import urllib3
from civipy.base.config import SETTINGS, logger
from civipy.exceptions import CiviAPIError, CiviHTTPError, CiviProgrammingError
from civipy.interface.base import CiviValue, CiviV3Response, BaseInterface


class V3Interface(BaseInterface):
    __doc__ = (
        BaseInterface.__doc__
        + """
This is the v3 API interface."""
    )

    api_version = "3"

    def execute(self, action: str, entity: str, params: CiviValue) -> CiviV3Response:
        if self.func is None:
            if SETTINGS.api_version != "3":
                raise CiviProgrammingError(f"API version '{SETTINGS.api_version}' cannot use V3Interface")
            if SETTINGS.api_type == "http":
                self.func = self.http_request
                self._configure_http_connection()
            elif SETTINGS.api_type in ("drush", "wp"):
                self.func = self.run_drush_or_wp_process
            elif SETTINGS.api_type == "cvcli":
                self.func = self.run_cv_cli_process
            else:
                raise CiviProgrammingError(f"API type '{SETTINGS.api_type}' not implemented")
        # in v3, the 'update' action is deprecated and we are instructed to use 'create' with an id.
        if action == "update" and "id" in params:
            action = "create"
        return self.func(action, entity, params)

    def http_request(self, action: str, entity: str, kwargs: CiviValue) -> CiviV3Response:
        # v3 see https://docs.civicrm.org/dev/en/latest/api/v3/rest/
        kwargs = self._pre_process(kwargs)
        params = self._http_params(entity, action, kwargs)

        # header for v3 API per https://docs.civicrm.org/dev/en/latest/api/v3/rest/#x-requested-with
        headers = {"X-Requested-With": "XMLHttpRequest"}

        # v3 API GET actions apparently all start with "get"; POST actions are create, delete, etc.
        method = "GET" if action.startswith("get") else "POST"
        # urllib3 uses the `fields` parameter to compose the query string for GET requests,
        # and uses the same parameter to compose form data for POST requests
        response = self.http.request(method, SETTINGS.rest_base, fields=params, headers=headers)
        return self.process_http_response(response)

    @staticmethod
    def _http_params(entity: str, action: str, kwargs: CiviValue) -> CiviValue:
        params = {
            "entity": entity,
            "action": action,
            "api_key": SETTINGS.user_key,
            "debug": 1,
            "key": SETTINGS.site_key,
            "json": 1,
            "sequential": 1,
        }
        if kwargs:
            for key, value in kwargs.items():
                if value is None:
                    continue
                params[key] = value
        return params

    def process_http_response(self, response: urllib3.BaseHTTPResponse) -> CiviV3Response:
        logger.debug(response.url)
        if response.status == 200:
            return self.process_json_response(response.json())
        else:
            raise CiviHTTPError(response)

    def run_cv_cli_process(self, action: str, entity: str, params: CiviValue) -> CiviV3Response:
        params = self._pre_process(params)
        # cli.php -e entity -a action [-u user] [-s site] [--output|--json] [PARAMS]
        params = ["--%s=%s" % (k, v) for k, v in params.items()]
        process = subprocess.run(
            [SETTINGS.rest_base, "-e", entity, "-a", action, "--json"] + params, capture_output=True, check=True
        )
        return self.process_json_response(json.loads(process.stdout.decode("UTF-8")))

    def run_drush_or_wp_process(self, action: str, entity: str, params: CiviValue) -> CiviV3Response:
        params = self._pre_process(params)
        process = subprocess.run(
            [SETTINGS.rest_base, "civicrm-api", "--out=json", "--in=json", "%s.%s" % (entity, action)],
            capture_output=True,
            check=True,
            input=json.dumps(params).encode("UTF-8"),
        )
        return self.process_json_response(json.loads(process.stdout.decode("UTF-8")))

    @staticmethod
    def _pre_process(params: CiviValue) -> CiviValue:
        if "options" in params:
            params["options"] = json.dumps(params["options"], separators=(",", ":"))
        return params

    @staticmethod
    def process_json_response(data: CiviV3Response) -> CiviV3Response:
        if "is_error" in data and data["is_error"] == 1:
            raise CiviAPIError(data)
        return data

    @staticmethod
    def select(fields: list[str]) -> CiviValue:
        return {"return": fields}

    @staticmethod
    def join(tables: list[tuple[str, str, str]]) -> CiviValue:
        raise NotImplementedError

    @staticmethod
    def sort(kwargs: CiviValue) -> CiviValue:
        option = []
        for k, v in kwargs.items():
            if isinstance(v, str) and v.upper() in ("ASC", "DESC"):
                option.append(k if v.upper() == "ASC" else f"{k} DESC")
            elif isinstance(v, int) and v in (0, 1):
                option.append(k if v else f"{k} DESC")
            else:
                raise CiviProgrammingError(f"Invalid sort value for {k}: {repr(v)}")
        return {"options": {"sort": option}}

    @staticmethod
    def limit(value: int, offset: int | None = None) -> CiviValue:
        option = {"limit": value}
        if offset is not None:
            option["offset"] = offset
        return {"options": option}

    @classmethod
    def where(cls, kwargs: CiviValue) -> CiviValue:
        option = {}
        for key, val in kwargs.items():
            parts = key.split("__")
            if len(parts) > 1 and parts[-1] in cls.operators:
                *parts, op = parts
                if op == "isnull":
                    val = {"IS NULL": 1} if val else {"IS NOT NULL": 1}  # noqa PLW2901 (loop var)
                elif (op.endswith("between") or op.endswith("in")) and not isinstance(val, list):
                    raise CiviProgrammingError(f"Must provide a list for `{op}` operator.")
                else:
                    val = {cls.operators[op]: val}  # noqa PLW2901 (loop var)
            option[".".join(parts)] = val
        return kwargs

    @staticmethod
    def values(kwargs: CiviValue) -> CiviValue:
        return kwargs


v3_interface = V3Interface()
__all__ = ["v3_interface"]
