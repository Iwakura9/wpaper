from textual.app import App
from db.schema import initialize_db
from ui.screens.home import HomeScreen
from ui.screens.dashboard import DashboardScreen


class WpaperApp(App):
    TITLE = "wpaper"

    SCREENS = {
        "home": HomeScreen,
        "dashboard": DashboardScreen,
    }

    def on_mount(self) -> None:
        initialize_db()
        self.push_screen("home")

if __name__ == "__main__":
    app = WpaperApp()
    app.run()
