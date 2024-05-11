from datetime import datetime
from typing import Literal
from civipy.base.base import CiviCRMBase
from civipy.contribution import CiviContribution
from civipy.exceptions import CiviProgrammingError
from civipy.interface import CiviValue


class CiviMembershipPayment(CiviCRMBase):
    pass


class CiviMembership(CiviCRMBase):
    def payments(self):
        """Find all MembershipPayment records associated with this Membership."""
        return CiviMembershipPayment.find_all(membership_id=self.id)

    def apply_contribution(self, contribution: CiviContribution):
        """Apply a Contribution to this Membership and extend the expiration date."""
        # The new expiration date should be the old expiration date plus one year.
        end = datetime.strptime(self.end_date, "%Y-%m-%d")
        end = end.replace(year=end.year + 1)
        # If the new expiration date is in the future, change the status to "Current".
        status = "2" if end > datetime.now() else self.status_id
        cid = contribution.id
        CiviMembershipPayment.create(contribution_id=cid, membership_id=self.id)
        self.update(end_date=end.strftime("%Y-%m-%d"), status_id=status)

    def set_status(self, status_id: int | None = None, status: str | None = None, is_override: bool = False):
        if status_id is not None and status is not None:
            raise CiviProgrammingError("Undefined behavior: called set_status with `status_id` and `status`.")
        if status_id is None and status is None:
            raise CiviProgrammingError("Called set_status with no status.")
        values = {"status_id": status_id}
        if is_override is True:
            values["is_override"] = True
        return self.objects.filter(id=self.id).update(**values)

    @classmethod
    def query_values_hook(cls, version: Literal["3", "4"], query: CiviValue) -> CiviValue:
        if version == "4" and "values" in query and isinstance(query["values"].get("status_id"), str):
            query["values"]["status_id.name"] = query["values"].pop("status_id")
        return query
