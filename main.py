# -*- coding: utf-8 -*-
"""
main.py

Point d'entrée de l'application. Lancement :
    python main.py
"""
import sys

from PyQt5.QtWidgets import QApplication

from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Calcul de Flexion Composée — Mrd")
    fenetre = MainWindow()
    fenetre.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
