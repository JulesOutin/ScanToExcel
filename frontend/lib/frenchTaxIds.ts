/**
 * Portage JS des contrôles SIREN/SIRET/TVA FR — même algorithme que
 * backend/app/services/french_tax_ids.py, pour un retour immédiat dans le
 * formulaire sans aller-retour serveur. Le backend reste la source de vérité
 * (revalidé à l'extraction et à la sauvegarde).
 */
const LA_POSTE_SIREN = "356000000";

function luhnOk(digits: string): boolean {
  let total = 0;
  const rev = digits.split("").reverse();
  rev.forEach((ch, i) => {
    let d = Number(ch);
    if (i % 2 === 1) {
      d *= 2;
      if (d > 9) d -= 9;
    }
    total += d;
  });
  return total % 10 === 0;
}

function cleanDigits(value: string): string {
  return (value || "").replace(/[^0-9]/g, "");
}

export function isValidSiren(value: string): boolean {
  const digits = cleanDigits(value);
  if (digits.length !== 9) return false;
  return luhnOk(digits);
}

export function isValidSiret(value: string): boolean {
  const digits = cleanDigits(value);
  if (digits.length !== 14) return false;
  const siren = digits.slice(0, 9);
  if (siren === LA_POSTE_SIREN) {
    const sum = digits.split("").reduce((acc, c) => acc + Number(c), 0);
    return sum % 5 === 0;
  }
  return luhnOk(digits);
}

export function computeTvaKey(siren: string): string | null {
  if (!isValidSiren(siren)) return null;
  const key = (12 + 3 * (Number(siren) % 97)) % 97;
  return String(key).padStart(2, "0");
}

export function validateTvaFr(value: string): { valid: boolean | null; message: string } {
  const cleaned = (value || "").toUpperCase().replace(/[\s.-]/g, "");
  const m = cleaned.match(/^FR([0-9A-Z]{2})(\d{9})$/);
  if (!m) return { valid: false, message: "Format attendu : FR + 2 caractères + 9 chiffres (SIREN)." };

  const [, key, siren] = m;
  if (!isValidSiren(siren)) return { valid: false, message: "Le SIREN contenu dans le n° de TVA est invalide." };

  if (/^\d{2}$/.test(key)) {
    const expected = computeTvaKey(siren);
    if (key === expected) return { valid: true, message: "N° de TVA valide." };
    return { valid: false, message: `Clé de contrôle incorrecte (attendu ${expected}).` };
  }
  return { valid: null, message: "SIREN valide, clé alphabétique non vérifiable automatiquement." };
}

/** Message d'avertissement si la valeur ressemble à un SIRET/SIREN/TVA FR invalide, sinon null. */
export function identifyAndCheck(value: string): string | null {
  if (!value) return null;
  const stripped = value.trim().toUpperCase();

  if (stripped.startsWith("FR") && /\d/.test(stripped)) {
    const check = validateTvaFr(stripped);
    return check.valid === false ? `N° de TVA invalide : ${check.message}` : null;
  }

  const digits = cleanDigits(stripped);
  if (digits.length === 14) return isValidSiret(digits) ? null : "SIRET invalide (clé de contrôle incorrecte).";
  if (digits.length === 9) return isValidSiren(digits) ? null : "SIREN invalide (clé de contrôle incorrecte).";
  return null;
}
