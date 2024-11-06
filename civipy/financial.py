from civipy.base.base import CiviCRMBase


class CiviEntityFinancialTrxn(CiviCRMBase):
    @classmethod
    def cancel(cls, **kwargs):
        return cls.action("cancel", **kwargs)

    @classmethod
    def find_by_transaction_id(cls, trxn_id: str, entity_table: str) -> "CiviEntityFinancialTrxn | None":
        """Find a Contribution Payment by payment transaction ID"""
        found = cls.objects.filter(
            entity_table=entity_table, financial_trxn_id__trxn_id=trxn_id
        ).select(["*", "financial_trxn_id.*"]).all()
        return next(filter(lambda c: bool(c.civi.get("entity_id")), found), None)


class CiviFinancialTrxn(CiviCRMBase):
    ...


class CiviFinancialItem(CiviCRMBase):
    ...


class CiviLineItem(CiviCRMBase):
    ...
