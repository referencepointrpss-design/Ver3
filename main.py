__version__ = "0.1.1"

from kivy.app import App
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, NoTransition

Window.softinput_mode = 'below_target'

from menu import MainMenuScreen
from add_device import AddEquipmentScreen
from add_log import AddLogScreen
from equipment_profile import ViewEquipmentScreen, ProfileDetailScreen


class SurveyApp(App):
    def build(self):
        self.title = "Survey Office Manager"
        self.icon = 'icon.png'
        self.sm = ScreenManager(transition=NoTransition())
        self.sm.add_widget(MainMenuScreen(name='main_menu'))
        self.sm.add_widget(AddEquipmentScreen(name='add_equip'))
        self.sm.add_widget(AddLogScreen(name='add_log'))
        self.sm.add_widget(ViewEquipmentScreen(name='view_equip'))
        self.sm.add_widget(ProfileDetailScreen(name='profile_detail'))

        # Android hardware back button:
        # - Detail screen returns to list
        # - Other screens return to main menu
        # - Main menu consumes the key so accidental presses do not close the app
        Window.bind(on_keyboard=self._handle_keyboard)
        return self.sm

    def _handle_keyboard(self, window, key, scancode=None, codepoint=None, modifiers=None):
        if key != 27:  # Android back / ESC
            return False

        current = self.sm.current
        if current == 'profile_detail':
            self.sm.get_screen('view_equip').update_list()
            self.sm.current = 'view_equip'
        elif current in ('add_equip', 'add_log', 'view_equip'):
            self.sm.current = 'main_menu'
        else:
            # Stay on main menu instead of closing the app accidentally.
            pass
        return True

    def on_pause(self):
        return True


if __name__ == '__main__':
    SurveyApp().run()
