from civipy.base.base import CiviCRMBase
from civipy.contact import CiviContact


class CiviContribution(CiviCRMBase):
    civicrm_entity_table = "contribution"

    def complete_transaction(self, **kwargs):
        """Calls the CiviCRM API completetransaction action and returns parsed JSON on success."""
        kwargs["id"] = self.civi_id
        return self.objects._interface().execute("completetransaction", "Contribution", kwargs)

    @classmethod
    def find_by_transaction_id(cls, trxn_id: str, select: list[str] | None = None):
        """Find a contribution by payment transaction ID"""
        return cls.objects.get(select=select, trxn_id=trxn_id)

    @classmethod
    def find_by_invoice_id(cls, invoice_id: str, select: list[str] | None = None):
        return cls.objects.get(select=select, invoice_id=invoice_id)

    @classmethod
    def find_by_donor(
        cls,
        display_name: str,
        total_amount: float | None = None,
        receive_date: str | None = None,
        select: list[str] | None = None,
    ):
        """Find a contribution by donor's display name, and optionally
        by amount and/or date received (yyyy-mm-dd)."""
        result = CiviContact.objects.filter(display_name=display_name).values("contact_id").all()
        contact = result[0] if result else None
        return cls.find_by_donor_id(contact["contact_id"], total_amount, receive_date, select)

    @classmethod
    def find_by_donor_id(
        cls,
        contact_id: int,
        total_amount: float | None = None,
        receive_date: str | None = None,
        select: list[str] | None = None,
    ):
        """Find a contribution by donor's contact ID, and optionally
        by amount and/or date received (yyyy-mm-dd)."""
        query = {"contact_id": contact_id}
        if total_amount is not None:
            query["total_amount"] = total_amount
        if receive_date is not None:
            query["receive_date"] = {"BETWEEN": [receive_date, f"{receive_date} 23:59:59"]}
        return cls.objects.get(select=select, **query)


class CiviContributionRecur(CiviCRMBase):
    civicrm_entity_table = "contributionrecur"

    @classmethod
    def find_by_transaction_id(cls, trxn_id: str, select: list[str] | None = None):
        """
        Find a recurring contribution by subscription transaction ID
        """
        return cls.objects.get(select=select, trxn_id=trxn_id)
