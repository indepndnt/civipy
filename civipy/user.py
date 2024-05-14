from civipy.base.base import CiviCRMBase
from civipy.exceptions import NoResultError, NonUniqueResultError


class CiviUFField(CiviCRMBase): ...


class CiviUFGroup(CiviCRMBase): ...


class CiviUFJoin(CiviCRMBase): ...


class CiviUFMatch(CiviCRMBase):
    """This is the table that matches host system users to CiviCRM Contacts.

    create requires uf_id, uf_name, and contact_id

    Attributes:
        id: str e.g. "24392"
        domain_id: str e.g. "1"
        uf_id: str e.g. "46914"
        uf_name: str e.g. "user@example.com"
        contact_id: str e.g. "367872"
    """

    @classmethod
    def find_system_users(cls, contact_ids: list[int]) -> list["CiviUFMatch"]:
        result = []
        for contact_id in set(contact_ids):
            found = cls.find(contact_id=contact_id)
            if not found:
                continue
            result.append(found)
        if not result:
            raise NoResultError("No result found!")
        if len(result) != 1:
            views = [f"{r.civi}\n" for r in result]
            raise NonUniqueResultError(f"Too many results:\n {''.join(views)}")
        result = result[0]
        for attr in ("id", "domain_id", "uf_id", "contact_id"):
            result.civi[attr] = int(result.civi[attr])
        return result

    def update_system_user(self, user_id: int):
        return self.update(**self.civi, uf_id=user_id)

    @classmethod
    def connect(cls, host_user: int, contact_id: int, domain_id: int = 1):
        return cls.objects.create(domain_id=domain_id, uf_id=host_user, contact_id=contact_id)


class CiviUser(CiviCRMBase): ...
