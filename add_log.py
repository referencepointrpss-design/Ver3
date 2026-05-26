from datetime import datetime
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.dropdown import DropDown
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp, sp
from database import load_data, save_data


BG = (0.10, 0.14, 0.21, 1)
PANEL = (0.16, 0.22, 0.33, 1)
PANEL_2 = (0.2, 0.26, 0.38, 1)
SUCCESS = (0.04, 0.70, 0.40, 1)
MUTED = (0.25, 0.28, 0.35, 1)
TEXT = (0.9, 0.95, 1, 1)


def make_button(text, bg, height=54, font_size=16, bold=False, **kwargs):
    return Button(
        text=text,
        size_hint_y=None,
        height=dp(height),
        background_color=bg,
        background_normal='',
        font_size=sp(font_size),
        bold=bold,
        color=(1, 1, 1, 1),
        **kwargs
    )


def make_input(hint, text='', disabled=False, color=(1, 1, 1, 1)):
    return TextInput(
        hint_text=hint,
        text=text,
        multiline=False,
        size_hint_y=None,
        height=dp(54),
        font_size=sp(16),
        background_color=PANEL,
        foreground_color=color,
        hint_text_color=(0.65, 0.65, 0.65, 1),
        disabled=disabled,
        padding=[dp(12), dp(14), dp(12), dp(14)]
    )


class AddLogScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(*BG)
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_rect, pos=self._update_rect)

        self.root_box = BoxLayout(orientation='vertical', padding=dp(6), spacing=dp(6))
        self.scroll = ScrollView(size_hint=(1, 1))
        self.layout = BoxLayout(orientation='vertical', spacing=dp(6), size_hint_y=None)
        self.layout.bind(minimum_height=self.layout.setter('height'))
        self.scroll.add_widget(self.layout)
        self.root_box.add_widget(self.scroll)
        self.add_widget(self.root_box)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def on_enter(self):
        self.layout.clear_widgets()
        title = Label(text="Log Deployment Location", font_size=sp(17), bold=True, size_hint_y=None, height=dp(30), color=TEXT)
        title.bind(size=title.setter('text_size'))
        self.layout.add_widget(title)

        data = load_data()
        equip_list = list(data["equipments"].keys())

        self.btn_equip = make_button('Select Device ID', PANEL, 54, 16)
        self.dropdown_equip = DropDown()
        if not equip_list:
            self.dropdown_equip.add_widget(make_button('No Equipment Profiles Registered', PANEL_2, 52, 15, False, disabled=True))
        for opt in equip_list:
            b = make_button(opt, PANEL_2, 52, 16)
            b.bind(on_release=lambda btn: self.dropdown_equip.select(btn.text))
            self.dropdown_equip.add_widget(b)
        self.btn_equip.bind(on_release=self.dropdown_equip.open)
        self.dropdown_equip.bind(on_select=lambda instance, x: setattr(self.btn_equip, 'text', x))
        self.layout.add_widget(self.btn_equip)

        self.btn_term = make_button('Daily Basis', PANEL, 54, 16)
        self.dropdown_term = DropDown()
        for opt in ['Daily Basis', 'Monthly Contract']:
            b = make_button(opt, PANEL_2, 52, 16)
            b.bind(on_release=lambda btn: self.dropdown_term.select(btn.text))
            self.dropdown_term.add_widget(b)
        self.btn_term.bind(on_release=self.dropdown_term.open)
        self.dropdown_term.bind(on_select=lambda instance, x: self.toggle_term_state(x))
        self.layout.add_widget(self.btn_term)

        self.btn_client = make_button('Select "Rented To" Client', PANEL, 54, 16)
        self.dropdown_client = DropDown()
        if not data["rented_to_companies"].keys():
            self.dropdown_client.add_widget(make_button('No Clients Registered in Directory', PANEL_2, 52, 15, False, disabled=True))
        for opt in data["rented_to_companies"].keys():
            b = make_button(opt, PANEL_2, 52, 16)
            b.bind(on_release=lambda btn: self.dropdown_client.select(btn.text))
            self.dropdown_client.add_widget(b)
        self.btn_client.bind(on_release=self.dropdown_client.open)
        self.dropdown_client.bind(on_select=lambda instance, x: setattr(self.btn_client, 'text', x))
        self.layout.add_widget(self.btn_client)

        today = datetime.now().strftime("%Y-%m-%d")
        self.txt_start_date = make_input("Date (YYYY-MM-DD)", today)
        self.txt_start_date.bind(text=self.sync_daily_dates)
        self.layout.add_widget(self.txt_start_date)

        self.txt_end_date = make_input("End Date (YYYY-MM-DD)", today, disabled=True, color=(0.65, 0.65, 0.65, 1))
        self.layout.add_widget(self.txt_end_date)

        self.lbl_error = Label(text="", color=(1, 0.3, 0.3, 1), font_size=sp(15), size_hint_y=None, height=dp(42))
        self.lbl_error.bind(size=self.lbl_error.setter('text_size'))
        self.layout.add_widget(self.lbl_error)

        btn_save = make_button("Save Log Entry", SUCCESS, 50, 16, True)
        btn_save.bind(on_press=self.save_log)
        self.layout.add_widget(btn_save)

        btn_back = make_button("Back to Menu", MUTED, 46, 15)
        btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main_menu'))
        self.layout.add_widget(btn_back)

        self.layout.add_widget(Label(size_hint_y=None, height=dp(4)))

    def sync_daily_dates(self, instance, text):
        if self.btn_term.text == 'Daily Basis':
            self.txt_end_date.text = text

    def toggle_term_state(self, selected_term):
        self.btn_term.text = selected_term
        if selected_term == "Daily Basis":
            self.txt_start_date.hint_text = "Date (YYYY-MM-DD)"
            self.txt_end_date.text = self.txt_start_date.text
            self.txt_end_date.disabled = True
            self.txt_end_date.foreground_color = (0.65, 0.65, 0.65, 1)
        else:
            self.txt_start_date.hint_text = "Contract Start Date (YYYY-MM-DD)"
            self.txt_end_date.disabled = False
            self.txt_end_date.foreground_color = (1, 1, 1, 1)

    def save_log(self, instance):
        if self.btn_equip.text == 'Select Device ID' or self.btn_client.text == 'Select "Rented To" Client':
            self.lbl_error.text = "Error: Dropdowns must be completely specified."
            return

        start_str = self.txt_start_date.text.strip()
        end_str = self.txt_end_date.text.strip()

        try:
            new_start = datetime.strptime(start_str, "%Y-%m-%d")
            new_end = datetime.strptime(end_str, "%Y-%m-%d")
            if new_start > new_end:
                self.lbl_error.text = "Error: Start Date cannot follow End Date."
                return
        except ValueError:
            self.lbl_error.text = "Error: Input must use YYYY-MM-DD syntax."
            return

        data = load_data()

        if self.btn_equip.text not in data["equipments"]:
            self.lbl_error.text = "Error: Selected equipment no longer exists."
            return

        if self.btn_client.text not in data["rented_to_companies"]:
            self.lbl_error.text = "Error: Selected client no longer exists."
            return

        for log in data["logs"]:
            if log.get("equip_id") == self.btn_equip.text:
                try:
                    existing_start = datetime.strptime(log.get("start_date", log.get("date")), "%Y-%m-%d")
                    existing_end = datetime.strptime(log.get("end_date", log.get("date")), "%Y-%m-%d")
                    if not (new_end < existing_start or new_start > existing_end):
                        self.lbl_error.text = f"Conflict: Already at {log.get('client', 'another client')}"
                        return
                except Exception:
                    continue

        data["logs"].append({
            "equip_id": self.btn_equip.text,
            "client": self.btn_client.text,
            "start_date": start_str,
            "end_date": end_str,
            "term": self.btn_term.text
        })
        save_data(data)
        self.manager.current = 'main_menu'
