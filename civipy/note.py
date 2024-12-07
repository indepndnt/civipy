from civipy.base.base import CiviCRMBase


class CiviNote(CiviCRMBase):
    pass


class CiviNotable(CiviCRMBase):
    def _where_for_note(self, note: str, subject: str) -> dict[str, str | int]:
        return {
            "entity_id": self.civi["id"], "entity_table": self.civicrm_entity_table, "note": note, "subject": subject
        }

    def add_note(self, subject: str, note: str):
        return CiviNote(self._where_for_note(note, subject)).save()

    def find_or_create_note(self, subject: str, note: str):
        notes = CiviNote.objects.filter(**self._where_for_note(note, subject)).all()
        instance = notes[0] if notes else CiviNote(**self._where_for_note(note, subject))
        return instance.save()
