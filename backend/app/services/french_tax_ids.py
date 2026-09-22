"""
Validation des identifiants d'entreprise français : SIREN, SIRET, n° de TVA intracommunautaire.

Références (algorithmes publics, non propriétaires) :
- SIREN/SIRET : clé de Luhn (norme INSEE), à l'exception des établissements
  du groupe La Poste (SIREN 356000000) qui suivent une règle particulière
  (somme des chiffres multiple de 5) — gérée séparément ci-dessous.
- TVA intracommunautaire FR : clé = (12 + 3 × (SIREN mod 97)) mod 97, sur 2 chiffres.
  Les numéros de TVA à clé alphabétique (ancien schéma, hors formule numérique)
  ne sont pas vérifiables par ce calcul : on ne les rejette pas, on signale
  simplement que la clé n'a pas pu être confirmée.
"""
import re
from dataclasses import dataclass

LA_POSTE_SIREN = "356000000"


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


def clean_digits(value: str) -> str:
    return re.sub(r"[^0-9]", "", value or "")


def is_valid_siren(value: str) -> bool:
    digits = clean_digits(value)
    if len(digits) != 9:
        return False
    return _luhn_ok(digits)


def is_valid_siret(value: str) -> bool:
    digits = clean_digits(value)
    if len(digits) != 14:
        return False
    siren, nic = digits[:9], digits[9:]
    if siren == LA_POSTE_SIREN:
        return sum(int(c) for c in digits) % 5 == 0
    return _luhn_ok(digits)


def compute_tva_key(siren: str) -> str | None:
    """Clé de contrôle à 2 chiffres selon la formule officielle. None si le SIREN est invalide."""
    if not is_valid_siren(siren):
        return None
    key = (12 + 3 * (int(siren) % 97)) % 97
    return f"{key:02d}"


@dataclass
class TvaCheck:
    valid: bool | None  # True/False si vérifiable, None si le format échappe à la formule numérique
    siren: str | None
    message: str


def validate_tva_fr(value: str) -> TvaCheck:
    cleaned = re.sub(r"[\s.-]", "", (value or "").upper())
    m = re.match(r"^FR([0-9A-Z]{2})(\d{9})$", cleaned)
    if not m:
        return TvaCheck(valid=False, siren=None, message="Format attendu : FR + 2 caractères + 9 chiffres (SIREN).")

    key, siren = m.group(1), m.group(2)
    if not is_valid_siren(siren):
        return TvaCheck(valid=False, siren=siren, message="Le SIREN contenu dans le n° de TVA est invalide.")

    if key.isdigit():
        expected = compute_tva_key(siren)
        if key == expected:
            return TvaCheck(valid=True, siren=siren, message="N° de TVA valide.")
        return TvaCheck(valid=False, siren=siren, message=f"Clé de contrôle incorrecte (attendu {expected}).")

    # Ancien schéma alphabétique — le SIREN est valide mais la clé n'est pas vérifiable ici.
    return TvaCheck(valid=None, siren=siren, message="SIREN valide, mais clé alphabétique non vérifiable automatiquement.")


def identify_and_check(value: str) -> str | None:
    """
    Détecte s'il s'agit d'un SIRET, SIREN ou n° de TVA FR à partir de sa forme,
    et retourne un message d'avertissement si le contrôle échoue — None si tout va bien
    ou si la forme ne correspond à aucun de ces identifiants (on ne force rien).
    """
    if not value:
        return None
    stripped = value.strip().upper()

    if stripped.startswith("FR") and any(c.isdigit() for c in stripped):
        check = validate_tva_fr(stripped)
        if check.valid is False:
            return f"N° de TVA « {value} » invalide : {check.message}"
        return None

    digits = clean_digits(stripped)
    if len(digits) == 14:
        return None if is_valid_siret(digits) else f"SIRET « {value} » invalide (clé de contrôle incorrecte)."
    if len(digits) == 9:
        return None if is_valid_siren(digits) else f"SIREN « {value} » invalide (clé de contrôle incorrecte)."

    return None  # ni SIRET, ni SIREN, ni TVA FR reconnaissable — on ne le signale pas comme une erreur
