from civipy import CiviContact


def test_get_with_existing():
    contact_info = CiviContact.objects.filter(email="validunique@example.com").all()

    assert len(contact_info) == 1
    assert isinstance(contact_info[0], CiviContact)


def test_get_no_match():
    contact = CiviContact.objects.get(email="unknown@example.com")
    assert contact is None


def test_find_with_existing():
    result = CiviContact.objects.filter(email="validunique@example.com").all()
    contact = result[0] if result else None

    assert isinstance(contact, CiviContact)
    assert contact.display_name == "Valid Unique"
    assert contact.email == "validunique@example.com"
    assert contact.civi["display_name"] == "Valid Unique"
    assert contact.civi["email"] == "validunique@example.com"

    # do some tests of setattr while we have an object
    #
    # existing civi attributes can be modified
    contact.display_name = "New Name"
    assert contact.civi["display_name"] == "New Name"
    assert "display_name" not in contact.__dict__
    assert contact.display_name == "New Name"

    # but other attributes won't affect civi dict
    contact.foo = "bar"
    assert "foo" not in contact.civi
    assert contact.foo == "bar"

    # unless they are prefixed with civi_
    contact.civi_foo = "bar"
    assert contact.civi["foo"] == "bar"
    assert contact.foo == "bar"


def test_find_and_update_with_existing():
    contact = CiviContact.objects.get(email="validunique@example.com")
    contact.display_name = "Updated Name"
    contact.save()

    assert isinstance(contact, CiviContact)
    assert contact.display_name == "Updated Name"
    assert contact.email == "validunique@example.com"
    assert contact.civi["display_name"] == "Updated Name"
    assert contact.civi["email"] == "validunique@example.com"


def test_find_no_match():
    result = CiviContact.objects.filter(email="unknown@example.com").all()
    contact = result[0] if result else None

    assert contact is None


def test_find_all_no_match():
    contact = CiviContact.objects.filter(email="unknown@example.com").all()

    assert contact == []


def test_find_or_create_with_existing():
    contacts = CiviContact.objects.filter(email="validunique@example.com").all()
    contact = contacts[0] if contacts else CiviContact(email="validunique@example.com")
    contact.save()

    assert isinstance(contact, CiviContact)
    assert contact.display_name == "Valid Unique"
    assert contact.email == "validunique@example.com"
    assert contact.civi["display_name"] == "Valid Unique"
    assert contact.civi["email"] == "validunique@example.com"
