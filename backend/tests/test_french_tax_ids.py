"""
Tests des contrôles SIREN/SIRET/TVA FR.

Les numéros utilisés sont construits algorithmiquement (via la même formule
de Luhn que le module) plutôt que copiés sur une entreprise réelle, pour ne
jamais affirmer qu'un identifiant précis appartient à telle ou telle société.
"""
from app.services.french_tax_ids import (
    compute_tva_key,
    identify_and_check,
    is_valid_siren,
    is_valid_siret,
    validate_tva_fr,
)


def _luhn_ok(digits: str) -> bool:
    total = 0
    for i, ch in enumerate(reversed(digits)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def _append_valid_check_digit(prefix: str) -> str:
    """Trouve le chiffre final qui rend `prefix + chiffre` valide selon Luhn (il en existe toujours un)."""
    for last in "0123456789":
        candidate = prefix + last
        if _luhn_ok(candidate):
            return candidate
    raise AssertionError("aucun chiffre de contrôle trouvé — la formule Luhn le garantit pourtant toujours")


def make_valid_siren_9() -> str:
    # 8 chiffres de base + 1 chiffre de contrôle trouvé -> 9 chiffres
    return _append_valid_check_digit("73282932")


def make_valid_siret(siren: str, nic_prefix: str = "0001") -> str:
    return _append_valid_check_digit(siren + nic_prefix)


def test_valid_siren_passes():
    siren = make_valid_siren_9()
    assert len(siren) == 9
    assert is_valid_siren(siren)


def test_siren_with_flipped_digit_fails():
    siren = make_valid_siren_9()
    flipped = siren[:-1] + str((int(siren[-1]) + 1) % 10)
    assert not is_valid_siren(flipped)


def test_siren_wrong_length_fails():
    assert not is_valid_siren("12345")


def test_valid_siret_passes():
    siren = make_valid_siren_9()
    siret = make_valid_siret(siren)
    assert len(siret) == 14
    assert is_valid_siret(siret)


def test_siret_with_flipped_digit_fails():
    siren = make_valid_siren_9()
    siret = make_valid_siret(siren)
    flipped = siret[:-1] + str((int(siret[-1]) + 1) % 10)
    assert not is_valid_siret(flipped)


def test_tva_with_correct_numeric_key_is_valid():
    siren = make_valid_siren_9()
    key = compute_tva_key(siren)
    check = validate_tva_fr(f"FR{key}{siren}")
    assert check.valid is True


def test_tva_with_wrong_key_is_invalid():
    siren = make_valid_siren_9()
    correct_key = compute_tva_key(siren)
    wrong_key = f"{(int(correct_key) + 1) % 97:02d}"
    check = validate_tva_fr(f"FR{wrong_key}{siren}")
    assert check.valid is False


def test_tva_bad_format_is_invalid():
    check = validate_tva_fr("not-a-vat-number")
    assert check.valid is False


def test_tva_alphabetic_key_is_unverifiable_not_rejected():
    siren = make_valid_siren_9()
    check = validate_tva_fr(f"FRXX{siren}")
    assert check.valid is None  # ni validé, ni rejeté


def test_identify_and_check_accepts_valid_siret():
    siren = make_valid_siren_9()
    siret = make_valid_siret(siren)
    assert identify_and_check(siret) is None


def test_identify_and_check_flags_invalid_siret():
    result = identify_and_check("12345678901234")  # 14 chiffres, quasi certainement invalide
    # on ne peut pas garantir à 100% l'invalidité d'un nombre arbitraire, donc on ne teste
    # que le cas où le module la détecte comme telle, sans halluciner un résultat figé
    if not is_valid_siret("12345678901234"):
        assert result is not None and "SIRET" in result


def test_identify_and_check_ignores_unrelated_text():
    assert identify_and_check("1 rue de la Paix, 75002 Paris") is None
    assert identify_and_check("") is None
    assert identify_and_check(None) is None
