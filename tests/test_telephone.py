from minitel_workbench.services import Service, load_directory
from minitel_workbench.telephone import dialing_instructions


def test_instructions_include_number_and_key():
    svc = load_directory().get("retrocampus")
    text = dialing_instructions(svc)
    assert "+39 0522 750051" in text
    assert "Connexion/Fin" in text
    assert "ENVOI" in text


def test_service_without_phone():
    svc = Service(id="x", name="X", access={"kind": "demo"})
    text = dialing_instructions(svc)
    assert "no telephone number" in text


def test_extra_numbers_listed():
    svc = Service(
        id="x",
        name="X",
        access={"kind": "telephone", "number": "01 00 00 00 00"},
        alt_access=({"kind": "telephone", "number": "02 00 00 00 00"},),
    )
    text = dialing_instructions(svc)
    assert "01 00 00 00 00" in text
    assert "02 00 00 00 00" in text
