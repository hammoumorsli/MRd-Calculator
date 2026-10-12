# -*- coding: utf-8 -*-
"""
engine/mrd.py

Moteur de calcul de la flexion composée (Nrd / Mrd) pour une section
rectangulaire en béton armé, par la méthode du diagramme d'interaction
N-M (balayage de la position de l'axe neutre X, pivots A/B/C).

IMPORTANT — FIDÉLITÉ AU CALCUL ORIGINAL
-----------------------------------------------------------------------
Les équations, les conditions de domaine, les conventions de signe et
la méthode d'interpolation de ce module sont une reprise EXACTE du
fichier `Mrd.py` fourni. Aucune formule n'a été modifiée.

La seule différence structurelle est que le calcul des tableaux
`X, Nui, Mui` (et de la classification par domaine) a été extrait dans
la fonction interne `_calculer_tableaux_capacite`, afin qu'il puisse
être réutilisé à la fois par `calcul_Mrd` (recherche de Mrd par
interpolation pour un Nu donné) et par `engine.interaction`
(construction du diagramme d'interaction complet), sans dupliquer les
équations à deux endroits différents du projet.

CONVENTION D'UNITÉS DE CE MODULE (voir engine/materials.py)
-----------------------------------------------------------------------
    Fc28, Fe, Es : MPa
    b, h         : mètres (m)   <- convertis ici depuis des cm en entrée
    c, Cs        : centimètres (cm) en entrée, convertis en m en interne
    As1, As2     : centimètres carrés (cm²) en entrée, convertis en m²
    Nu           : kilonewtons (kN)
    Mrd (sortie) : kilonewton-mètres (kN.m)

Le fichier original ne convertissait pas b et h (conversion en
commentaire). Après confirmation de l'utilisateur, ce module convertit
maintenant b et h de cm vers m au même titre que c et Cs, afin que le
GUI puisse rester exprimé uniformément en centimètres (voir §11 de la
spécification). Cette conversion est appliquée UNE SEULE FOIS, ici.
"""

from dataclasses import dataclass

import numpy as np

from engine.materials import cm_vers_m, cm2_vers_m2

# Constantes physiques du modèle (identiques au fichier original)
PSI_SU = 0.01      # déformation ultime de l'acier tendu
PSI_CU = 0.0035    # déformation ultime du béton comprimé


@dataclass
class TableauxCapacite:
    """Résultat du balayage de l'axe neutre X : tout ce dont on a besoin
    pour interpoler Mrd (engine.mrd) ou tracer le diagramme N-M
    (engine.interaction)."""
    X: np.ndarray
    Nui: np.ndarray
    Mui: np.ndarray
    d: float
    X_lim: float
    h: float


def _calculer_tableaux_capacite(
    Fc28, Fe, theta, gamma_b, gamma_s, Es, b, h, As1, c, As2, Cs
) -> TableauxCapacite:
    """Calcule les tableaux X, Nui, Mui pour toute la plage de positions
    de l'axe neutre. Reprend EXACTEMENT la logique du fichier original,
    à l'exception de la conversion cm -> m ajoutée pour b et h.
    """
    # --- Conversions d'unités (cm -> m, cm² -> m²) ---
    b = cm_vers_m(b)
    h = cm_vers_m(h)
    c = cm_vers_m(c)
    Cs = cm_vers_m(Cs)
    As1 = cm2_vers_m2(As1)
    As2 = cm2_vers_m2(As2)

    d = h - c

    fbu = 0.85 * Fc28 / (theta * gamma_b)
    Fsu = Fe / gamma_s

    psi_su = PSI_SU
    psi_cu = PSI_CU
    psi_y = Fsu / Es

    X_lim = 0.259 * d

    x_values = np.concatenate([
        np.arange(-100, -1, 0.1),
        np.arange(-1, 0, 0.01),
        np.arange(0.001, 0.3, 0.001),
        np.arange(0.3, 1.0, 0.005),
        np.arange(1.0, 1.4, 0.001),
        np.arange(1.4, 2.0, 0.01),
        np.arange(2, 10, 0.1),
        np.arange(10, 1000.1, 1.0),
    ])

    X = x_values * d

    X_domaine2 = d * psi_cu / (psi_cu + psi_su)

    conditions = [
        X <= 0,
        (X > 0) & (X <= X_domaine2),
        (X > X_domaine2) & (X <= X_lim),
        (X > X_lim) & (X <= d),
        (X > d) & (X <= h),
        X > h
    ]

    psi_s1 = np.select(
        conditions,
        [
            np.nan,
            np.nan,
            psi_cu * (d - X) / X,
            psi_cu * (d - X) / X,
            psi_cu * (X - d) / X,
            psi_y * (X - d) / (X - h / 2)
        ],
        default=np.nan
    )

    sigma_s1 = np.where(
        np.isnan(psi_s1),
        np.nan,
        np.where(
            psi_s1 >= 0,
            np.minimum(psi_s1 * Es, Fsu),
            np.maximum(psi_s1 * Es, -Fsu)
        )
    )

    psi_s2 = np.full_like(X, np.nan, dtype=float)

    mask = conditions[0]
    psi_s2[mask] = psi_su * (Cs - X[mask]) / (d - X[mask])

    mask = conditions[1]
    psi_s2[mask] = psi_su * (X[mask] - Cs) / (d - X[mask])

    mask = conditions[2] | conditions[3] | conditions[4]
    psi_s2[mask] = psi_su * (X[mask] - Cs) / X[mask]

    mask = conditions[5]
    psi_s2[mask] = psi_y * (X[mask] - Cs) / (X[mask] - h / 2)

    sigma_s2 = np.where(
        np.isnan(psi_s2),
        np.nan,
        np.where(
            psi_s2 >= 0,
            np.minimum(psi_s2 * Es, Fsu),
            np.maximum(psi_s2 * Es, -Fsu)
        )
    )

    Nui = np.select(
        conditions,
        [
            (
                -As2 * (sigma_s2 - 0.8 * fbu)
                - As1 * Fsu
            ) * 1000,

            (
                0.8 * fbu * X * b
                + As2 * (sigma_s2 - 0.8 * fbu)
                - As1 * Fsu
            ) * 1000,

            (
                0.8 * fbu * X * b
                + As2 * (sigma_s2 - 0.8 * fbu)
                - As1 * sigma_s1
            ) * 1000,

            (
                0.8 * fbu * X * b
                + As2 * (sigma_s2 - 0.8 * fbu)
                - As1 * sigma_s1
            ) * 1000,

            (
                0.8 * fbu * X * b
                + As2 * (sigma_s2 - 0.8 * fbu)
                + As1 * sigma_s1
            ) * 1000,

            (
                fbu * (1 - (1 - 0.8) * h / X) * h * b
                + As2 * (sigma_s2 - 0.8 * fbu)
                + As1 * sigma_s1
            ) * 1000
        ],
        default=np.nan
    )

    Mui = np.select(
        conditions,
        [
            (
                -As2 * (sigma_s2 - 0.8 * fbu) * (h / 2 - Cs)
                - As1 * Fsu * (h / 2 - d)
            ) * 1000,

            (
                0.8 * fbu * X * b * (h / 2 - 0.8 * X / 2)
                + As2 * (sigma_s2 - 0.8 * fbu) * (h / 2 - Cs)
                - As1 * Fsu * (h / 2 - d)
            ) * 1000,

            (
                0.8 * fbu * X * b * (h / 2 - 0.8 * X / 2)
                + As2 * (sigma_s2 - 0.8 * fbu) * (h / 2 - Cs)
                - As1 * sigma_s1 * (h / 2 - d)
            ) * 1000,

            (
                0.8 * fbu * X * b * (h / 2 - 0.8 * X / 2)
                + As2 * (sigma_s2 - 0.8 * fbu) * (h / 2 - Cs)
                - As1 * sigma_s1 * (h / 2 - d)
            ) * 1000,

            (
                0.8 * fbu * X * b * (h / 2 - 0.8 * X / 2)
                + As2 * (sigma_s2 - 0.8 * fbu) * (h / 2 - Cs)
                + As1 * sigma_s1 * (h / 2 - d)
            ) * 1000,

            (
                fbu * (1 - (1 - 0.8) * h / X)
                * h * b
                * (
                    h / 2
                    - (1 - (1 - 0.8) * h / X) * h / 2
                )
                + As2 * sigma_s2 * (h / 2 - Cs)
                + As1 * sigma_s1 * (h / 2 - d)
            ) * 1000
        ],
        default=np.nan
    )

    return TableauxCapacite(X=X, Nui=Nui, Mui=Mui, d=d, X_lim=X_lim, h=h)


