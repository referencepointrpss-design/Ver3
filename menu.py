from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp, sp
from database import load_data, save_data
from export_tools import (
    backup_database_json,
    export_equipment_inventory_csv,
    export_allocation_logs_csv,
    export_summary_pdf,
    get_export_dir,
)

BG      = (0.10, 0.14, 0.21, 1)
PANEL   = (0.16, 0.22, 0.33, 1)
PANEL_2 = (0.20, 0.25, 0.35, 1)
PRIMARY = (0.0,  0.45, 0.90, 1)
SUCCESS = (0.04, 0.70, 0.40, 1)
DANGER  = (0.80, 0.18, 0.18, 1)
MUTED   = (0.30, 0.30, 0.30, 1)
TEXT    = (0.9,  0.95, 1.0,  1)
SUBTEXT = (0.8,  0.80, 0.80, 1)
ACCENT  = (0.63, 0.77, 0.94, 1)
STAT_BG = (0.12, 0.19, 0.29, 1)


def make_button(text, bg, height=56, font_size=16, bold=False):
    return Button(
        text=text,
        size_hint_y=None,
        height=dp(height),
        background_color=bg,
        background_normal='',
        font_size=sp(font_size),
        bold=bold,
        color=(1, 1, 1, 1),
        halign='center',
        valign='middle',
    )


class MainMenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Background
        with self.canvas.before:
            Color(*BG)
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_rect, pos=self._update_rect)

        # ── Root: anchored to top, shrinks to content ──────────────────
        layout = BoxLayout(
            orientation='vertical',
            padding=dp(8),
            spacing=dp(7),
            size_hint=(1, None),
            pos_hint={'x': 0, 'top': 1},
        )
        layout.bind(minimum_height=layout.setter('height'))

        # ① Slim header bar ────────────────────────────────────────────
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(32))
        lbl_title = Label(
            text='SURVEY OFFICE MANAGER',
            font_size=sp(14), bold=True,
            color=ACCENT,
            halign='left', valign='middle',
        )
        lbl_title.bind(size=lbl_title.setter('text_size'))
        lbl_ver = Label(
            text='v0.1.1',
            font_size=sp(11),
            color=(0.35, 0.45, 0.55, 1),
            halign='right', valign='middle',
            size_hint_x=0.22,
        )
        lbl_ver.bind(size=lbl_ver.setter('text_size'))
        header.add_widget(lbl_title)
        header.add_widget(lbl_ver)
        layout.add_widget(header)

        # ② Stats row ──────────────────────────────────────────────────
        stats_row = BoxLayout(
            orientation='horizontal',
            size_hint_y=None, height=dp(64),
            spacing=dp(7),
        )
        self.stat_d = self._make_stat_tile('-', 'DEVICES')
        self.stat_l = self._make_stat_tile('-', 'LOGS')
        self.stat_c = self._make_stat_tile('-', 'CLIENTS')
        for t in (self.stat_d, self.stat_l, self.stat_c):
            stats_row.add_widget(t)
        layout.add_widget(stats_row)

        # ③ Main buttons ───────────────────────────────────────────────
        btn_add = make_button('  \u2795  Add Equipment Profile', PANEL, 50, 15, True)
        btn_add.bind(on_press=lambda x: setattr(self.manager, 'current', 'add_equip'))
        layout.add_widget(btn_add)

        btn_log = make_button('  \U0001f4cb  Log Allocation / Assignment', PANEL, 50, 15, True)
        btn_log.bind(on_press=lambda x: setattr(self.manager, 'current', 'add_log'))
        layout.add_widget(btn_log)

        btn_view = make_button('  \U0001f4e6  View Profiles & Calendars', PRIMARY, 50, 15, True)
        btn_view.bind(on_press=lambda x: self.go_to_view())
        layout.add_widget(btn_view)

        # ④ Side-by-side manage buttons ────────────────────────────────
        manage_row = BoxLayout(
            orientation='horizontal',
            size_hint_y=None, height=dp(46),
            spacing=dp(7),
        )
        btn_owners = make_button('\U0001f464  Device Owners', PANEL_2, 46, 13)
        btn_owners.bind(on_press=lambda x: self.show_directory_popup(
            'device_owners', 'Manage Device Owners'))
        btn_clients = make_button('\U0001f3e2  Client Companies', PANEL_2, 46, 13)
        btn_clients.bind(on_press=lambda x: self.show_directory_popup(
            'rented_to_companies', 'Manage Rented To Companies'))
        manage_row.add_widget(btn_owners)
        manage_row.add_widget(btn_clients)
        layout.add_widget(manage_row)

        btn_reports = make_button('  \U0001f4c4  Reports / Backup / Export', SUCCESS, 50, 15, True)
        btn_reports.bind(on_press=lambda x: self.show_reports_popup())
        layout.add_widget(btn_reports)

        # ⑤ Last-log card ──────────────────────────────────────────────
        self.last_log_card = BoxLayout(
            orientation='vertical',
            size_hint_y=None, height=dp(68),
            padding=(dp(10), dp(6)),
            spacing=dp(2),
        )
        with self.last_log_card.canvas.before:
            Color(*STAT_BG)
            self._card_rect = Rectangle(
                size=self.last_log_card.size,
                pos=self.last_log_card.pos,
            )
        self.last_log_card.bind(
            size=lambda i, v: setattr(self._card_rect, 'size', v),
            pos=lambda i, v: setattr(self._card_rect, 'pos', v),
        )
        self._card_header = Label(
            text='LAST LOG',
            font_size=sp(10), bold=True,
            color=(0.50, 0.68, 0.88, 1),
            halign='left', valign='middle',
            size_hint_y=None, height=dp(18),
        )
        self._card_header.bind(size=self._card_header.setter('text_size'))
        self._card_body = Label(
            text='No logs yet.',
            font_size=sp(14),
            color=TEXT,
            halign='left', valign='middle',
            size_hint_y=None, height=dp(22),
        )
        self._card_body.bind(size=self._card_body.setter('text_size'))
        self._card_sub = Label(
            text='',
            font_size=sp(11),
            color=(0.55, 0.72, 0.88, 1),
            halign='left', valign='middle',
            size_hint_y=None, height=dp(16),
        )
        self._card_sub.bind(size=self._card_sub.setter('text_size'))
        self.last_log_card.add_widget(self._card_header)
        self.last_log_card.add_widget(self._card_body)
        self.last_log_card.add_widget(self._card_sub)
        layout.add_widget(self.last_log_card)

        self.add_widget(layout)

    # ── helpers ───────────────────────────────────────────────────────

    def _make_stat_tile(self, number, label):
        tile = BoxLayout(orientation='vertical', spacing=0)
        with tile.canvas.before:
            Color(*STAT_BG)
            rect = Rectangle(size=tile.size, pos=tile.pos)
        tile.bind(
            size=lambda i, v: setattr(rect, 'size', v),
            pos=lambda i, v: setattr(rect, 'pos', v),
        )
        lbl_num = Label(
            text=number,
            font_size=sp(24), bold=True,
            color=TEXT,
            halign='center', valign='bottom',
            size_hint_y=0.6,
        )
        lbl_num.bind(size=lbl_num.setter('text_size'))
        lbl_name = Label(
            text=label,
            font_size=sp(10),
            color=ACCENT,
            halign='center', valign='top',
            size_hint_y=0.4,
        )
        lbl_name.bind(size=lbl_name.setter('text_size'))
        tile.add_widget(lbl_num)
        tile.add_widget(lbl_name)
        tile._num_label = lbl_num
        return tile

    def _update_stat(self, tile, value):
        tile._num_label.text = str(value)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    # ── screen events ─────────────────────────────────────────────────

    def on_enter(self):
        self.refresh_stats()

    def refresh_stats(self):
        data = load_data()
        self._update_stat(self.stat_d, len(data.get('equipments', {})))
        self._update_stat(self.stat_l, len(data.get('logs', [])))
        self._update_stat(self.stat_c, len(data.get('rented_to_companies', {})))

        logs = data.get('logs', [])
        if logs:
            last  = logs[-1]
            equip  = last.get('equip_id', '')
            client = last.get('client', '')
            start  = last.get('start_date', last.get('date', ''))
            end    = last.get('end_date', '')
            term   = last.get('term', '')
            self._card_header.text = 'LAST LOG'
            self._card_body.text   = f'{equip}  \u2192  {client}   |   {term}'
            self._card_sub.text    = f'{start}  \u2013  {end}'
        else:
            self._card_header.text = 'LAST LOG'
            self._card_body.text   = 'No logs recorded yet.'
            self._card_sub.text    = ''

    def go_to_view(self):
        self.manager.get_screen('view_equip').update_list()
        self.manager.current = 'view_equip'

    # ── directory popup ───────────────────────────────────────────────

    def show_directory_popup(self, key_target, label_title):
        pop_layout = BoxLayout(orientation='vertical', padding=dp(14), spacing=dp(10))

        txt_name = TextInput(
            hint_text='Enter Name...',
            multiline=False,
            size_hint_y=None, height=dp(52),
            font_size=sp(16),
            background_color=PANEL,
            foreground_color=(1, 1, 1, 1),
            hint_text_color=(0.65, 0.65, 0.65, 1),
        )
        txt_phone = TextInput(
            hint_text='Enter Phone Number...',
            multiline=False,
            size_hint_y=None, height=dp(52),
            font_size=sp(16),
            background_color=PANEL,
            foreground_color=(1, 1, 1, 1),
            hint_text_color=(0.65, 0.65, 0.65, 1),
        )
        pop_layout.add_widget(txt_name)
        pop_layout.add_widget(txt_phone)

        scroll   = ScrollView(size_hint_y=1)
        list_box = GridLayout(cols=1, spacing=dp(8), size_hint_y=None, padding=(0, dp(4)))
        list_box.bind(minimum_height=list_box.setter('height'))
        scroll.add_widget(list_box)
        pop_layout.add_widget(scroll)

        popup = Popup(title=label_title, content=pop_layout, size_hint=(0.96, 0.86))

        def refresh_list():
            list_box.clear_widgets()
            data = load_data()
            if not data[key_target]:
                list_box.add_widget(Label(
                    text='No entries yet.',
                    size_hint_y=None, height=dp(52),
                    color=SUBTEXT, font_size=sp(16),
                ))
                return
            for name, details in data[key_target].items():
                row = BoxLayout(size_hint_y=None, height=dp(72), spacing=dp(8))
                lbl = Label(
                    text=f'[b]{name}[/b]\n[color=00b3ff]{details.get("phone", "N/A")}[/color]',
                    markup=True, halign='left', valign='middle',
                    size_hint_x=0.68, font_size=sp(15), color=TEXT,
                )
                lbl.bind(size=lbl.setter('text_size'))
                row.add_widget(lbl)
                btn_del = make_button('Delete', DANGER, 58, 15, True)
                btn_del.size_hint_x = 0.32
                if name == 'My Office':
                    btn_del.text = 'Locked'
                    btn_del.disabled = True
                    btn_del.background_color = (0.35, 0.35, 0.35, 1)
                else:
                    btn_del.bind(on_press=lambda x, n=name: confirm_delete_item(n))
                row.add_widget(btn_del)
                list_box.add_widget(row)

        def add_item(instance):
            name_val  = txt_name.text.strip()
            phone_val = txt_phone.text.strip() or 'No Phone'
            if name_val:
                data = load_data()
                data[key_target][name_val] = {'phone': phone_val}
                save_data(data)
                txt_name.text = ''
                txt_phone.text = ''
                refresh_list()

        def confirm_delete_item(name_key):
            data = load_data()
            if key_target == 'device_owners':
                used = sum(1 for eq in data['equipments'].values() if eq.get('supplier') == name_key)
                msg2 = f'\nUsed by {used} equipment profile(s).\nExisting records kept as history.'
            else:
                used = sum(1 for log in data['logs'] if log.get('client') == name_key)
                msg2 = f'\nUsed by {used} allocation log(s).\nExisting logs kept as history.'

            cl = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(14))
            msg = Label(
                text=f'Delete directory entry:\n[b]{name_key}[/b]{msg2}',
                markup=True, halign='center', valign='middle',
                font_size=sp(16), color=TEXT,
            )
            msg.bind(size=msg.setter('text_size'))
            cl.add_widget(msg)
            bb = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(56))
            by = make_button('Delete Entry', DANGER, 56, 16, True)
            bn = make_button('Cancel',       MUTED,  56, 16)
            bb.add_widget(by); bb.add_widget(bn)
            cl.add_widget(bb)
            cp = Popup(title='Confirm Delete', content=cl, size_hint=(0.90, 0.42))

            def do_delete(instance):
                d2 = load_data()
                if name_key in d2[key_target]:
                    del d2[key_target][name_key]
                    save_data(d2)
                cp.dismiss()
                refresh_list()

            by.bind(on_press=do_delete)
            bn.bind(on_press=cp.dismiss)
            cp.open()

        btn_add_entry = make_button('+ Add Entry Profile', SUCCESS, 54, 16, True)
        btn_add_entry.bind(on_press=add_item)
        pop_layout.add_widget(btn_add_entry)

        btn_close = make_button('Close', MUTED, 50, 16)
        btn_close.bind(on_press=popup.dismiss)
        pop_layout.add_widget(btn_close)

        refresh_list()
        popup.open()

    # ── reports popup ─────────────────────────────────────────────────

    def show_reports_popup(self):
        pop_layout = BoxLayout(orientation='vertical', padding=dp(14), spacing=dp(10))
        result_lbl = Label(
            text=f'Export folder:\n{get_export_dir()}',
            font_size=sp(13), color=SUBTEXT,
            halign='center', valign='middle',
            size_hint_y=None, height=dp(88),
        )
        result_lbl.bind(size=result_lbl.setter('text_size'))
        pop_layout.add_widget(result_lbl)

        def run_export(action, label):
            try:
                path = action()
                result_lbl.text = f'Done: {label}\n\nSaved at:\n{path}'
            except Exception as exc:
                result_lbl.text = f'Export failed:\n{exc}'

        for label, action, color in [
            ('Backup Database JSON',      backup_database_json,           PANEL),
            ('Export Inventory CSV',      export_equipment_inventory_csv, PANEL),
            ('Export Allocation Logs CSV',export_allocation_logs_csv,     PANEL),
            ('Create Summary PDF',        export_summary_pdf,             PRIMARY),
        ]:
            b = make_button(label, color, 56, 16, True)
            b.bind(on_press=lambda x, a=action, l=label: run_export(a, l))
            pop_layout.add_widget(b)

        note = Label(
            text='CSV files open directly in Excel.\nPDF is a printable summary report.',
            font_size=sp(13), color=SUBTEXT,
            halign='center', valign='middle',
            size_hint_y=None, height=dp(58),
        )
        note.bind(size=note.setter('text_size'))
        pop_layout.add_widget(note)

        btn_close = make_button('Close', MUTED, 54, 16)
        pop_layout.add_widget(btn_close)

        popup = Popup(title='Reports / Backup / Export', content=pop_layout, size_hint=(0.96, 0.86))
        btn_close.bind(on_press=popup.dismiss)
        popup.open()
