from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static


class ConfirmModal(ModalScreen):
    CSS_PATH = "confirm_modal.tcss"

    BINDINGS = [
        ("escape", "cancel"),
    ]

    def __init__(self, message: str):
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        yield Vertical(
            Static(self.message, id="confirm_message"),
            Horizontal(
                Button("Cancel", id="cancel_button"),
                Button("Confirm", variant="error", id="confirm_button"),
                id="modal_buttons",
            ),
            id="confirm_modal",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "confirm_button")

    def action_cancel(self) -> None:
        self.dismiss(False)
