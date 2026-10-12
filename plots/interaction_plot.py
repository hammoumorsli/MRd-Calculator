# -*- coding: utf-8 -*-
"""
plots/interaction_plot.py

Widget matplotlib intégré (FigureCanvasQTAgg) affichant le diagramme
d'interaction N-M de la section : courbe complète (tous domaines, y
compris Pivot C), point (Mrd, Nu), ligne N = Nu, axes M=0 / N=0.

Ne recalcule rien : reçoit un objet engine.interaction.DiagrammeInteraction
et, en option, le point (Mrd, Nu) déjà calculé par engine.mrd.calcul_Mrd.
"""

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure


class DiagrammeInteractionCanvas(FigureCanvasQTAgg):
    """Canvas matplotlib affichant le diagramme d'interaction N-M.

    Axe horizontal : M [kN.m] (respecte le signe réel de Mui, pas de abs()).
    Axe vertical    : N [kN].
    """

    def __init__(self, parent=None):
        self.figure = Figure(figsize=(6, 5), tight_layout=True)
        super().__init__(self.figure)
        self.setParent(parent)
        self.ax = self.figure.add_subplot(111)
        self._dessiner_vide()

    def _dessiner_vide(self):
        self.ax.clear()
        self.ax.set_xlabel("M [kN.m]")
        self.ax.set_ylabel("N [kN]")
        self.ax.set_title("Diagramme d'interaction N-M")
        self.ax.grid(True, linewidth=0.4, alpha=0.5)
        self.ax.axhline(0, color="black", linewidth=0.8)
        self.ax.axvline(0, color="black", linewidth=0.8)
        self.draw()

    def tracer(self, diagramme, Nu=None, Mrd=None):
        """Trace le diagramme d'interaction complet.

        diagramme : engine.interaction.DiagrammeInteraction
        Nu, Mrd   : effort normal saisi et moment résistant trouvé
                    (facultatifs — si absents, seule la courbe est tracée)
        """
        self.ax.clear()

        self.ax.plot(
            diagramme.M, diagramme.N,
            color="#1f5fa8", linewidth=1.6,
            label="Capacité de la section",
        )

        self.ax.axhline(0, color="black", linewidth=0.8)
        self.ax.axvline(0, color="black", linewidth=0.8)
        self.ax.grid(True, linewidth=0.4, alpha=0.5)

        if Nu is not None:
            self.ax.axhline(
                Nu, color="#c0392b", linewidth=1.0, linestyle="--",
                label=f"N = Nu = {Nu:.0f} kN",
            )

        if Nu is not None and Mrd is not None:
            self.ax.plot(
                [Mrd], [Nu],
                marker="o", markersize=8,
                color="#e67e22", markeredgecolor="black",
                zorder=5,
                label=f"(Mrd, Nu) = ({Mrd:.1f}, {Nu:.0f})",
            )
            self.ax.annotate(
                f"Mrd = {Mrd:.1f} kN.m",
                xy=(Mrd, Nu),
                xytext=(12, 12),
                textcoords="offset points",
                fontsize=9,
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#e67e22"),
            )

        self.ax.set_xlabel("M [kN.m]")
        self.ax.set_ylabel("N [kN]")
        self.ax.set_title("Diagramme d'interaction N-M")
        self.ax.legend(loc="best", fontsize=8)

        self.draw()

    def reinitialiser(self):
        self._dessiner_vide()
