"""Boîtes de dialogue : paramètres (clés API) et fiche détaillée d'un prospect."""
from __future__ import annotations

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from prospexia.config import Settings
from prospexia.core.models import Prospect
from prospexia.ui import theme
from prospexia.ui.widgets.common import Badge, section_label


class SettingsDialog(QDialog):
    def __init__(self, settings: Settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Paramètres — Prospexia")
        self.setMinimumWidth(560)
        lay = QVBoxLayout(self)
        lay.setSpacing(12)

        title = QLabel("Paramètres")
        title.setObjectName("PageTitle")
        lay.addWidget(title)
        sub = QLabel("Les clés sont stockées localement dans votre dossier de configuration utilisateur.")
        sub.setObjectName("PageSub")
        sub.setWordWrap(True)
        lay.addWidget(sub)

        card = QFrame(); card.setObjectName("Card")
        form = QFormLayout(card)
        form.setContentsMargins(16, 16, 16, 16)
        form.setSpacing(10)

        self.google = QLineEdit(settings.google_places_api_key)
        self.google.setEchoMode(QLineEdit.EchoMode.Password)
        self.google.setPlaceholderText("AIza…  (Places API (New) activée sur Google Cloud)")
        self.serp = QLineEdit(settings.serpapi_api_key)
        self.serp.setEchoMode(QLineEdit.EchoMode.Password)
        self.serp.setPlaceholderText("Clé SerpAPI (serpapi.com) — sinon repli DuckDuckGo")
        self.concurrency = QSpinBox(); self.concurrency.setRange(1, 32); self.concurrency.setValue(settings.concurrency)
        self.timeout = QSpinBox(); self.timeout.setRange(3, 60); self.timeout.setSuffix(" s")
        self.timeout.setValue(int(settings.request_timeout))
        exp_row = QHBoxLayout()
        self.export_dir = QLineEdit(settings.export_dir)
        browse = QPushButton("…"); browse.setFixedWidth(36)
        browse.clicked.connect(self._browse)
        exp_row.addWidget(self.export_dir); exp_row.addWidget(browse)

        form.addRow(section_label("Google Places API"), self.google)
        form.addRow(section_label("SerpAPI"), self.serp)
        form.addRow(section_label("Analyses simultanées"), self.concurrency)
        form.addRow(section_label("Délai réseau"), self.timeout)
        form.addRow(section_label("Dossier d'export"), exp_row)
        lay.addWidget(card)

        card2 = QFrame(); card2.setObjectName("Card")
        form2 = QFormLayout(card2)
        form2.setContentsMargins(16, 16, 16, 16)
        form2.setSpacing(10)
        self.use_cache = QCheckBox("Réutiliser les analyses et recherches récentes")
        self.use_cache.setChecked(settings.use_cache)
        self.use_cache.setToolTip("Une recherche identique (ou partiellement identique) relancée pendant la période\n"
                                  "de validité ne consomme aucun crédit Google Places / SerpAPI.")
        cache_row = QHBoxLayout()
        self.cache_ttl = QSpinBox(); self.cache_ttl.setRange(1, 365); self.cache_ttl.setSuffix(" jours")
        self.cache_ttl.setValue(settings.cache_ttl_days)
        self.cache_stats = QLabel(); self.cache_stats.setObjectName("Hint")
        clear = QPushButton("Vider le cache"); clear.setObjectName("Danger"); clear.clicked.connect(self._clear_cache)
        cache_row.addWidget(self.cache_ttl); cache_row.addWidget(self.cache_stats, 1); cache_row.addWidget(clear)
        self.enrich_legal = QCheckBox("Interroger le registre officiel pour les prospects retenus")
        self.enrich_legal.setChecked(settings.enrich_legal)
        self.enrich_legal.setToolTip("France : API publique gratuite (SIREN, SIRET, forme juridique, NAF, dirigeants…).\n"
                                     "Autres pays : lien de recherche pré-rempli vers le registre.")
        form2.addRow(section_label("Cache"), self.use_cache)
        form2.addRow(section_label("Validité du cache"), cache_row)
        form2.addRow(section_label("Registre officiel"), self.enrich_legal)
        lay.addWidget(card2)
        self._refresh_cache_stats()

        help_ = QLabel(
            "• Sans clé Google, la recherche d'entreprises utilise OpenStreetMap (gratuit, couverture variable).<br>"
            "• Sans clé SerpAPI, la visibilité web est estimée via DuckDuckGo (moins précis).<br>"
            "<a style='color:#3ec6ff' href='https://console.cloud.google.com/apis/library/places-backend.googleapis.com'>Obtenir une clé Google Places</a> · "
            "<a style='color:#3ec6ff' href='https://serpapi.com/manage-api-key'>Obtenir une clé SerpAPI</a>")
        help_.setObjectName("Hint"); help_.setOpenExternalLinks(True); help_.setWordWrap(True)
        lay.addWidget(help_)

        btns = QHBoxLayout(); btns.addStretch()
        cancel = QPushButton("Annuler"); cancel.setObjectName("Ghost"); cancel.clicked.connect(self.reject)
        save = QPushButton("Enregistrer"); save.setObjectName("Primary"); save.clicked.connect(self._save)
        btns.addWidget(cancel); btns.addWidget(save)
        lay.addLayout(btns)

    def _refresh_cache_stats(self) -> None:
        try:
            from prospexia.core.cache import ResultCache
            c = ResultCache(ttl_days=self.settings.cache_ttl_days)
            c.purge_expired()
            st = c.stats(); c.close()
            self.cache_stats.setText(f"{st['analyses']} analyse(s) · {st['queries']} requête(s) en cache")
        except Exception:  # noqa: BLE001
            self.cache_stats.setText("")

    def _clear_cache(self) -> None:
        if QMessageBox.question(self, "Vider le cache",
                                "Supprimer toutes les analyses et recherches en cache ?\n"
                                "Les prochaines recherches reconsommeront des crédits API.") != QMessageBox.StandardButton.Yes:
            return
        from prospexia.core.cache import ResultCache
        c = ResultCache(); c.clear(); c.close()
        self._refresh_cache_stats()

    def _browse(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "Dossier d'export", self.export_dir.text())
        if d:
            self.export_dir.setText(d)

    def _save(self) -> None:
        s = self.settings
        s.google_places_api_key = self.google.text().strip()
        s.serpapi_api_key = self.serp.text().strip()
        s.concurrency = self.concurrency.value()
        s.request_timeout = float(self.timeout.value())
        s.export_dir = self.export_dir.text().strip() or s.export_dir
        s.use_cache = self.use_cache.isChecked()
        s.cache_ttl_days = self.cache_ttl.value()
        s.enrich_legal = self.enrich_legal.isChecked()
        s.save()
        self.accept()


class ProspectDialog(QDialog):
    def __init__(self, p: Prospect, parent=None):
        super().__init__(parent)
        self.setWindowTitle(p.company.name)
        self.setMinimumWidth(620)
        lay = QVBoxLayout(self); lay.setSpacing(12)

        head = QHBoxLayout()
        name = QLabel(p.company.name); name.setObjectName("PageTitle"); name.setWordWrap(True)
        head.addWidget(name, 1)
        head.addWidget(Badge(p.verdict.label, theme.VERDICT_COLORS[p.verdict.value]))
        head.addWidget(Badge(p.website.status.label, theme.STATUS_COLORS[p.website.status.value]))
        lay.addLayout(head)

        sub = QLabel(f"{p.company.sector} · {p.company.city or '—'} · source {p.company.source}")
        sub.setObjectName("PageSub"); lay.addWidget(sub)

        card = QFrame(); card.setObjectName("Card")
        g = QGridLayout(card); g.setContentsMargins(16, 14, 16, 14); g.setVerticalSpacing(8)
        rows = [
            ("Adresse", p.company.address or "—"),
            ("Téléphone", p.company.phone or "—"),
            ("Site web", p.company.website or "Aucun"),
            ("Score présence", f"{p.score} / 100  (0 = invisible)"),
            ("Opportunité", p.opportunity),
            ("Réseaux sociaux", ", ".join(f"{k}" for k in p.presence.socials) or "Aucun trouvé"),
            ("Résultats web", f"{p.presence.search_hits} ({p.presence.search_engine or 'n/a'})"),
            ("Avis Google", f"{p.company.reviews_count}" + (f" · note {p.company.rating}" if p.company.rating else "")),
        ]
        for i, (k, v) in enumerate(rows):
            kl = QLabel(k); kl.setObjectName("StatLabel")
            vl = QLabel(v); vl.setWordWrap(True); vl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            g.addWidget(kl, i, 0, Qt.AlignmentFlag.AlignTop); g.addWidget(vl, i, 1)
        g.setColumnStretch(1, 1)
        lay.addWidget(card)

        lg = p.legal
        if lg and lg.matched:
            lay.addWidget(section_label(f"Registre officiel — {lg.registry}"))
            lcard = QFrame(); lcard.setObjectName("Card")
            lg_grid = QGridLayout(lcard); lg_grid.setContentsMargins(16, 12, 16, 12); lg_grid.setVerticalSpacing(6)
            lrows = [
                (lg.identifier_label or "Identifiant", lg.identifier),
                (lg.secondary_label or "Identifiant 2", lg.secondary_id),
                ("Dénomination", lg.legal_name), ("Forme juridique", lg.legal_form),
                ("Activité", f"{lg.activity_code} {lg.activity_label}".strip()),
                ("Création", lg.creation_date), ("Effectif", lg.headcount), ("État", lg.status),
                ("Siège", lg.address), ("Dirigeants", "\n".join(lg.managers)), ("N° TVA", lg.vat_number),
                ("Confiance", f"{int(lg.confidence * 100)} %"),
            ]
            r = 0
            for k, v in lrows:
                if not v:
                    continue
                kl = QLabel(k); kl.setObjectName("StatLabel")
                vl = QLabel(v); vl.setWordWrap(True); vl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                lg_grid.addWidget(kl, r, 0, Qt.AlignmentFlag.AlignTop); lg_grid.addWidget(vl, r, 1); r += 1
            lg_grid.setColumnStretch(1, 1)
            lay.addWidget(lcard)
        elif lg:
            lay.addWidget(section_label("Registre officiel"))
            nl = QLabel(f"Aucune fiche appariée automatiquement ({lg.registry}). "
                        f"<a style='color:#3ec6ff' href='{lg.source_url}'>Rechercher manuellement</a>")
            nl.setOpenExternalLinks(True); nl.setWordWrap(True)
            lay.addWidget(nl)

        lay.addWidget(section_label("Diagnostic"))
        diag = QLabel("\n".join("• " + r for r in p.reasons) or "—"); diag.setWordWrap(True)
        lay.addWidget(diag)
        if p.website.issues:
            lay.addWidget(section_label("Problèmes du site"))
            iss = QLabel("\n".join("• " + r for r in p.website.issues)); iss.setWordWrap(True)
            lay.addWidget(iss)

        btns = QHBoxLayout(); btns.addStretch()
        if p.company.maps_url:
            b = QPushButton("🗺  Ouvrir la fiche"); b.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(p.company.maps_url)))
            btns.addWidget(b)
        if p.legal and p.legal.matched and p.legal.source_url:
            b = QPushButton("🏛  Fiche registre"); b.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(p.legal.source_url)))
            btns.addWidget(b)
        if p.company.website:
            b = QPushButton("🌐  Ouvrir le site"); b.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(p.website.final_url or p.company.website)))
            btns.addWidget(b)
        for soc, url in p.presence.socials.items():
            b = QPushButton(soc.capitalize()); b.setObjectName("Ghost")
            b.clicked.connect(lambda _=False, u=url: QDesktopServices.openUrl(QUrl(u)))
            btns.addWidget(b)
        close = QPushButton("Fermer"); close.setObjectName("Primary"); close.clicked.connect(self.accept)
        btns.addWidget(close)
        lay.addLayout(btns)
