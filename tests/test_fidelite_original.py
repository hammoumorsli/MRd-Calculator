# -*- coding: utf-8 -*-
"""
tests/test_fidelite_original.py

Compare les résultats de engine.mrd.calcul_Mrd avec ceux du fichier
Mrd_original.py fourni par l'utilisateur, pour une série de cas
(traction, compression, Nu=0, sections tendues/partiellement
comprimées/entièrement comprimées, Nu hors domaine).

IMPORTANT : Mrd_original.py n'a PAS la conversion cm->m de b et h
(elle est commentée dans l'original). Pour comparer à isopérimètre,
ce test appelle donc Mrd_original avec b et h déjà en MÈTRES, et
engine.mrd (qui attend b, h en cm comme le GUI) avec les mêmes
dimensions exprimées en CENTIMÈTRES. Les deux doivent donner un
résultat identique (aux erreurs d'arrondi flottant près).
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

import Mrd_original
from engine.mrd import calcul_Mrd

# Jeu de paramètres matériaux commun
MATERIAUX = dict(Fc28=25, Fe=500, theta=0.85, gamma_b=1.5, gamma_s=1.15, Es=200000)

# Géométrie en mètres (pour l'original) et en centimètres (pour engine.mrd)
B_M, H_M, C_M, CS_M = 0.30, 0.50, 0.04, 0.04
B_CM, H_CM, C_CM, CS_CM = 30.0, 50.0, 4.0, 4.0

AS1_CM2, AS2_CM2 = 8.0, 8.0

CAS_DE_TEST = [
    ("Compression modérée, Nu=500 kN", 500),
    ("Nu = 0 (flexion simple)", 0),
    ("Traction, Nu=-300 kN", -300),
    ("Forte compression, Nu=3000 kN", 3000),
    ("Nu hors domaine (trop élevé)", 1e9),
    ("Nu hors domaine (trop négatif)", -1e9),
]


def comparer(nom, Nu):
    Mrd_orig, Y_orig, Pivot_orig, Section_orig = Mrd_original.calcul_Mrd(
        MATERIAUX["Fc28"], MATERIAUX["Fe"], MATERIAUX["theta"],
        MATERIAUX["gamma_b"], MATERIAUX["gamma_s"], MATERIAUX["Es"],
        B_M, H_M, AS1_CM2, C_M * 100, AS2_CM2, CS_M * 100, Nu
    )
    # Mrd_original convertit c/Cs (cm->m) et As1/As2 (cm2->m2) en interne,
    # mais PAS b/h : on lui passe donc b/h déjà en m, et c/Cs en cm (car
    # il les convertit lui-même), exactement comme dans le fichier fourni.

    Mrd_new, Y_new, Pivot_new, Section_new = calcul_Mrd(
        MATERIAUX["Fc28"], MATERIAUX["Fe"], MATERIAUX["theta"],
        MATERIAUX["gamma_b"], MATERIAUX["gamma_s"], MATERIAUX["Es"],
        B_CM, H_CM, AS1_CM2, C_CM, AS2_CM2, CS_CM, Nu
    )
    # engine.mrd attend TOUT en cm (b, h inclus) : c'est la seule
    # différence volontaire par rapport à l'original.

    if Mrd_orig is None and Mrd_new is None:
        statut = "OK (tous deux hors domaine)"
        diff = 0.0
    elif Mrd_orig is None or Mrd_new is None:
        statut = "ECHEC (un seul est None)"
        diff = float("nan")
    else:
        diff = abs(Mrd_orig - Mrd_new)
        statut = "OK" if diff < 1e-6 and Pivot_orig == Pivot_new and Section_orig == Section_new else "ECHEC"

    print(f"[{statut}] {nom}")
    print(f"    original    : Mrd={Mrd_orig}, Pivot={Pivot_orig}, Section={Section_orig}")
    print(f"    engine.mrd  : Mrd={Mrd_new}, Pivot={Pivot_new}, Section={Section_new}")
    print(f"    ecart Mrd   : {diff}")
    return statut.startswith("OK")


def main():
    resultats = [comparer(nom, Nu) for nom, Nu in CAS_DE_TEST]
    print()
    if all(resultats):
        print(f"=> Tous les cas ({len(resultats)}) sont identiques au fichier original.")
        return 0
    else:
        echecs = resultats.count(False)
        print(f"=> {echecs} cas différent(s) du fichier original.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
