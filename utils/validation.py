# -*- coding: utf-8 -*-
"""
utils/validation.py

Validation des données saisies par l'utilisateur, avant tout appel au
moteur de calcul. Retourne une liste de messages d'erreur en français
(liste vide = entrées valides). N'affiche rien, ne cache aucune
exception : c'est à l'appelant (GUI) de décider comment afficher ces
messages.
"""


def valider_entrees(donnees: dict) -> list:
    """Valide le dictionnaire de données saisies dans le GUI.

    Clés attendues (toutes obligatoires) :
        Fc28, Fe, theta, gamma_b, gamma_s, Es,
        b, h, c, Cs, As1, As2, Nu

    Retourne la liste des messages d'erreur (vide si tout est valide).
    """
    erreurs = []

    def positif_strict(cle, libelle):
        val = donnees.get(cle)
        if val is None:
            erreurs.append(f"Erreur : {libelle} est requis.")
        elif val <= 0:
            erreurs.append(f"Erreur : {libelle} doit être strictement supérieur à 0.")

    def positif_ou_nul(cle, libelle):
        val = donnees.get(cle)
        if val is None:
            erreurs.append(f"Erreur : {libelle} est requis.")
        elif val < 0:
            erreurs.append(f"Erreur : {libelle} doit être supérieur ou égal à 0.")

    # Matériaux
    positif_strict("Fc28", "la résistance du béton Fc28")
    positif_strict("theta", "le coefficient theta")
    positif_strict("gamma_b", "le coefficient de sécurité gamma_b")
    positif_strict("Fe", "la limite élastique de l'acier Fe")
    positif_strict("gamma_s", "le coefficient de sécurité gamma_s")
    positif_strict("Es", "le module d'élasticité de l'acier Es")

    # Géométrie
    positif_strict("b", "la largeur b")
    positif_strict("h", "la hauteur h")
    positif_ou_nul("c", "l'enrobage c")
    positif_ou_nul("Cs", "la position Cs")

    # Armatures
    positif_ou_nul("As1", "la section d'armature As1")
    positif_ou_nul("As2", "la section d'armature As2")

    # Cohérence géométrique : c et Cs doivent rester dans la section
    if donnees.get("h") is not None and donnees.get("c") is not None:
        if donnees["h"] > 0 and donnees["c"] >= donnees["h"]:
            erreurs.append(
                "Erreur : l'enrobage c doit être inférieur à la hauteur h."
            )
    if donnees.get("h") is not None and donnees.get("Cs") is not None:
        if donnees["h"] > 0 and donnees["Cs"] >= donnees["h"]:
            erreurs.append(
                "Erreur : la position Cs doit être inférieure à la hauteur h."
            )

    # Nu : doit être un nombre, mais peut être positif, nul ou négatif
    if donnees.get("Nu") is None:
        erreurs.append("Erreur : l'effort normal Nu est requis.")

    return erreurs
