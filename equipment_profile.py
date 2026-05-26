import calendar
from datetime import datetime
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp, sp
from database import load_data, save_data


BG = (0.10, 0.14, 0.21, 1)
PANEL = (0.16, 0.22, 0.33, 1)
PRIMARY = (0.0, 0.45, 0.90, 1)
SUCCESS = (0.04, 0.70, 0.40, 1)
DANGER = (0.80, 0.18, 0.18, 1)
DANGER_2 = (0.90, 0.05, 0.05, 1)
MUTED = (0.25, 0.28, 0.35, 1)
TEXT = (0.9, 0.95, 1, 1)
SUBTEXT = (0.8, 0.8, 0.8, 1)


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


def make_popup_message(text, title, size_hint=(0.90, 0.42)):
    pop_layout = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(14))
    lbl = Label(text=text, markup=True, halign='center', valign='middle', font_size=sp(16), color=TEXT)
    lbl.bind(size=lbl.setter('text_size'))
    pop_layout.add_widget(lbl)
    popup = Popup(title=title, content=pop_layout, size_hint=size_hint)
    return popup, pop_layout


class ViewEquipmentScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(*BG)
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_rect, pos=self._update_rect)

        self.layout = BoxLayout(orientation='vertical', padding=dp(6), spacing=dp(6))
        self.scroll = ScrollView()
        self.list_layout = BoxLayout(orientation='vertical', spacing=dp(8), size_hint_y=None)
        self.list_layout.bind(minimum_height=self.list_layout.setter('height'))
        self.scroll.add_widget(self.list_layout)

        title = Label(text="Equipment Inventories", font_size=sp(17), bold=True, size_hint_y=None, height=dp(30), color=TEXT)
        title.bind(size=title.setter('text_size'))
        self.layout.add_widget(title)
        self.layout.add_widget(self.scroll)

        btn_back = make_button("Back to Menu", MUTED, 46, 15)
        btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'main_menu'))
        self.layout.add_widget(btn_back)
        self.add_widget(self.layout)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def update_list(self):
        self.list_layout.clear_widgets()
        data = load_data()

        if not data["equipments"]:
            self.list_layout.add_widget(Label(
                text="No equipment profiles registered yet.",
                size_hint_y=None,
                height=dp(60),
                color=SUBTEXT,
                font_size=sp(16)
            ))
            return

        for equip_id, info in data["equipments"].items():
            row = BoxLayout(size_hint_y=None, height=dp(78), spacing=dp(8))

            btn_open = Button(
                text=f"{equip_id}\n{info.get('brand', '')} {info.get('model', '')} ({info.get('type', '')})",
                size_hint_x=0.72,
                background_color=PANEL,
                background_normal='',
                halign='left',
                valign='middle',
                font_size=sp(15),
                color=(1, 1, 1, 1)
            )
            btn_open.bind(size=btn_open.setter('text_size'))
            btn_open.bind(on_press=lambda x, eid=equip_id: self.open_profile(eid))
            row.add_widget(btn_open)

            btn_delete = make_button("Delete", DANGER, 78, 15, True)
            btn_delete.size_hint_x = 0.28
            btn_delete.bind(on_press=lambda x, eid=equip_id: self.confirm_delete_equipment_popup(eid))
            row.add_widget(btn_delete)

            self.list_layout.add_widget(row)

    def open_profile(self, equip_id):
        self.manager.get_screen('profile_detail').current_view_date = datetime.now()
        self.manager.get_screen('profile_detail').setup_profile(equip_id)
        self.manager.current = 'profile_detail'

    def confirm_delete_equipment_popup(self, equip_id):
        data = load_data()
        log_count = sum(1 for log in data["logs"] if log.get("equip_id") == equip_id)

        popup, pop_layout = make_popup_message(
            f"Delete equipment profile:\n[b]{equip_id}[/b]\n\nThis will also delete {log_count} related log(s).",
            "Confirm Equipment Delete",
            size_hint=(0.90, 0.40)
        )

        btn_box = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(56))
        btn_yes = make_button("Delete Equipment", DANGER, 56, 16, True)
        btn_no = make_button("Cancel", MUTED, 56, 16)
        btn_box.add_widget(btn_yes)
        btn_box.add_widget(btn_no)
        pop_layout.add_widget(btn_box)

        def execute_delete(instance):
            data = load_data()
            data["equipments"].pop(equip_id, None)
            data["logs"] = [log for log in data["logs"] if log.get("equip_id") != equip_id]
            save_data(data)
            popup.dismiss()
            self.update_list()

        btn_yes.bind(on_press=execute_delete)
        btn_no.bind(on_press=popup.dismiss)
        popup.open()


class ProfileDetailScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_view_date = datetime.now()
        self.active_equip_id = None

        with self.canvas.before:
            Color(*BG)
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_rect, pos=self._update_rect)

        self.root_box = BoxLayout(orientation='vertical', padding=dp(6), spacing=dp(6))
        self.scroll = ScrollView()
        self.layout = BoxLayout(orientation='vertical', spacing=dp(8), size_hint_y=None)
        self.layout.bind(minimum_height=self.layout.setter('height'))
        self.scroll.add_widget(self.layout)
        self.root_box.add_widget(self.scroll)

        self.btn_back = make_button("Back to Inventories", MUTED, 46, 15)
        self.btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'view_equip'))
        self.root_box.add_widget(self.btn_back)
        self.add_widget(self.root_box)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def setup_profile(self, equip_id):
        self.active_equip_id = equip_id
        self.layout.clear_widgets()
        data = load_data()

        if equip_id not in data["equipments"]:
            self.manager.get_screen('view_equip').update_list()
            self.manager.current = 'view_equip'
            return

        info = data["equipments"][equip_id]

        title = Label(text=f"Equipment: {equip_id}", font_size=sp(17), bold=True, size_hint_y=None, height=dp(28), color=TEXT)
        title.bind(size=title.setter('text_size'))
        self.layout.add_widget(title)

        info_box = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(132), spacing=dp(6), padding=(dp(8), dp(6)))
        lbl = Label(
            text=(
                f"[b][color=00b3ff]Type:[/color][/b] {info.get('type', '')}\n"
                f"[b][color=00b3ff]Brand / Model:[/color][/b] {info.get('brand', '')} {info.get('model', '')}\n"
                f"[b][color=00b3ff]Serial:[/color][/b] {info.get('serial', '') or '-'}\n"
                f"[b][color=00b3ff]Ownership:[/color][/b] {info.get('ownership', '')}\n"
                f"[b][color=00b3ff]Supplier:[/color][/b] {info.get('supplier', '')}"
            ),
            markup=True,
            halign='left',
            valign='middle',
            font_size=sp(15),
            color=TEXT
        )
        lbl.bind(size=lbl.setter('text_size'))
        info_box.add_widget(lbl)

        action_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(54), spacing=dp(8))
        btn_wipe = make_button("Wipe History", DANGER, 54, 15, True)
        btn_wipe.bind(on_press=lambda x: self.confirm_wipe_popup(equip_id))
        action_box.add_widget(btn_wipe)

        btn_delete = make_button("Delete Device", DANGER_2, 54, 15, True)
        btn_delete.bind(on_press=lambda x: self.confirm_delete_equipment_popup(equip_id))
        action_box.add_widget(btn_delete)
        info_box.add_widget(action_box)
        self.layout.add_widget(info_box)

        key_lbl = Label(
            text="[color=04b368]■ Monthly Contract[/color]     [color=0077ff]■ Daily Basis[/color]",
            markup=True,
            size_hint_y=None,
            height=dp(28),
            font_size=sp(14),
            bold=True,
            color=TEXT
        )
        key_lbl.bind(size=key_lbl.setter('text_size'))
        self.layout.add_widget(key_lbl)

        nav_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(54), spacing=dp(8))
        btn_prev = make_button("< Prev", PANEL, 54, 15, True)
        btn_prev.size_hint_x = 0.28
        btn_prev.bind(on_press=self.go_prev_month)

        self.lbl_month_title = Label(text=self.current_view_date.strftime('%B %Y'), font_size=sp(18), bold=True, color=TEXT, size_hint_x=0.44)
        self.lbl_month_title.bind(size=self.lbl_month_title.setter('text_size'))

        btn_next = make_button("Next >", PANEL, 54, 15, True)
        btn_next.size_hint_x = 0.28
        btn_next.bind(on_press=self.go_next_month)

        nav_box.add_widget(btn_prev)
        nav_box.add_widget(self.lbl_month_title)
        nav_box.add_widget(btn_next)
        self.layout.add_widget(nav_box)

        cal = calendar.monthcalendar(self.current_view_date.year, self.current_view_date.month)
        cell_h = dp(44)
        grid = GridLayout(cols=7, spacing=dp(3), size_hint_y=None, row_default_height=cell_h)
        grid.bind(minimum_height=grid.setter('height'))

        for day in ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su']:
            grid.add_widget(make_button(day, PANEL, 44, 13, True, disabled=True))

        for week in cal:
            for day in week:
                if day == 0:
                    grid.add_widget(Label(text="", size_hint_y=None, height=cell_h))
                else:
                    current_cell_date = datetime(self.current_view_date.year, self.current_view_date.month, day)
                    matched_log = None

                    for log in data["logs"]:
                        if log.get("equip_id") == equip_id:
                            try:
                                s_str = log.get("start_date", log.get("date"))
                                e_str = log.get("end_date", s_str)
                                start_dt = datetime.strptime(s_str, "%Y-%m-%d")
                                end_dt = datetime.strptime(e_str, "%Y-%m-%d")
                                if start_dt <= current_cell_date <= end_dt:
                                    matched_log = log
                                    break
                            except Exception:
                                continue

                    if matched_log:
                        bg_color = SUCCESS if matched_log.get("term") == "Monthly Contract" else PRIMARY
                        short_client = matched_log.get('client', '')[:4]
                        btn = Button(
                            text=f"[b]{day}[/b]\n{short_client}",
                            markup=True,
                            font_size=sp(12),
                            halign='center',
                            valign='middle',
                            background_color=bg_color,
                            background_normal='',
                            color=(1, 1, 1, 1)
                        )
                        btn.bind(size=btn.setter('text_size'))
                        btn.bind(on_press=lambda x, lg=matched_log: self.show_log_popup(lg))
                    else:
                        btn = Button(
                            text=str(day),
                            font_size=sp(14),
                            background_color=PANEL,
                            background_normal='',
                            color=SUBTEXT
                        )
                    grid.add_widget(btn)

        self.layout.add_widget(grid)
        self.layout.add_widget(Label(size_hint_y=None, height=dp(8)))

    def go_prev_month(self, instance):
        m = self.current_view_date.month - 1
        y = self.current_view_date.year
        if m == 0:
            m = 12
            y -= 1
        self.current_view_date = datetime(y, m, 1)
        self.setup_profile(self.active_equip_id)

    def go_next_month(self, instance):
        m = self.current_view_date.month + 1
        y = self.current_view_date.year
        if m == 13:
            m = 1
            y += 1
        self.current_view_date = datetime(y, m, 1)
        self.setup_profile(self.active_equip_id)

    def confirm_wipe_popup(self, equip_id):
        popup, pop_layout = make_popup_message(
            f"Delete all historical logs for\n[b]{equip_id}[/b] permanently?",
            "Confirm Action Data Reset",
            size_hint=(0.90, 0.36)
        )

        btn_box = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(56))
        btn_yes = make_button("Wipe Everything", DANGER, 56, 16, True)
        btn_no = make_button("Cancel", MUTED, 56, 16)
        btn_box.add_widget(btn_yes)
        btn_box.add_widget(btn_no)
        pop_layout.add_widget(btn_box)

        def execute_wipe(instance):
            data = load_data()
            data["logs"] = [log for log in data["logs"] if log.get("equip_id") != equip_id]
            save_data(data)
            popup.dismiss()
            self.setup_profile(equip_id)

        btn_yes.bind(on_press=execute_wipe)
        btn_no.bind(on_press=popup.dismiss)
        popup.open()

    def confirm_delete_equipment_popup(self, equip_id):
        data = load_data()
        log_count = sum(1 for log in data["logs"] if log.get("equip_id") == equip_id)

        popup, pop_layout = make_popup_message(
            f"Delete equipment profile:\n[b]{equip_id}[/b]\n\nThis will also delete {log_count} related log(s).",
            "Confirm Equipment Delete",
            size_hint=(0.90, 0.40)
        )

        btn_box = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(56))
        btn_yes = make_button("Delete Equipment", DANGER, 56, 16, True)
        btn_no = make_button("Cancel", MUTED, 56, 16)
        btn_box.add_widget(btn_yes)
        btn_box.add_widget(btn_no)
        pop_layout.add_widget(btn_box)

        def execute_delete(instance):
            data = load_data()
            data["equipments"].pop(equip_id, None)
            data["logs"] = [log for log in data["logs"] if log.get("equip_id") != equip_id]
            save_data(data)
            popup.dismiss()
            self.manager.get_screen('view_equip').update_list()
            self.manager.current = 'view_equip'

        btn_yes.bind(on_press=execute_delete)
        btn_no.bind(on_press=popup.dismiss)
        popup.open()

    def show_log_popup(self, log):
        start_str = log.get("start_date", log.get("date", ""))
        end_str = log.get("end_date", start_str)
        term = log.get("term", "")
        client = log.get("client", "")

        popup, pop_layout = make_popup_message(
            (f"[b]Client:[/b] {client}\n"
             f"[b]Term:[/b] {term}\n"
             f"[b]From:[/b] {start_str}\n"
             f"[b]To:[/b] {end_str}"),
            "Allocation Log Details",
            size_hint=(0.90, 0.46)
        )

        btn_box = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(56))
        btn_delete = make_button("Delete This Log", DANGER, 56, 16, True)
        btn_close = make_button("Close", MUTED, 56, 16)
        btn_box.add_widget(btn_delete)
        btn_box.add_widget(btn_close)
        pop_layout.add_widget(btn_box)

        def execute_delete_log(instance):
            data = load_data()
            deleted = False
            new_logs = []

            for item in data["logs"]:
                item_start = item.get("start_date", item.get("date", ""))
                item_end = item.get("end_date", item_start)

                same_log = (
                    item.get("equip_id") == log.get("equip_id") and
                    item.get("client") == client and
                    item.get("term") == term and
                    item_start == start_str and
                    item_end == end_str
                )

                if same_log and not deleted:
                    deleted = True
                    continue

                new_logs.append(item)

            data["logs"] = new_logs
            save_data(data)
            popup.dismiss()
            self.setup_profile(self.active_equip_id)

        btn_delete.bind(on_press=execute_delete_log)
        btn_close.bind(on_press=popup.dismiss)
        popup.open()