def calcul_Mrd(
    Fc28,
    Fe,
    theta,
    gamma_b,
    gamma_s,
    Es,
    b,
    h,
    As1,
    c,
    As2,
    Cs,
    Nu
):
    """Calcule Mrd, la position de l'axe neutre, le pivot et le type de
    section pour un effort normal Nu donné.

    Reprend exactement la méthode d'interpolation du fichier original :
    recherche du premier changement de signe entre Nui et Nu le long du
    tableau X (ordonné de la traction pure vers la compression totale),
    puis interpolation linéaire de Mui et X à ce point.

    Retourne (Mrd, Y_axe, Pivot_section, Section), ou
    (None, None, None, None) si Nu est hors du domaine de résistance
    calculé de la section.
    """
    tab = _calculer_tableaux_capacite(
        Fc28, Fe, theta, gamma_b, gamma_s, Es, b, h, As1, c, As2, Cs
    )
    X, Nui, Mui, d, h = tab.X, tab.Nui, tab.Mui, tab.d, tab.h

    Mur_corr = np.full_like(Nui, np.nan, dtype=float)
    X_corr = np.full_like(Nui, np.nan, dtype=float)

    for i in range(1, len(Nui)):
        if (
            (Nui[i] >= Nu and Nui[i - 1] <= Nu)
            or
            (Nui[i] <= Nu and Nui[i - 1] >= Nu)
        ):
            if Nui[i] != Nui[i - 1]:
                Mur_corr[i] = (
                    Mui[i]
                    + (Mui[i - 1] - Mui[i])
                    * (Nui[i] - Nu)
                    / (Nui[i] - Nui[i - 1])
                )

                X_corr[i] = (
                    X[i]
                    + (X[i - 1] - X[i])
                    * (Nui[i] - Nu)
                    / (Nui[i] - Nui[i - 1])
                )

    min_cal = np.nanmin(Nui)
    max_cal = np.nanmax(Nui)

    if Nu < min_cal or Nu > max_cal:
        return None, None, None, None

    indices = np.where(~np.isnan(X_corr))[0]

    if len(indices) == 0:
        return None, None, None, None

    i = indices[0]

    Mrd = Mur_corr[i]
    X_final = X_corr[i]

    if X_final < 0:
        Y_axe = "< 0"
    elif X_final > h:
        Y_axe = "> h"
    else:
        Y_axe = 100 * X_final

    if X_final < 0.259 * d:
        Pivot_section = "Pivot A"
    elif X_final < h:
        Pivot_section = "Pivot B"
    else:
        Pivot_section = "Pivot C"

    if 0 < X_final < h:
        Section = "Section Partiellement Comprimée"
    elif X_final <= 0:
        Section = "Section Entierement Tendue"
    else:
        Section = "Section Entierement Comprimée"

    return Mrd, Y_axe, Pivot_section, Section
