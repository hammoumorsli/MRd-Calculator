# -*- coding: utf-8 -*-
"""
engine/materials.py

Constantes matériaux et fonctions de conversion d'unités.

Ce module ne contient AUCUNE équation de résistance des matériaux :
il ne fait que centraliser les valeurs par défaut affichées dans le
GUI et les conversions d'unités (cm -> m, cm² -> m²) nécessaires
pour appeler le moteur de calcul `engine.mrd.calcul_Mrd`.

Convention d'unités du moteur (engine/mrd.py) :
    Fc28, Fe, Es       : MPa
    b, h, c, Cs        : mètres (m)
    As1, As2           : mètres carrés (m²)
    Nu                 : kilonewtons (kN)
    Mrd (sortie)       : kilonewton-mètres (kN.m)

Convention d'unités du GUI (ce que l'ingénieur saisit) :
    Fc28, Fe, Es       : MPa
    b, h, c, Cs        : centimètres (cm)
    As1, As2           : centimètres carrés (cm²)
    Nu                 : kilonewtons (kN)

La conversion cm -> m (b, h, c, Cs) et cm² -> m² (As1, As2) doit être
faite UNE SEULE FOIS, au moment de l'appel au moteur. Elle est
centralisée ici pour éviter toute double conversion.
"""

# ---------------------------------------------------------------------------
# Valeurs par défaut (affichées dans le GUI, modifiables par l'utilisateur)
# ---------------------------------------------------------------------------

DEFAUTS_BETON = {
    "Fc28": 25.0,     # MPa
    "theta": 0.85,    # coefficient de durée d'application du chargement
    "gamma_b": 1.2,   # NOTE : valeur d'exemple fournie par l'utilisateur.
                      # Le BAEL/RPA usuel retient 1.5 (durable) / 1.15 (accidentel).
                      # Valeur conservée telle quelle : à confirmer avant utilisation réelle.
}

DEFAUTS_ACIER = {
    "Fe": 500.0,      # MPa
    "gamma_s": 1.0,   # NOTE : valeur d'exemple fournie par l'utilisateur.
                      # Le BAEL/RPA usuel retient 1.15 (durable) / 1.0 (accidentel).
                      # Valeur conservée telle quelle : à confirmer avant utilisation réelle.
    "Es": 200000.0,   # MPa
}

DEFAUTS_GEOMETRIE = {
    "b": 30.0,   # cm
    "h": 50.0,   # cm
    "c": 4.0,    # cm (enrobage / position de As1)
    "Cs": 4.0,   # cm (position de As2)
}

DEFAUTS_ARMATURES = {
    "As1": 8.0,  # cm²
    "As2": 8.0,  # cm²
}

DEFAUTS_EFFORTS = {
    "Nu": 0.0,   # kN
}


# ---------------------------------------------------------------------------
# Conversions d'unités
# ---------------------------------------------------------------------------

def cm_vers_m(valeur_cm: float) -> float:
    """Convertit une longueur de centimètres en mètres."""
    return valeur_cm / 100.0


def cm2_vers_m2(valeur_cm2: float) -> float:
    """Convertit une aire de centimètres carrés en mètres carrés."""
    return valeur_cm2 / 10000.0
