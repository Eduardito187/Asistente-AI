from app.application.services.hasher_contacto import HasherContacto


def test_email_hash_determinista():
    h1 = HasherContacto.email("eduardo@gmail.com")
    h2 = HasherContacto.email("EDUARDO@GMAIL.COM")
    assert h1 == h2  # case-insensitive
    assert len(h1) == 64  # sha256


def test_emails_distintos_hashes_distintos():
    h1 = HasherContacto.email("a@b.com")
    h2 = HasherContacto.email("c@d.com")
    assert h1 != h2


def test_telefono_normaliza_codigo_pais():
    h1 = HasherContacto.telefono("+591 70123456")
    h2 = HasherContacto.telefono("70123456")
    assert h1 == h2


def test_telefono_ignora_separadores():
    h1 = HasherContacto.telefono("70-123-456")
    h2 = HasherContacto.telefono("70123456")
    assert h1 == h2


def test_email_vs_telefono_namespace_separado():
    h1 = HasherContacto.email("70123456@gmail.com")
    h2 = HasherContacto.telefono("70123456")
    assert h1 != h2  # namespace prefix protege
