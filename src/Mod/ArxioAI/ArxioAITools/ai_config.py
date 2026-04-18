# SPDX-License-Identifier: LGPL-2.1-or-later
"""Qt dialog for configuring the Arxio AI LLM provider + API key."""

import FreeCAD

from ArxioAITools import ai


def open_dialog():
    """Open the config dialog, persist the result. Returns True on save."""
    try:
        from PySide import QtWidgets
    except ImportError:  # pragma: no cover
        FreeCAD.Console.PrintError(
            "Arxio AI: Qt indisponible, impossible d'afficher la configuration.\n"
        )
        return False

    cfg = ai.get_config()

    dlg = QtWidgets.QDialog()
    dlg.setWindowTitle("Arxio AI — Configuration de l'intelligence artificielle")
    dlg.setMinimumWidth(480)
    layout = QtWidgets.QVBoxLayout(dlg)

    info = QtWidgets.QLabel(
        "Configurez le fournisseur LLM utilisé par les commandes IA.\n"
        "La clé est stockée uniquement dans le paramètre local FreeCAD."
    )
    info.setWordWrap(True)
    layout.addWidget(info)

    form = QtWidgets.QFormLayout()

    provider = QtWidgets.QComboBox()
    provider.addItems(["anthropic", "openai"])
    provider.setCurrentText(cfg["provider"])

    base_url = QtWidgets.QLineEdit(cfg["base_url"])
    base_url.setPlaceholderText("https://api.anthropic.com/v1")

    model = QtWidgets.QLineEdit(cfg["model"])
    model.setPlaceholderText("claude-sonnet-4-5")

    api_key = QtWidgets.QLineEdit(cfg["api_key"])
    api_key.setEchoMode(QtWidgets.QLineEdit.Password)
    api_key.setPlaceholderText("sk-ant-… ou sk-…")

    show_key = QtWidgets.QCheckBox("Afficher la clé")

    def _toggle_echo(state):
        api_key.setEchoMode(
            QtWidgets.QLineEdit.Normal if state else QtWidgets.QLineEdit.Password
        )

    show_key.stateChanged.connect(_toggle_echo)

    max_tokens = QtWidgets.QSpinBox()
    max_tokens.setRange(256, 32000)
    max_tokens.setValue(cfg["max_tokens"])

    timeout = QtWidgets.QSpinBox()
    timeout.setRange(10, 600)
    timeout.setValue(cfg["timeout"])
    timeout.setSuffix(" s")

    form.addRow("Fournisseur", provider)
    form.addRow("URL de base", base_url)
    form.addRow("Modèle", model)
    form.addRow("Clé API", api_key)
    form.addRow("", show_key)
    form.addRow("max_tokens", max_tokens)
    form.addRow("Timeout", timeout)
    layout.addLayout(form)

    preset_row = QtWidgets.QHBoxLayout()
    preset_row.addWidget(QtWidgets.QLabel("Préréglages :"))

    def _preset_anthropic():
        provider.setCurrentText("anthropic")
        base_url.setText("https://api.anthropic.com/v1")
        model.setText("claude-sonnet-4-5")

    def _preset_openai():
        provider.setCurrentText("openai")
        base_url.setText("https://api.openai.com/v1")
        model.setText("gpt-4o-mini")

    def _preset_ollama():
        provider.setCurrentText("openai")
        base_url.setText("http://localhost:11434/v1")
        model.setText("llama3.1:8b")

    btn_a = QtWidgets.QPushButton("Anthropic")
    btn_a.clicked.connect(_preset_anthropic)
    btn_o = QtWidgets.QPushButton("OpenAI")
    btn_o.clicked.connect(_preset_openai)
    btn_l = QtWidgets.QPushButton("Ollama local")
    btn_l.clicked.connect(_preset_ollama)
    preset_row.addWidget(btn_a)
    preset_row.addWidget(btn_o)
    preset_row.addWidget(btn_l)
    preset_row.addStretch(1)
    layout.addLayout(preset_row)

    status = QtWidgets.QLabel("")
    status.setStyleSheet("color: #555;")
    layout.addWidget(status)

    def _test():
        tmp = {
            "provider": provider.currentText(),
            "base_url": base_url.text().strip(),
            "model": model.text().strip(),
            "api_key": api_key.text().strip(),
            "max_tokens": int(max_tokens.value()),
            "timeout": int(timeout.value()),
        }
        if not tmp["api_key"]:
            status.setText("⚠ Saisissez une clé API avant de tester.")
            return
        status.setText("… test en cours …")
        QtWidgets.QApplication.processEvents()
        try:
            reply = ai.ask(
                "Réponds uniquement par OK.",
                system="Tu es un service de santé. Réponds strictement 'OK'.",
                config=tmp,
            )
            status.setText(f"✅ Connexion OK — réponse : « {reply.strip()[:60]} »")
        except ai.LLMError as exc:
            status.setText(f"❌ {exc}")

    buttons = QtWidgets.QDialogButtonBox(
        QtWidgets.QDialogButtonBox.Save | QtWidgets.QDialogButtonBox.Cancel
    )
    test_btn = QtWidgets.QPushButton("Tester la connexion")
    test_btn.clicked.connect(_test)
    buttons.addButton(test_btn, QtWidgets.QDialogButtonBox.ActionRole)
    buttons.accepted.connect(dlg.accept)
    buttons.rejected.connect(dlg.reject)
    layout.addWidget(buttons)

    if dlg.exec_() != QtWidgets.QDialog.Accepted:
        return False

    ai.set_config(
        provider=provider.currentText(),
        base_url=base_url.text().strip(),
        model=model.text().strip(),
        api_key=api_key.text().strip(),
        max_tokens=int(max_tokens.value()),
        timeout=int(timeout.value()),
    )
    FreeCAD.Console.PrintMessage("Arxio AI — configuration enregistrée.\n")
    return True
