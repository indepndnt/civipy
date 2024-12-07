from typing import Iterable
from civipy.base.base import CiviCRMBase
from civipy.exceptions import NoResultError


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
    REPR_FIELDS = ["domain_id", "uf_id", "uf_name", "contact_id"]

    @classmethod
    def find_system_users(cls, contact_ids: Iterable[int]) -> list["CiviUFMatch"]:
        result = []
        for contact_id in set(contact_ids):
            found = cls.objects.get(contact_id=contact_id)
            if not found:
                continue
            result.append(found)
        if not result:
            raise NoResultError("No result found!")
        for uf in result:
            for attr in ("id", "domain_id", "uf_id", "contact_id"):
                uf.civi[attr] = int(uf.civi[attr])
        return result

    def update_system_user(self, user_id: int) -> "CiviUFMatch":
        self.uf_id = user_id
        return self.save()

    @classmethod
    def connect(cls, host_user: int, contact_id: int, domain_id: int = 1):
        return cls.objects.create(domain_id=domain_id, uf_id=host_user, contact_id=contact_id)


class CiviUser(CiviCRMBase): ...
