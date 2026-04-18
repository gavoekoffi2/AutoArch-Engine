# SPDX-License-Identifier: LGPL-2.1-or-later
"""Chat assistant dock widget.

A minimal, context-aware Qt chat that lets the architect ask the LLM
general questions or ask for guidance on the active document. The
conversation history is kept in-memory for the session; nothing is
written to disk.
"""

import FreeCAD

from ArxioAITools import ai
from ArxioAITools import estimate as aa_estimate


SYSTEM_PROMPT = """Tu es Arxio AI, un assistant conversationnel pour architectes
francophones utilisant FreeCAD. Tu connais le BIM, le dessin 2D/3D, les
principes constructifs, et les normes courantes (DTU, RE2020, accessibilité).

Règles :
- Réponds en français, clair, concis, concret.
- Quand on te donne le résumé du projet actif, tu peux le commenter,
  répondre à des questions sur ses quantités et suggérer des actions
  à réaliser dans le workbench « Arxio AI ».
- Si tu ne sais pas, dis-le.
- N'invente pas de commande FreeCAD. Les commandes disponibles dans
  Arxio AI sont : Initialiser le projet, Murs rapides, Toiture & dalle
  auto, Placer portes & fenêtres, Plans 2D automatiques, Métré & devis,
  Analyse solaire, Générer depuis brief, Revue IA.
"""


def _document_context():
    doc = FreeCAD.ActiveDocument
    if doc is None:
        return "Aucun document actif."
    try:
        report = aa_estimate.run(doc)
    except Exception:
        return f"Document actif: {doc.Label}. (Impossible de générer le quantitatif.)"
    q = report["quantities"]
    prices = report["prices"]
    return (
        f"Document actif: {doc.Label}, {len(doc.Objects)} objets.\n"
        f"Quantités: murs {q['wall_m3']:.2f} m³, dalles {q['slab_m3']:.2f} m³, "
        f"toiture {q['roof_m2']:.2f} m², {q['windows']} fenêtres, {q['doors']} portes.\n"
        f"Coût estimé: {report['total_cost']:.0f} {prices['currency']}."
    )


class ChatState:
    """Holds conversation history for the current session."""

    def __init__(self):
        self.history = []  # list[{"role": "...", "content": "..."}]

    def reset(self):
        self.history = []

    def append(self, role, content):
        self.history.append({"role": role, "content": content})

    def send(self, user_text, include_context=True):
        messages = list(self.history)
        if include_context:
            ctx = _document_context()
            messages.append(
                {
                    "role": "user",
                    "content": f"[CONTEXTE PROJET]\n{ctx}\n\n[QUESTION]\n{user_text}",
                }
            )
        else:
            messages.append({"role": "user", "content": user_text})
        reply = ai.chat(messages, system=SYSTEM_PROMPT)
        self.append("user", user_text)
        self.append("assistant", reply)
        return reply


_state = ChatState()


def open_dialog():
    """Open a modeless chat window bound to the session's history."""
    try:
        from PySide import QtCore, QtWidgets
    except ImportError:  # pragma: no cover
        FreeCAD.Console.PrintError(
            "Arxio AI: Qt indisponible, impossible d'ouvrir l'assistant.\n"
        )
        return None

    dlg = QtWidgets.QDialog()
    dlg.setWindowTitle("Arxio AI — Assistant IA")
    dlg.resize(680, 620)
    dlg.setWindowFlags(dlg.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)

    layout = QtWidgets.QVBoxLayout(dlg)

    header = QtWidgets.QLabel(
        "<b>Arxio AI</b> — assistant conversationnel. "
        "Le contexte du document actif est joint automatiquement."
    )
    header.setWordWrap(True)
    layout.addWidget(header)

    history = QtWidgets.QTextBrowser()
    history.setOpenExternalLinks(True)
    layout.addWidget(history, stretch=1)

    for msg in _state.history:
        _append_bubble(history, msg["role"], msg["content"])

    input_box = QtWidgets.QPlainTextEdit()
    input_box.setPlaceholderText(
        "Posez votre question à Arxio AI… (Ctrl+Entrée pour envoyer)"
    )
    input_box.setFixedHeight(110)
    layout.addWidget(input_box)

    row = QtWidgets.QHBoxLayout()
    include_ctx = QtWidgets.QCheckBox("Joindre le contexte du document")
    include_ctx.setChecked(True)
    row.addWidget(include_ctx)
    row.addStretch(1)
    send_btn = QtWidgets.QPushButton("Envoyer (Ctrl+⏎)")
    reset_btn = QtWidgets.QPushButton("Nouvelle conversation")
    row.addWidget(reset_btn)
    row.addWidget(send_btn)
    layout.addLayout(row)

    def _do_send():
        text = input_box.toPlainText().strip()
        if not text:
            return
        _append_bubble(history, "user", text)
        input_box.setPlainText("")
        QtWidgets.QApplication.processEvents()
        send_btn.setEnabled(False)
        try:
            reply = _state.send(text, include_context=include_ctx.isChecked())
            _append_bubble(history, "assistant", reply)
        except ai.LLMError as exc:
            _append_bubble(history, "system", f"Erreur IA : {exc}")
        finally:
            send_btn.setEnabled(True)
            sb = history.verticalScrollBar()
            sb.setValue(sb.maximum())

    def _reset():
        _state.reset()
        history.clear()

    send_btn.clicked.connect(_do_send)
    reset_btn.clicked.connect(_reset)

    # Ctrl+Enter shortcut
    shortcut = QtWidgets.QShortcut(QtCore.Qt.CTRL + QtCore.Qt.Key_Return, dlg)
    shortcut.activated.connect(_do_send)

    dlg.show()
    return dlg


def _append_bubble(browser, role, content):
    colors = {
        "user": "#1e5aa8",
        "assistant": "#0b6e3c",
        "system": "#b55015",
    }
    label = {"user": "Vous", "assistant": "Arxio AI", "system": "Système"}[role]
    color = colors.get(role, "#333")
    safe = (
        content.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br>")
    )
    browser.append(
        f'<p style="margin:6px 0;"><span style="color:{color};font-weight:600;">'
        f"{label} :</span><br>{safe}</p>"
    )
