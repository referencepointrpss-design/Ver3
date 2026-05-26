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


def make_input(hint, text=''):
    return TextInput(
        hint_text=hint,
        text=text,
        multiline=False,
        size_hint_y=None,
        height=dp(54),
        font_size=sp(16),
        background_color=PANEL,
        foreground_color=(1, 1, 1, 1),
        hint_text_color=(0.65, 0.65, 0.65, 1),
        padding=[dp(12), dp(14), dp(12), dp(14)]
    )


class AddEquipmentScreen(Screen):
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

    def _make_option_dropdown(self, items, on_select_callback):
        dd = DropDown()
        for opt in items:
            b = make_button(opt, PANEL_2, 52, 16)
            b.bind(on_release=lambda btn: dd.select(btn.text))
            dd.add_widget(b)
        dd.bind(on_select=lambda instance, x: on_select_callback(x))
        return dd

    def on_enter(self):
        self.layout.clear_widgets()

        title = Label(text="Create Equipment Profile", font_size=sp(17), bold=True, size_hint_y=None, height=dp(30), color=TEXT)
        title.bind(size=title.setter('text_size'))
        self.layout.add_widget(title)

        self.txt_id = make_input("Equipment ID (e.g., TS-01)")
        self.layout.add_widget(self.txt_id)

        self.btn_type = make_button('Select Device Type', PANEL, 54, 16)
        self.dropdown_type = self._make_option_dropdown(
            ['GNSS device', 'Total Station', 'Level', 'Drone', 'Laser Scanner'],
            lambda x: setattr(self.btn_type, 'text', x)
        )
        self.btn_type.bind(on_release=self.dropdown_type.open)
        self.layout.add_widget(self.btn_type)

        self.txt_brand = make_input("Brand (e.g., Leica, Sokkia)")
        self.layout.add_widget(self.txt_brand)

        self.txt_model = make_input("Model (e.g., IM 105)")
        self.layout.add_widget(self.txt_model)

        self.txt_sn = make_input("Serial Number (Required for Total Station)")
        self.layout.add_widget(self.txt_sn)

        self.btn_owner = make_button('Owned by me', PANEL, 54, 16)
        self.dropdown_owner = self._make_option_dropdown(
            ['Owned by me', 'Rented from someone else'],
            self.handle_ownership_change
        )
        self.btn_owner.bind(on_release=self.dropdown_owner.open)
        self.layout.add_widget(self.btn_owner)

        data = load_data()
        self.btn_supplier = make_button('My Office', PANEL, 54, 16)
        self.btn_supplier.disabled = True
        self.btn_supplier.color = (0.65, 0.65, 0.65, 1)
        self.dropdown_supplier = self._make_option_dropdown(
            list(data["device_owners"].keys()),
            lambda x: setattr(self.btn_supplier, 'text', x)
        )
        self.btn_supplier.bind(on_release=self.dropdown_supplier.open)
        self.layout.add_widget(self.btn_supplier)

        self.lbl_error = Label(text="", color=(1, 0.3, 0.3, 1), font_size=sp(15), size_hint_y=None, height=dp(42))
        self.lbl_error.bind(size=self.lbl_error.setter('text_size'))
        self.layout.add_widget(self.lbl_error)

        btn_save = make_button("Save Profile Entry", SUCCESS, 50, 16, True)
        btn_save.bind(on_press=self.save_equipment)
        self.layout.add_widget(btn_save)

        btn_back = make_button("Cancel", MUTED, 46, 15)
        btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main_menu'))
        self.layout.add_widget(btn_back)

        self.layout.add_widget(Label(size_hint_y=None, height=dp(4)))

    def handle_ownership_change(self, target_status):
        self.btn_owner.text = target_status
        if target_status == 'Owned by me':
            self.btn_supplier.text = 'My Office'
            self.btn_supplier.disabled = True
            self.btn_supplier.color = (0.65, 0.65, 0.65, 1)
        else:
            self.btn_supplier.text = 'Select Device Owner'
            self.btn_supplier.disabled = False
            self.btn_supplier.color = (1, 1, 1, 1)

    def save_equipment(self, instance):
        eq_id = self.txt_id.text.strip()
        data = load_data()

        if not eq_id:
            self.lbl_error.text = "Error: Equipment ID is required."
            return

        if self.btn_type.text == 'Select Device Type':
            self.lbl_error.text = "Error: Device type is required."
            return

        if eq_id in data["equipments"]:
            self.lbl_error.text = "Error: This Equipment ID already exists."
            return

        serial_val = self.txt_sn.text.strip()
        if self.btn_type.text == 'Total Station' and not serial_val:
            self.lbl_error.text = "Error: Serial number is required for Total Station."
            return

        supplier_val = 'My Office'
        if self.btn_owner.text == 'Rented from someone else':
            supplier_val = self.btn_supplier.text
            if supplier_val == 'Select Device Owner' or supplier_val not in data["device_owners"]:
                self.lbl_error.text = "Error: Select the real device owner/supplier first."
                return

        data["equipments"][eq_id] = {
            "type": self.btn_type.text,
            "brand": self.txt_brand.text.strip(),
            "model": self.txt_model.text.strip(),
            "serial": serial_val,
            "ownership": self.btn_owner.text,
            "supplier": supplier_val
        }
        save_data(data)
        self.manager.current = 'main_menu'
