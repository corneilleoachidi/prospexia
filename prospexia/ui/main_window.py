"""Fenêtre principale : barre latérale (paramètres de recherche) + zone de résultats."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

from PySide6.QtCore import QModelIndex, Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from prospexia.config import Settings
from prospexia.core.export import export_csv, export_pdf, export_xlsx
from prospexia.core.models import (
    ProgressEvent,
    Prospect,
    RelevanceMode,
    SearchRequest,
    Verdict,
    WebsiteStatus,
)
from prospexia.data.countries import COUNTRIES, COUNTRY_BY_CODE
from prospexia.ui import theme
from prospexia.ui.widgets.common import Badge, StatCard, section_label
from prospexia.ui.widgets.dialogs import ProspectDialog, SettingsDialog
from prospexia.ui.widgets.results_table import VERDICT_HELP, ResultsTable
from prospexia.ui.widgets.sector_picker import SectorPicker
from prospexia.ui.worker import PipelineWorker

MAX_CHOICES = [5, 10, 20, 50, 100, 200, 300]


class MainWindow(QMainWindow):
    def __init__(self, settings: Settings):
        super().__init__()
        self.settings = settings
        self.worker: PipelineWorker | None = None
        self.results: list[Prospect] = []
        self.setWindowTitle("Prospexia — prospection web & SEO")
        self.resize(1440, 860)
        self.setMinimumSize(1100, 680)

        root = QWidget(); self.setCentralWidget(root)
        h = QHBoxLayout(root); h.setContentsMargins(0, 0, 0, 0); h.setSpacing(0)
        h.addWidget(self._build_sidebar())
        h.addWidget(self._build_main(), 1)
        self._restore_prefs()
        self._refresh_key_badges()

    # ================================================================== sidebar
    def _build_sidebar(self) -> QWidget:
        side = QFrame(); side.setObjectName("Sidebar"); side.setFixedWidth(360)
        outer = QVBoxLayout(side); outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget(); lay = QVBoxLayout(inner)
        lay.setContentsMargins(22, 22, 22, 16); lay.setSpacing(10)

        brand = QLabel("◆ Prospexia"); brand.setObjectName("Brand")
        sub = QLabel("Trouvez les entreprises qui ont besoin d'un site web ou de SEO.")
        sub.setObjectName("BrandSub"); sub.setWordWrap(True)
        lay.addWidget(brand); lay.addWidget(sub); lay.addSpacing(8)

        lay.addWidget(section_label("Pays"))
        self.country = QComboBox()
        for c in COUNTRIES:
            self.country.addItem(f"{c.flag}  {c.name_fr}", c.code)
        self.country.currentIndexChanged.connect(self._on_country_changed)
        lay.addWidget(self.country)
        self.country_hint = QLabel(); self.country_hint.setObjectName("Hint"); self.country_hint.setWordWrap(True)
        self.country_hint.setOpenExternalLinks(True)
        lay.addWidget(self.country_hint)

        lay.addWidget(section_label("Secteurs d'activité"))
        self.sectors = SectorPicker()
        self.sectors.changed.connect(self._update_launch_state)
        lay.addWidget(self.sectors)

        lay.addWidget(section_label("Nombre max. de résultats"))
        pills = QHBoxLayout(); pills.setSpacing(4)
        self.max_group = QButtonGroup(self); self.max_group.setExclusive(True)
        for n in MAX_CHOICES:
            b = QPushButton(str(n)); b.setObjectName("Pill"); b.setCheckable(True)
            b.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            self.max_group.addButton(b, n); pills.addWidget(b)
        lay.addLayout(pills)

        lay.addWidget(section_label("Mode de pertinence"))
        seg = QHBoxLayout(); seg.setSpacing(6)
        self.mode_group = QButtonGroup(self); self.mode_group.setExclusive(True)
        self.btn_strict = QPushButton("Strict"); self.btn_flex = QPushButton("Flexible")
        for i, b in enumerate((self.btn_strict, self.btn_flex)):
            b.setObjectName("Segment"); b.setCheckable(True); b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            self.mode_group.addButton(b, i); seg.addWidget(b)
        self.mode_group.idClicked.connect(self._update_mode_hint)
        lay.addLayout(seg)
        self.mode_hint = QLabel(); self.mode_hint.setObjectName("Hint"); self.mode_hint.setWordWrap(True)
        lay.addWidget(self.mode_hint)

        lay.addSpacing(6)
        self.launch = QPushButton("🚀  Lancer la prospection"); self.launch.setObjectName("Primary")
        self.launch.setCursor(Qt.CursorShape.PointingHandCursor)
        self.launch.clicked.connect(self._start)
        self.stop = QPushButton("■  Arrêter"); self.stop.setObjectName("Danger"); self.stop.hide()
        self.stop.clicked.connect(self._stop)
        lay.addWidget(self.launch); lay.addWidget(self.stop)
        lay.addStretch()

        scroll.setWidget(inner); outer.addWidget(scroll, 1)

        foot = QFrame(); fl = QHBoxLayout(foot); fl.setContentsMargins(22, 10, 22, 14)
        self.badge_google = Badge("Google Places"); self.badge_serp = Badge("SerpAPI")
        fl.addWidget(self.badge_google); fl.addWidget(self.badge_serp); fl.addStretch()
        gear = QPushButton("⚙"); gear.setObjectName("Icon"); gear.setToolTip("Paramètres (clés API)")
        gear.setCursor(Qt.CursorShape.PointingHandCursor); gear.clicked.connect(self._open_settings)
        fl.addWidget(gear)
        outer.addWidget(foot)
        return side

    # ================================================================== main area
    def _build_main(self) -> QWidget:
        main = QWidget(); lay = QVBoxLayout(main)
        lay.setContentsMargins(26, 22, 26, 20); lay.setSpacing(14)

        head = QHBoxLayout()
        tcol = QVBoxLayout(); tcol.setSpacing(2)
        self.title = QLabel("Prêt à prospecter"); self.title.setObjectName("PageTitle")
        self.subtitle = QLabel("Choisissez un pays et un ou plusieurs secteurs, puis lancez la recherche.")
        self.subtitle.setObjectName("PageSub"); self.subtitle.setWordWrap(True)
        tcol.addWidget(self.title); tcol.addWidget(self.subtitle)
        head.addLayout(tcol, 1)
        self.btn_csv = QPushButton("⤓  CSV"); self.btn_xlsx = QPushButton("⤓  Excel")
        self.btn_pdf = QPushButton("⤓  PDF"); self.btn_pdf.setToolTip("Rapport PDF prêt à partager (WhatsApp, e-mail…)")
        for b in (self.btn_csv, self.btn_xlsx, self.btn_pdf):
            b.setEnabled(False); b.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_csv.clicked.connect(lambda: self._export("csv"))
        self.btn_xlsx.clicked.connect(lambda: self._export("xlsx"))
        self.btn_pdf.clicked.connect(lambda: self._export("pdf"))
        head.addWidget(self.btn_csv); head.addWidget(self.btn_xlsx); head.addWidget(self.btn_pdf)
        lay.addLayout(head)

        stats = QHBoxLayout(); stats.setSpacing(12)
        self.card_analyzed = StatCard("Analysées", theme.ACCENT_2)
        self.card_found = StatCard("Retenues", theme.TEXT)
        self.card_priority = StatCard("Prioritaires", theme.SUCCESS)
        self.card_nosite = StatCard("Sans site web", theme.DANGER)
        self.card_obsolete = StatCard("Site obsolète / HS", theme.WARN)
        for c in (self.card_analyzed, self.card_found, self.card_priority, self.card_nosite, self.card_obsolete):
            stats.addWidget(c)
        lay.addLayout(stats)

        prog = QVBoxLayout(); prog.setSpacing(4)
        self.status = QLabel(""); self.status.setObjectName("StatusLabel")
        self.progress = QProgressBar(); self.progress.setFixedHeight(8); self.progress.setRange(0, 1); self.progress.setValue(0)
        prog.addWidget(self.status); prog.addWidget(self.progress)
        lay.addLayout(prog)

        tools = QHBoxLayout()
        self.filter = QLineEdit(); self.filter.setPlaceholderText("Filtrer par nom, ville, secteur…")
        self.filter.setClearButtonEnabled(True); self.filter.setMaximumWidth(340)
        self.show_out = QCheckBox("Afficher les hors cible")
        self.count_label = QLabel(""); self.count_label.setObjectName("Hint")
        tools.addWidget(self.filter); tools.addWidget(self.show_out); tools.addStretch()
        for verdict in (Verdict.PRIORITY, Verdict.TARGET, Verdict.OUT):
            b = Badge(verdict.label, theme.VERDICT_COLORS[verdict.value])
            b.setToolTip(VERDICT_HELP[verdict]); b.setCursor(Qt.CursorShape.WhatsThisCursor)
            tools.addWidget(b)
        help_btn = QPushButton("?"); help_btn.setObjectName("Pill"); help_btn.setFixedWidth(28)
        help_btn.setToolTip("Comprendre les verdicts et le score"); help_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        help_btn.clicked.connect(self._show_help)
        tools.addWidget(help_btn); tools.addSpacing(8); tools.addWidget(self.count_label)
        lay.addLayout(tools)

        self.table = ResultsTable()
        self.filter.textChanged.connect(lambda t: (self.table.proxy.set_text(t), self._update_count()))
        self.show_out.toggled.connect(lambda v: (self.table.proxy.set_show_out(v), self._update_count()))
        self.table.doubleClicked.connect(self._open_detail)
        lay.addWidget(self.table, 1)

        empty_hint = QLabel("Double-cliquez sur une ligne pour voir le diagnostic complet et ouvrir la fiche / le site.")
        empty_hint.setObjectName("Hint")
        lay.addWidget(empty_hint)
        return main

    # ================================================================== prefs
    def _restore_prefs(self) -> None:
        s = self.settings
        idx = self.country.findData(s.last_country)
        self.country.setCurrentIndex(max(0, idx))
        self._on_country_changed()
        self.sectors.set_selection(s.last_sectors)
        n = s.last_max_results if s.last_max_results in MAX_CHOICES else 20
        self.max_group.button(n).setChecked(True)
        (self.btn_flex if s.last_mode == "flexible" else self.btn_strict).setChecked(True)
        self._update_mode_hint()
        self._update_launch_state()

    def _save_prefs(self) -> None:
        s = self.settings
        s.last_country = self.country.currentData()
        s.last_sectors = self.sectors.sector_keys()
        s.last_max_results = self.max_group.checkedId()
        s.last_mode = self._mode().value
        s.save()

    def _mode(self) -> RelevanceMode:
        return RelevanceMode.FLEXIBLE if self.btn_flex.isChecked() else RelevanceMode.STRICT

    def _on_country_changed(self) -> None:
        c = COUNTRY_BY_CODE[self.country.currentData()]
        reg = f' · <a href="{c.registry}">registre officiel</a>' if c.registry else ""
        self.country_hint.setText(f"Langue de recherche : <b>{c.lang.upper()}</b> · {len(c.cities)} villes couvertes{reg}")

    def _update_mode_hint(self) -> None:
        if self._mode() is RelevanceMode.STRICT:
            self.mode_hint.setText("Strict — entreprises sans aucun site web et quasi invisibles en ligne.")
        else:
            self.mode_hint.setText("Flexible — site absent, obsolète ou hors service, et faible présence en ligne.")

    def _update_launch_state(self) -> None:
        ok = bool(self.sectors.sector_keys() or self.sectors.custom_sectors())
        self.launch.setEnabled(ok and self.worker is None)

    def _refresh_key_badges(self) -> None:
        self.badge_google.setText("Google Places ✓" if self.settings.has_google else "OpenStreetMap (sans clé)")
        self.badge_google.set_color(theme.SUCCESS if self.settings.has_google else theme.WARN)
        self.badge_serp.setText("SerpAPI ✓" if self.settings.has_serpapi else "DuckDuckGo (sans clé)")
        self.badge_serp.set_color(theme.SUCCESS if self.settings.has_serpapi else theme.WARN)

    def _open_settings(self) -> None:
        if SettingsDialog(self.settings, self).exec():
            self._refresh_key_badges()

    # ================================================================== run
    def _start(self) -> None:
        req = SearchRequest(
            country_code=self.country.currentData(),
            sector_keys=self.sectors.sector_keys(),
            custom_sectors=self.sectors.custom_sectors(),
            max_results=self.max_group.checkedId(),
            mode=self._mode(),
        )
        self._save_prefs()
        self.results.clear(); self.table.model_.clear()
        for c in (self.card_analyzed, self.card_found, self.card_priority, self.card_nosite, self.card_obsolete):
            c.set(0)
        self.btn_csv.setEnabled(False); self.btn_xlsx.setEnabled(False); self.btn_pdf.setEnabled(False)
        c = COUNTRY_BY_CODE[req.country_code]
        self.title.setText(f"{c.flag} {c.name_fr} — {', '.join(self.sectors.labels())}")
        self.subtitle.setText(f"Mode {req.mode.label} · jusqu'à {req.max_results} prospects")
        self.progress.setRange(0, 0)
        self.status.setText("Démarrage…")
        self.launch.hide(); self.stop.show()
        self._set_form_enabled(False)

        self.worker = PipelineWorker(self.settings, req, self)
        self.worker.progress.connect(self._on_progress)
        self.worker.prospect.connect(self._on_prospect)
        self.worker.finished_ok.connect(self._on_finished)
        self.worker.cancelled.connect(lambda: self._on_end("Recherche interrompue."))
        self.worker.failed.connect(self._on_failed)
        self.worker.start()

    def _stop(self) -> None:
        if self.worker:
            self.status.setText("Arrêt en cours…"); self.stop.setEnabled(False)
            self.worker.cancel()

    def _set_form_enabled(self, v: bool) -> None:
        for w in (self.country, self.sectors, *self.max_group.buttons(), self.btn_strict, self.btn_flex):
            w.setEnabled(v)

    def _on_progress(self, e: ProgressEvent) -> None:
        self.status.setText(e.message)
        if e.total:
            self.progress.setRange(0, e.total); self.progress.setValue(e.current)
        else:
            self.progress.setRange(0, 0)

    def _on_prospect(self, p: Prospect) -> None:
        self.table.model_.add(p)
        self.card_analyzed.set(self.table.model_.rowCount())
        if p.verdict is not Verdict.OUT:
            self.results.append(p)
            self.card_found.set(len(self.results))
            self.card_priority.set(sum(1 for r in self.results if r.verdict is Verdict.PRIORITY))
            self.card_nosite.set(sum(1 for r in self.results if r.website.status in (WebsiteStatus.NONE, WebsiteStatus.SOCIAL_ONLY, WebsiteStatus.THIRD_PARTY)))
            self.card_obsolete.set(sum(1 for r in self.results if r.website.status in (WebsiteStatus.OBSOLETE, WebsiteStatus.DEAD)))
        self._update_count()

    def _on_finished(self, results: list) -> None:
        n = len(results)
        self._on_end(f"Terminé — {n} prospect(s) retenu(s) sur {self.table.model_.rowCount()} entreprise(s) analysée(s).")
        if n == 0:
            QMessageBox.information(self, "Aucun résultat",
                                    "Aucune entreprise ne correspond aux critères.\n"
                                    "Essayez le mode Flexible, d'autres secteurs, ou vérifiez vos clés API.")

    def _on_failed(self, msg: str) -> None:
        self._on_end("Erreur : " + msg)
        QMessageBox.critical(self, "Erreur", msg)

    def _on_end(self, msg: str) -> None:
        self.status.setText(msg)
        self.progress.setRange(0, 1); self.progress.setValue(1)
        self.worker = None
        self.stop.hide(); self.stop.setEnabled(True); self.launch.show()
        self._set_form_enabled(True); self._update_launch_state()
        has = bool(self.results)
        self.btn_csv.setEnabled(has); self.btn_xlsx.setEnabled(has); self.btn_pdf.setEnabled(has)

    def _update_count(self) -> None:
        self.count_label.setText(f"{self.table.proxy.rowCount()} ligne(s) affichée(s)")

    # ================================================================== actions
    def _show_help(self) -> None:
        box = QMessageBox(self); box.setWindowTitle("Verdicts et score")
        box.setTextFormat(Qt.TextFormat.RichText)
        box.setText(
            "<h3 style='margin:0'>Comment lire les résultats</h3>"
            "<p><b style='color:#22c55e'>Prioritaire</b> — " + VERDICT_HELP[Verdict.PRIORITY] + "</p>"
            "<p><b style='color:#f59e0b'>Cible</b> — " + VERDICT_HELP[Verdict.TARGET] + "</p>"
            "<p><b style='color:#8b91a7'>Hors cible</b> — " + VERDICT_HELP[Verdict.OUT] + "</p>"
            "<p><b>Score de présence (0–100)</b> : 0 = invisible en ligne, 100 = très présent. "
            "Il additionne l'état du site (0 à 60 pts), les réseaux sociaux trouvés, les résultats web sur le nom, "
            "les annuaires et les avis Google.</p>"
            "<p><b>Mode</b> : <i>Strict</i> ne retient que les entreprises sans site propre et quasi invisibles "
            "(score ≤ 30) ; <i>Flexible</i> accepte aussi les sites obsolètes ou HS et une présence modérée (score ≤ 50).</p>"
            "<p><b>Opportunité</b> : prestation suggérée — création de site, refonte + SEO, ou SEO seul.</p>"
            "<p style='color:#8b91a7'>Survolez une cellule Verdict ou Score pour voir le détail du calcul ; "
            "double-cliquez une ligne pour la fiche complète.</p>")
        box.exec()

    def _open_detail(self, idx: QModelIndex) -> None:
        p = self.table.prospect_at(idx)
        if p:
            ProspectDialog(p, self).exec()

    def _export(self, kind: str) -> None:
        rows = self.table.visible_prospects() or self.results
        if not rows:
            return
        c = COUNTRY_BY_CODE[self.country.currentData()]
        stamp = dt.datetime.now().strftime("%Y%m%d-%H%M")
        path = Path(self.settings.export_dir) / f"prospexia_{c.code}_{stamp}.{kind}"
        try:
            if kind == "csv":
                path = export_csv(rows, path)
            elif kind == "xlsx":
                path = export_xlsx(rows, path)
            else:
                path = export_pdf(rows, path, self.title.text(), self.subtitle.text())
        except OSError as exc:
            QMessageBox.critical(self, "Export impossible", str(exc)); return
        self.status.setText(f"Export : {path}")
        box = QMessageBox(self); box.setWindowTitle("Export terminé")
        box.setText(f"{len(rows)} prospect(s) exporté(s) vers :\n{path}")
        open_btn = box.addButton("Ouvrir le dossier", QMessageBox.ButtonRole.ActionRole)
        box.addButton(QMessageBox.StandardButton.Ok)
        box.exec()
        if box.clickedButton() is open_btn:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.parent)))

    def closeEvent(self, event) -> None:
        if self.worker:
            self.worker.cancel(); self.worker.wait(3000)
        self._save_prefs()
        super().closeEvent(event)
