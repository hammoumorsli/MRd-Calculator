# -*- coding: utf-8 -*-
"""
utils/formatting.py

Mise en forme des résultats numériques pour l'affichage dans le GUI
(unités, arrondis) — aucune logique de calcul ici.
"""


def formater_moment(valeur_kNm) -> str:
    if valeur_kNm is None:
        return "—"
    return f"{valeur_kNm:.2f} kN.m"


def formater_effort(valeur_kN) -> str:
    if valeur_kN is None:
        return "—"
    return f"{valeur_kN:.2f} kN"


def formater_position_axe(y_axe) -> str:
    """Y_axe est soit une chaîne ('< 0', '> h'), soit un nombre (cm)."""
    if y_axe is None:
        return "—"
    if isinstance(y_axe, str):
        return y_axe
    return f"{y_axe:.2f} cm"


def formater_domaine_nu(min_kN, max_kN) -> str:
    return (
        f"Domaine de résistance de la section en N : "
        f"[{min_kN:.1f} kN ; {max_kN:.1f} kN]"
    )


def message_hors_domaine(nu_kN, min_kN, max_kN) -> str:
    return (
        "Nu est en dehors du domaine de résistance calculé de la section.\n"
        f"Nu saisi : {nu_kN:.1f} kN\n"
        f"Domaine admissible : de {min_kN:.1f} kN à {max_kN:.1f} kN"
    )
