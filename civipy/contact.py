import json
from typing import Iterable, Literal
from civipy.base.base import CiviCRMBase, CiviEntity
from civipy.address import CiviCountry
from civipy.exceptions import CiviProgrammingError
from civipy.interface import CiviValue
from civipy.note import CiviNotable


class CiviContact(CiviNotable):
    civicrm_entity_table = "contact"

    @classmethod
    def find_by_email(cls, email_address: str, select: list[str] | None = None):
        if select is None:
            select = []
        email_obj = CiviEmail.objects.filter(email=email_address).values("contact_id")[0]
        return cls.objects.filter(id=email_obj.civi["contact_id"]).values(*select)[0]

    @classmethod
    def find_all_by_email(cls, email_address: str, select: list[str] | None = None):
        if select is None:
            select = []
        return [
            cls.objects.filter(id=email_obj.civi["contact_id"]).values(*select)[0]
            for email_obj in CiviEmail.objects.filter(email=email_address).values("contact_id").all()
        ]

    @classmethod
    def create(cls, **kwargs: CiviValue) -> "CiviContact":
        country_code: str | None = kwargs.pop("country_code", None)
        if country_code is not None:
            country = CiviCountry.find_by_country_code(country_code=country_code, select=["id"])
            kwargs["country_id"] = country.id
        return super().create(**kwargs)


class CiviEmail(CiviCRMBase):
    pass


class CiviPhone(CiviCRMBase):
    pass


class CiviWebsite(CiviCRMBase):
    pass


class CiviRelationship(CiviCRMBase):
    @classmethod
    def find_all(cls, select: list[str] | None = None, **kwargs: CiviValue) -> list[CiviEntity]:
        if select is None:
            return cls.objects.filter(**kwargs).all()
        return cls.objects.filter(**kwargs).values(*select).all()

    @classmethod
    def query_filter_hook(cls, version: Literal["3", "4"], query: CiviValue) -> CiviValue:
        if version == "3" or "where" not in query:
            return query
        contact_id = None
        parts = []
        for k, c, v in query["where"]:
            if k == "contact_id":
                contact_id = v
                parts.append(["OR", [["contact_id_a", "=", contact_id], ["contact_id_b", "=", contact_id]]])
                continue
            parts.append([k, c, v])
        if contact_id is not None:
            query["where"] = parts
        return query

    @classmethod
    def create_or_increment_relationship(  # noqa PLR0913 (too many args)
        cls,
        contact_id_a: int,
        contact_id_b: int,
        relationship_type_id: int,
        event_id: int | None = None,
        activity_id: int | None = None,
    ):
        print(f"in create_or_increment_relationship with a {contact_id_a} b {contact_id_b} type {relationship_type_id}")
        if not event_id and not activity_id:
            raise CiviProgrammingError("Must provide either event_id or activity_id")

        existing_relationship = cls.find(
            contact_id_a=contact_id_a,
            contact_id_b=contact_id_b,
            relationship_type_id=relationship_type_id,
        )
        if existing_relationship is None:
            # look for reverse relationship
            existing_relationship = cls.find(
                contact_id_a=contact_id_b,
                contact_id_b=contact_id_a,
                relationship_type_id=relationship_type_id,
            )

        events = [event_id] if event_id else []
        activities = [activity_id] if activity_id else []
        if existing_relationship is None:
            # create new relationship
            cls.create(
                contact_id_a=contact_id_a,
                contact_id_b=contact_id_b,
                relationship_type_id=relationship_type_id,
                description=json.dumps({"events": events, "activities": activities}),
                debug=1,
            )
        else:
            # update existing relationship
            relationship_info = {}
            if "description" in existing_relationship.civi:
                desc = existing_relationship.civi_description
                try:
                    relationship_info = json.loads(desc)
                except json.decoder.JSONDecodeError:
                    pass

            if "events" not in relationship_info:
                events.extend(relationship_info["events"])
            relationship_info["events"] = list(set(filter(None, events)))

            if "activities" not in relationship_info:
                activities.extend(relationship_info["activities"])
            relationship_info["activities"] = list(set(filter(None, activities)))

            existing_relationship.update(description=json.dumps(relationship_info))


class CiviEntityTag(CiviCRMBase):
    pass


class CiviTag(CiviCRMBase):
    pass


class CiviGroupContact(CiviCRMBase):
    pass


class CiviGroup(CiviCRMBase):
    @classmethod
    def find_by_title(cls, title: str, select: list[str] | None = None) -> "CiviGroup":
        """Finds a CiviGroup object for the group entitled "title"."""
        return cls.find(select=select, title=title)

    def update_all(self, contacts: Iterable[int | CiviContact]) -> None:
        query = CiviGroupContact.objects.filter(group_id=self.id).values("contact_id")
        current_pop = {c.contact_id for c in query}
        contact_ids = {c.id if isinstance(c, CiviContact) else c for c in contacts}
        for contact_id in current_pop.difference(contact_ids):
            CiviGroupContact.objects.filter(group_id=self.id, contact_id=contact_id).delete()
        for contact_id in contact_ids.difference(current_pop):
            CiviGroupContact.objects.create(group_id=self.id, contact_id=contact_id)

    def add_member(self, civi_contact: CiviContact) -> CiviGroupContact:
        return CiviGroupContact.find_or_create(where={"contact_id": civi_contact.id, "group_id": self.id})
