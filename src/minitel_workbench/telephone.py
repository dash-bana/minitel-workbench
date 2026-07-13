"""Telephone assistant — for the majority of owners, who dial in.

Most living Minitels connect by telephone, not a USB cable, so this is core
functionality, not an add-on (Constitution rule II). It needs no hardware: it
turns a service's listed number into clear, bilingual dialing instructions.
"""

from __future__ import annotations

from .services import Service


def dialing_instructions(svc: Service) -> str:
    """Human, bilingual instructions for reaching ``svc`` by telephone."""
    numbers = svc.telephone_numbers()
    if not numbers:
        return (
            f"{svc.name} has no telephone number listed.\n"
            f"{svc.name} n'a pas de numéro de téléphone indiqué.\n\n"
            + (f"On the web: {svc.website}\n" if svc.website else "")
        ).rstrip() + "\n"

    number = numbers[0]
    lines = [
        f"{svc.name} — by telephone / par téléphone",
        "",
        f"  Dial:   {number}",
        "",
        "  EN  1. Make sure the Minitel is on the telephone line and powered on.",
        "      2. Dial the number above.",
        "      3. When you hear the modem carrier (the squealing tone),",
        "         press Connexion/Fin on the Minitel.",
        "      4. The service's home page appears. Type a code and press ENVOI.",
        "",
        "  FR  1. Vérifiez que le Minitel est raccordé à la ligne et allumé.",
        "      2. Composez le numéro ci-dessus.",
        "      3. À la porteuse du modem (le sifflement), appuyez sur",
        "         Connexion/Fin sur le Minitel.",
        "      4. La page d'accueil s'affiche. Tapez un code puis ENVOI.",
    ]
    if len(numbers) > 1:
        lines += ["", "  Other numbers / autres numéros: " + ", ".join(numbers[1:])]
    if svc.website:
        lines += ["", f"  More: {svc.website}"]
    return "\n".join(lines) + "\n"
