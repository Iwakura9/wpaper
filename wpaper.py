from textual.app import App
from ui.screens.home import HomeScreen


class WpaperApp(App):
    TITLE = "wpaper"

    SCREENS = {
        "home": HomeScreen
    }

    def on_mount(self) -> None:
        self.push_screen("home")

if __name__ == "__main__":
    app = WpaperApp()
    app.run()
