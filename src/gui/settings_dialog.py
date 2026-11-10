"""
Settings dialog for F1 Race Replay application.
Provides UI for configuring application settings like cache location.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from src.lib.settings import get_settings


class SettingsDialog(QDialog):
    """Dialog for configuring application settings."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = get_settings()
        self._setup_ui()
        self._load_current_settings()

    def _setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("Settings")
        self.setMinimumWidth(500)
        self.setModal(True)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Cache Settings Group
        cache_group = QGroupBox("Cache Settings")
        cache_layout = QFormLayout()
        cache_group.setLayout(cache_layout)

        # FastF1 Cache Location
        cache_path_layout = QHBoxLayout()
        self.cache_path_edit = QLineEdit()
        self.cache_path_edit.setPlaceholderText("Path to FastF1 cache folder...")
        self.cache_browse_btn = QPushButton("Browse...")
        self.cache_browse_btn.clicked.connect(self._browse_cache_location)
        cache_path_layout.addWidget(self.cache_path_edit)
        cache_path_layout.addWidget(self.cache_browse_btn)

        cache_layout.addRow("FastF1 Cache Location:", cache_path_layout)

        # Help text for cache
        cache_help = QLabel(
            "This is where FastF1 stores downloaded session data.\n"
            "Changing this location will not move existing cached data."
        )
        cache_help.setStyleSheet("color: gray; font-size: 11px;")
        cache_help.setWordWrap(True)
        cache_layout.addRow("", cache_help)

        # Computed Data Location
        computed_path_layout = QHBoxLayout()
        self.computed_path_edit = QLineEdit()
        self.computed_path_edit.setPlaceholderText("Path to computed data folder...")
        self.computed_browse_btn = QPushButton("Browse...")
        self.computed_browse_btn.clicked.connect(self._browse_computed_location)
        computed_path_layout.addWidget(self.computed_path_edit)
        computed_path_layout.addWidget(self.computed_browse_btn)

        cache_layout.addRow("Computed Data Location:", computed_path_layout)

        # Help text for computed data
        computed_help = QLabel(
            "This is where pre-processed telemetry data is stored.\n"
            "Helps speed up loading previously viewed sessions."
        )
        computed_help.setStyleSheet("color: gray; font-size: 11px;")
        computed_help.setWordWrap(True)
        cache_layout.addRow("", computed_help)

        layout.addWidget(cache_group)

        # API and provider health section. Credentials are read from .env and never
        # written into the desktop settings JSON file.
        api_group = QGroupBox("API & Data Providers")
        api_layout = QVBoxLayout()
        api_group.setLayout(api_layout)
        api_help = QLabel(
            "Jolpica and FastF1 work without API keys. OpenF1 historical data is free; "
            "authenticated live access requires an OpenF1 subscription and credentials "
            "in the project .env file. Secrets are never stored in settings.json."
        )
        api_help.setWordWrap(True)
        api_layout.addWidget(api_help)
        self.api_status_label = QLabel("Provider status: not tested")
        self.api_status_label.setWordWrap(True)
        api_layout.addWidget(self.api_status_label)
        api_buttons = QHBoxLayout()
        self.test_apis_btn = QPushButton("Test Providers")
        self.test_apis_btn.clicked.connect(self._test_api_providers)
        self.sync_season_btn = QPushButton("Sync Current Season")
        self.sync_season_btn.clicked.connect(self._sync_current_season)
        api_buttons.addWidget(self.test_apis_btn)
        api_buttons.addWidget(self.sync_season_btn)
        api_layout.addLayout(api_buttons)
        layout.addWidget(api_group)

        # Spacer
        layout.addStretch()

        # Reset to defaults button
        reset_layout = QHBoxLayout()
        self.reset_btn = QPushButton("Reset to Defaults")
        self.reset_btn.clicked.connect(self._reset_to_defaults)
        reset_layout.addWidget(self.reset_btn)
        reset_layout.addStretch()
        layout.addLayout(reset_layout)

        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self._save_settings)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)


    def _test_api_providers(self):
        try:
            from services.api_manager import ApiManager
            results = ApiManager().test_all()
            lines = [f"{name}: {'CONNECTED' if info.get('ok') else 'UNAVAILABLE'} — {info.get('message', '')}"
                     for name, info in results.items()]
            self.api_status_label.setText("\\n".join(lines))
        except Exception as exc:
            self.api_status_label.setText(f"Provider test failed: {exc}")

    def _sync_current_season(self):
        try:
            from datetime import datetime
            from services.synchronization_service import SynchronizationService
            year = datetime.now().year
            result = SynchronizationService().sync_jolpica_season(year)
            good = sum(1 for item in result.values() if item.get("ok"))
            self.api_status_label.setText(
                f"Jolpica {year} sync finished: {good}/{len(result)} datasets succeeded. "
                "See data/f1_data.sqlite3 and sync logs for stored records."
            )
        except Exception as exc:
            self.api_status_label.setText(f"Season sync failed: {exc}")

    def _load_current_settings(self):
        """Load current settings values into the UI."""
        self.cache_path_edit.setText(self.settings.cache_location)
        self.computed_path_edit.setText(self.settings.computed_data_location)

    def _browse_cache_location(self):
        """Open a folder browser for cache location."""
        current_path = self.cache_path_edit.text() or "."
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select FastF1 Cache Location",
            current_path,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
        )
        if folder:
            self.cache_path_edit.setText(folder)

    def _browse_computed_location(self):
        """Open a folder browser for computed data location."""
        current_path = self.computed_path_edit.text() or "."
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Computed Data Location",
            current_path,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks,
        )
        if folder:
            self.computed_path_edit.setText(folder)

    def _reset_to_defaults(self):
        """Reset settings to default values."""
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset all settings to their default values?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.settings.reset_to_defaults()
            self._load_current_settings()

    def _save_settings(self):
        """Save the settings and close the dialog."""
        # Validate paths (basic validation - just check they're not empty)
        cache_path = self.cache_path_edit.text().strip()
        computed_path = self.computed_path_edit.text().strip()

        if not cache_path:
            QMessageBox.warning(
                self,
                "Invalid Settings",
                "FastF1 cache location cannot be empty.",
            )
            return

        if not computed_path:
            QMessageBox.warning(
                self,
                "Invalid Settings",
                "Computed data location cannot be empty.",
            )
            return

        # Save settings
        self.settings.cache_location = cache_path
        self.settings.computed_data_location = computed_path
        self.settings.save()

        QMessageBox.information(
            self,
            "Settings Saved",
            "Settings have been saved successfully.\n\n"
            "Note: Cache location changes will take effect for new data downloads.",
        )

        self.accept()
