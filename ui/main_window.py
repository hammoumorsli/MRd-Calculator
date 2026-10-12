# -*- coding: utf-8 -*-
"""
ui/main_window.py

Fenêtre principale de l'application. Ce module ne fait QUE :
    lire les valeurs saisies -> appeler le moteur (engine/) -> afficher.

Aucune équation de résistance des matériaux n'apparaît ici.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QFormLayout, QDoubleSpinBox, QPushButton, QLabel,
    QTabWidget, QTableWidget, QTableWidgetItem, QMessageBox,
    QAction, QSplitter, QHeaderView,
)

from engine.mrd import calcul_Mrd
from engine.interaction import calculate_interaction_diagram
from engine.materials import (
    DEFAUTS_BETON, DEFAUTS_ACIER, DEFAUTS_GEOMETRIE,
    DEFAUTS_ARMATURES, DEFAUTS_EFFORTS,
)
from utils.validation import valider_entrees
from utils.formatting import (
    formater_moment, formater_position_axe, message_hors_domaine,
)
from plots.interaction_plot import DiagrammeInteractionCanvas


def _champ_spin(valeur_defaut, minimum, maximum, decimales=3, pas=0.1):
    """Fabrique un QDoubleSpinBox préconfiguré."""
    spin = QDoubleSpinBox()
    spin.setRange(minimum, maximum)
    spin.setDecimals(decimales)
    spin.setSingleStep(pas)
    spin.setValue(valeur_defaut)
    spin.setAlignment(Qt.AlignRight)
    return spin


class MainWindow(QMainWindow):
    """Fenêtre principale : CALCUL DE FLEXION COMPOSÉE - Mrd."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Calcul de Flexion Composée — Mrd")
        self.resize(1200, 780)

        self._construire_menu()
        self._construire_widgets()
        self._construire_layout()

        self.dernier_diagramme = None  # engine.interaction.DiagrammeInteraction

    # ------------------------------------------------------------------
    # Construction de l'interface
    # ------------------------------------------------------------------

    def _construire_menu(self):
        menu = self.menuBar()

        menu_fichier = menu.addMenu("&Fichier")
        action_nouveau = QAction("Nouveau", self)
        action_nouveau.triggered.connect(self._reinitialiser_formulaire)
        action_quitter = QAction("Quitter", self)
        action_quitter.triggered.connect(self.close)
        menu_fichier.addAction(action_nouveau)
        menu_fichier.addSeparator()
        menu_fichier.addAction(action_quitter)

        menu_calcul = menu.addMenu("&Calcul")
        action_calculer = QAction("Calculer", self)
        action_calculer.triggered.connect(self._calculer)
        action_effacer = QAction("Effacer les résultats", self)
        action_effacer.triggered.connect(self._effacer_resultats)
        menu_calcul.addAction(action_calculer)
        menu_calcul.addAction(action_effacer)

        menu_affichage = menu.addMenu("&Affichage")
        action_export = QAction("Exporter (bientôt disponible)", self)
        action_export.setEnabled(False)
        menu_affichage.addAction(action_export)

        menu_aide = menu.addMenu("&Aide")
        action_apropos = QAction("À propos", self)
        action_apropos.triggered.connect(self._afficher_apropos)
        menu_aide.addAction(action_apropos)

    def _construire_widgets(self):
        # --- Matériaux ---
        self.spin_fc28 = _champ_spin(DEFAUTS_BETON["Fc28"], 1, 200, 1, 1)
        self.spin_theta = _champ_spin(DEFAUTS_BETON["theta"], 0.01, 5, 3, 0.01)
        self.spin_gamma_b = _champ_spin(DEFAUTS_BETON["gamma_b"], 0.5, 5, 2, 0.05)
        self.spin_fe = _champ_spin(DEFAUTS_ACIER["Fe"], 1, 2000, 1, 10)
        self.spin_gamma_s = _champ_spin(DEFAUTS_ACIER["gamma_s"], 0.5, 5, 2, 0.05)
        self.spin_es = _champ_spin(DEFAUTS_ACIER["Es"], 1000, 400000, 0, 1000)

        # --- Géométrie ---
        self.spin_b = _champ_spin(DEFAUTS_GEOMETRIE["b"], 1, 1000, 1, 1)
        self.spin_h = _champ_spin(DEFAUTS_GEOMETRIE["h"], 1, 1000, 1, 1)
        self.spin_c = _champ_spin(DEFAUTS_GEOMETRIE["c"], 0, 500, 1, 0.5)
        self.spin_cs = _champ_spin(DEFAUTS_GEOMETRIE["Cs"], 0, 500, 1, 0.5)

        # --- Armatures ---
        self.spin_as1 = _champ_spin(DEFAUTS_ARMATURES["As1"], 0, 1000, 2, 0.5)
        self.spin_as2 = _champ_spin(DEFAUTS_ARMATURES["As2"], 0, 1000, 2, 0.5)

        # --- Efforts ---
        self.spin_nu = _champ_spin(DEFAUTS_EFFORTS["Nu"], -1e6, 1e6, 1, 10)

        # --- Bouton calcul ---
        self.bouton_calculer = QPushButton("CALCULER Mrd")
        self.bouton_calculer.setMinimumHeight(38)
        self.bouton_calculer.clicked.connect(self._calculer)

        # --- Résultats ---
        self.label_mrd = QLabel("Mrd = —")
        self.label_x = QLabel("X = —")
        self.label_pivot = QLabel("Pivot = —")
        self.label_section = QLabel("Section = —")
        for lbl in (self.label_mrd, self.label_x, self.label_pivot, self.label_section):
            lbl.setStyleSheet("font-size: 11pt; font-weight: 600;")

        # --- Diagramme ---
        self.canvas_diagramme = DiagrammeInteractionCanvas(self)

        # --- Tableau de résultats ---
        self.table_resultats = QTableWidget(0, 4)
        self.table_resultats.setHorizontalHeaderLabels(["X [cm]", "N [kN]", "M [kN.m]", "Pivot / Domaine"])
        self.table_resultats.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_resultats.setEditTriggers(QTableWidget.NoEditTriggers)

    def _groupe_materiaux(self):
        groupe = QGroupBox("DONNÉES MATÉRIAUX")
        forme = QFormLayout()
        forme.addRow("Fc28 [MPa]", self.spin_fc28)
        forme.addRow("theta", self.spin_theta)
        forme.addRow("gamma_b", self.spin_gamma_b)
        forme.addRow("Fe [MPa]", self.spin_fe)
        forme.addRow("gamma_s", self.spin_gamma_s)
        forme.addRow("Es [MPa]", self.spin_es)
        groupe.setLayout(forme)
        return groupe

    def _groupe_geometrie(self):
        groupe = QGroupBox("GÉOMÉTRIE")
        forme = QFormLayout()
        forme.addRow("b [cm]", self.spin_b)
        forme.addRow("h [cm]", self.spin_h)
        forme.addRow("c [cm]  (position de As1)", self.spin_c)
        forme.addRow("Cs [cm]  (position de As2)", self.spin_cs)
        groupe.setLayout(forme)
        return groupe

    def _groupe_armatures(self):
        groupe = QGroupBox("ARMATURES")
        forme = QFormLayout()
        forme.addRow("As1 [cm²]", self.spin_as1)
        forme.addRow("As2 [cm²]", self.spin_as2)
        groupe.setLayout(forme)
        return groupe

    def _groupe_efforts(self):
        groupe = QGroupBox("EFFORTS")
        forme = QFormLayout()
        forme.addRow("Nu [kN]  (>0, =0 ou <0)", self.spin_nu)
        groupe.setLayout(forme)
        return groupe

    def _groupe_resultats(self):
        groupe = QGroupBox("RÉSULTATS")
        forme = QFormLayout()
        forme.addRow(self.label_mrd)
        forme.addRow(self.label_x)
        forme.addRow(self.label_pivot)
        forme.addRow(self.label_section)
        groupe.setLayout(forme)
        return groupe

    def _construire_layout(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout_principal = QVBoxLayout(central)

        titre = QLabel("CALCUL DE FLEXION COMPOSÉE — Mrd")
        titre.setAlignment(Qt.AlignCenter)
        titre.setStyleSheet("font-size: 16pt; font-weight: 700; padding: 6px;")
        layout_principal.addWidget(titre)

        # Panneau de saisie (haut)
        panneau_saisie = QGridLayout()
        panneau_saisie.addWidget(self._groupe_materiaux(), 0, 0)
        panneau_saisie.addWidget(self._groupe_geometrie(), 0, 1)
        panneau_saisie.addWidget(self._groupe_armatures(), 0, 2)
        panneau_saisie.addWidget(self._groupe_efforts(), 0, 3)
        layout_principal.addLayout(panneau_saisie)

        layout_principal.addWidget(self.bouton_calculer)

        # Résultats + diagramme (splitter)
        splitter = QSplitter(Qt.Horizontal)

        panneau_gauche = QWidget()
        layout_gauche = QVBoxLayout(panneau_gauche)
        layout_gauche.addWidget(self._groupe_resultats())
        layout_gauche.addStretch(1)
        splitter.addWidget(panneau_gauche)

        onglets = QTabWidget()
        onglets.addTab(self.canvas_diagramme, "Diagramme d'interaction N-M")
        onglets.addTab(self.table_resultats, "Tableau des résultats")
        splitter.addWidget(onglets)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

        layout_principal.addWidget(splitter, stretch=1)

    # ------------------------------------------------------------------
    # Logique d'interaction (lecture -> moteur -> affichage)
    # ------------------------------------------------------------------

    def _lire_entrees(self) -> dict:
        return dict(
            Fc28=self.spin_fc28.value(),
            Fe=self.spin_fe.value(),
            theta=self.spin_theta.value(),
            gamma_b=self.spin_gamma_b.value(),
            gamma_s=self.spin_gamma_s.value(),
            Es=self.spin_es.value(),
            b=self.spin_b.value(),
            h=self.spin_h.value(),
            As1=self.spin_as1.value(),
            c=self.spin_c.value(),
            As2=self.spin_as2.value(),
            Cs=self.spin_cs.value(),
            Nu=self.spin_nu.value(),
        )

    def _calculer(self):
        donnees = self._lire_entrees()

        erreurs = valider_entrees(donnees)
        if erreurs:
            QMessageBox.critical(self, "Erreurs de saisie", "\n".join(erreurs))
            return

        # 1) Point Nu/Mrd via le moteur (méthode d'interpolation d'origine)
        Mrd, Y_axe, Pivot, Section = calcul_Mrd(
            donnees["Fc28"], donnees["Fe"], donnees["theta"],
            donnees["gamma_b"], donnees["gamma_s"], donnees["Es"],
            donnees["b"], donnees["h"], donnees["As1"], donnees["c"],
            donnees["As2"], donnees["Cs"], donnees["Nu"],
        )

        # 2) Diagramme complet (mêmes équations, tableau entier)
        diagramme = calculate_interaction_diagram(
            donnees["Fc28"], donnees["Fe"], donnees["theta"],
            donnees["gamma_b"], donnees["gamma_s"], donnees["Es"],
            donnees["b"], donnees["h"], donnees["As1"], donnees["c"],
            donnees["As2"], donnees["Cs"],
        )
        self.dernier_diagramme = diagramme

        if Mrd is None:
            n_min = float(diagramme.N.min()) if len(diagramme.N) else float("nan")
            n_max = float(diagramme.N.max()) if len(diagramme.N) else float("nan")
            QMessageBox.warning(
                self, "Hors domaine",
                message_hors_domaine(donnees["Nu"], n_min, n_max),
            )
            self.label_mrd.setText("Mrd = —")
            self.label_x.setText("X = —")
            self.label_pivot.setText("Pivot = —")
            self.label_section.setText("Section = —")
            self.canvas_diagramme.tracer(diagramme, Nu=donnees["Nu"], Mrd=None)
            self._remplir_tableau(diagramme)
            return

        self.label_mrd.setText(f"Mrd = {formater_moment(Mrd)}")
        self.label_x.setText(f"X = {formater_position_axe(Y_axe)}")
        self.label_pivot.setText(f"Pivot = {Pivot}")
        self.label_section.setText(f"Section = {Section}")

        self.canvas_diagramme.tracer(diagramme, Nu=donnees["Nu"], Mrd=Mrd)
        self._remplir_tableau(diagramme)

    def _remplir_tableau(self, diagramme):
        self.table_resultats.setRowCount(len(diagramme.points))
        for ligne, point in enumerate(diagramme.points):
            self.table_resultats.setItem(ligne, 0, QTableWidgetItem(f"{point.X_cm:.2f}"))
            self.table_resultats.setItem(ligne, 1, QTableWidgetItem(f"{point.N_kN:.1f}"))
            self.table_resultats.setItem(ligne, 2, QTableWidgetItem(f"{point.M_kNm:.1f}"))
            self.table_resultats.setItem(ligne, 3, QTableWidgetItem(f"{point.pivot} / {point.section}"))

    def _effacer_resultats(self):
        self.label_mrd.setText("Mrd = —")
        self.label_x.setText("X = —")
        self.label_pivot.setText("Pivot = —")
        self.label_section.setText("Section = —")
        self.table_resultats.setRowCount(0)
        self.canvas_diagramme.reinitialiser()
        self.dernier_diagramme = None

    def _reinitialiser_formulaire(self):
        self.spin_fc28.setValue(DEFAUTS_BETON["Fc28"])
        self.spin_theta.setValue(DEFAUTS_BETON["theta"])
        self.spin_gamma_b.setValue(DEFAUTS_BETON["gamma_b"])
        self.spin_fe.setValue(DEFAUTS_ACIER["Fe"])
        self.spin_gamma_s.setValue(DEFAUTS_ACIER["gamma_s"])
        self.spin_es.setValue(DEFAUTS_ACIER["Es"])
        self.spin_b.setValue(DEFAUTS_GEOMETRIE["b"])
        self.spin_h.setValue(DEFAUTS_GEOMETRIE["h"])
        self.spin_c.setValue(DEFAUTS_GEOMETRIE["c"])
        self.spin_cs.setValue(DEFAUTS_GEOMETRIE["Cs"])
        self.spin_as1.setValue(DEFAUTS_ARMATURES["As1"])
        self.spin_as2.setValue(DEFAUTS_ARMATURES["As2"])
        self.spin_nu.setValue(DEFAUTS_EFFORTS["Nu"])
        self._effacer_resultats()

    def _afficher_apropos(self):
        QMessageBox.information(
            self, "À propos",
            "Calcul de Flexion Composée — Mrd\n\n"
            "Moteur de calcul fidèle au fichier Mrd.py original.\n"
            "Diagramme d'interaction N-M construit à partir des mêmes "
            "équations, sur l'ensemble des domaines (Pivot A, B, C).",
        )
