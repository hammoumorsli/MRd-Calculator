# -*- coding: utf-8 -*-
"""
engine/interaction.py

Construction du diagramme d'interaction N-M complet de la section, à
partir des mêmes tableaux X/Nui/Mui que ceux utilisés par
`engine.mrd.calcul_Mrd` pour trouver Mrd par interpolation.

Aucune équation de résistance n'est recalculée ici : ce module
réutilise `engine.mrd._calculer_tableaux_capacite`, qui contient la
seule et unique implémentation des équations issues de Mrd.py.
"""

from dataclasses import dataclass

import numpy as np

from engine.mrd import _calculer_tableaux_capacite


@dataclass
class PointCapacite:
    """Un point du diagramme d'interaction, avec sa classification."""
    X_cm: float
    N_kN: float
    M_kNm: float
    pivot: str
    section: str


@dataclass
class DiagrammeInteraction:
    """Résultat complet du balayage de l'axe neutre, prêt pour le tracé
    matplotlib et pour le tableau de résultats du GUI."""
    X: np.ndarray       # position de l'axe neutre (m)
    N: np.ndarray       # effort normal résistant (kN)
    M: np.ndarray       # moment résistant (kN.m)
    d: float            # hauteur utile (m)
    h_m: float           # hauteur de section (m)
    X_lim: float         # limite pivot A/B (m)
    points: list         # liste de PointCapacite (pour le tableau de résultats)


def _classifier_point(X_val: float, d: float, h: float) -> tuple:
    """Reprend exactement les règles de classification utilisées en fin
    de `calcul_Mrd` (Pivot A/B/C, type de section), appliquées ici à
    n'importe quel point du diagramme plutôt qu'au seul point Nu/Mrd."""
    if X_val < 0.259 * d:
        pivot = "Pivot A"
    elif X_val < h:
        pivot = "Pivot B"
    else:
        pivot = "Pivot C"

    if 0 < X_val < h:
        section = "Section Partiellement Comprimée"
    elif X_val <= 0:
        section = "Section Entierement Tendue"
    else:
        section = "Section Entierement Comprimée"

    return pivot, section


def calculate_interaction_diagram(
    Fc28, Fe, theta, gamma_b, gamma_s, Es, b, h, As1, c, As2, Cs,
    max_points_tableau: int = 400,
) -> DiagrammeInteraction:
    """Calcule le diagramme d'interaction N-M complet de la section.

    Retourne un objet DiagrammeInteraction contenant :
      - X, N, M : tableaux numpy complets (tous domaines, y compris
        Pivot C / section entièrement comprimée), pour le tracé.
      - points : une liste sous-échantillonnée de PointCapacite,
        classés par pivot/section, pour le tableau de résultats du
        GUI (§22 de la spécification) — un tableau de résultats avec
        toutes les valeurs de X serait illisible (~8000 lignes).

    max_points_tableau contrôle la taille de cette liste sous-
    échantillonnée ; le tracé, lui, utilise toujours le tableau complet.
    """
    tab = _calculer_tableaux_capacite(
        Fc28, Fe, theta, gamma_b, gamma_s, Es, b, h, As1, c, As2, Cs
    )

    # Ne garder que les points où le calcul est défini (hors NaN)
    valides = ~(np.isnan(tab.Nui) | np.isnan(tab.Mui))
    X_valide = tab.X[valides]
    N_valide = tab.Nui[valides]
    M_valide = tab.Mui[valides]

    # Sous-échantillonnage régulier pour le tableau de résultats
    n = len(X_valide)
    if n == 0:
        points = []
    else:
        pas = max(1, n // max_points_tableau)
        indices = np.arange(0, n, pas)
        points = []
        for i in indices:
            pivot, section = _classifier_point(X_valide[i], tab.d, tab.h)
            points.append(PointCapacite(
                X_cm=X_valide[i] * 100,
                N_kN=N_valide[i],
                M_kNm=M_valide[i],
                pivot=pivot,
                section=section,
            ))

    return DiagrammeInteraction(
        X=X_valide, N=N_valide, M=M_valide,
        d=tab.d, h_m=tab.h, X_lim=tab.X_lim,
        points=points,
    )
