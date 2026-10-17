#!/usr/bin/env python3
import os
import glob
import gettext
import locale
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

# ---------------------------------------------------------
# Internationalization Configuration (i18n) - Native Standard
# ---------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_LOCALE = os.path.join(BASE_DIR, 'locale')

# Attention: /usr/bin/locale is a system command (file), so
# we need to check that it is a directory and contains our translation.
if os.path.isfile(os.path.join(LOCAL_LOCALE, 'pt_PT', 'LC_MESSAGES', 'autostart-manager.mo')):
    LOCALE_DIR = LOCAL_LOCALE
else:
    LOCALE_DIR = '/usr/share/locale'

DOMAIN = 'autostart-manager'

try:
    locale.setlocale(locale.LC_ALL, '')
except Exception:
    pass


def _setup_translation():
    """Respects the priority order of languages (LANGUAGE, LC_ALL,
    LC_MESSAGES, LANG). Any Portuguese variant (pt, pt_PT, pt_BR)
    uses the pt_PT translation. If the primary language is English, do not translate."""
    prefs = []
    for var in ('LANGUAGE', 'LC_ALL', 'LC_MESSAGES', 'LANG'):
        val = os.environ.get(var)
        if val:
            prefs += [l.split('.')[0].split('@')[0] for l in val.split(':') if l]

    langs = []
    for l in prefs:
        if l in ('C', 'POSIX') or l.startswith('en'):
            langs.append('C')   # 'C' stops the search -> original English text
            break
        langs.append('pt_PT' if l.startswith('pt') else l)

    translation = gettext.translation(
        DOMAIN, LOCALE_DIR, languages=langs or None, fallback=True
    )
    return translation.gettext


_ = _setup_translation()

AUTOSTART_DIR = os.path.expanduser('~/.config/autostart')

# CSS style for rounded cards and distinct text lines
STYLE_PROVIDER = Gtk.CssProvider()
CSS_DATA = b"""
list {
    background-color: transparent;
    padding: 6px;
}

/* Container for each entry (Card) */
list row {
    background-color: rgba(255, 255, 255, 0.07);
    margin-bottom: 10px;
    padding: 12px 14px;
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.05);
}

list row:hover {
    background-color: rgba(255, 255, 255, 0.12);
}

list row:selected {
    background-color: rgba(255, 255, 255, 0.18);
}

/* Highlighted app name */
.name-label {
    font-weight: bold;
    font-size: 14px;
}

/* Command line */
.exec-label {
    color: #b0b0b0;
    font-size: 12px;
    margin-top: 2px;
    font-family: monospace;
}

/* Comment line */
.comment-label {
    color: #888888;
    font-size: 11px;
    margin-top: 2px;
    font-style: italic;
}
"""
STYLE_PROVIDER.load_from_data(CSS_DATA)


class EditDialog(Gtk.Dialog):
    def __init__(self, parent, name="", exec_cmd="", comment=""):
        super().__init__(title=_("Edit/Add Startup Item"), parent=parent, flags=0)
        self.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)
        self.set_default_size(480, 240)

        box = self.get_content_area()
        box.set_spacing(8)
        box.set_border_width(12)

        box.add(Gtk.Label(label=_("Name:"), xalign=0))
        self.entry_name = Gtk.Entry(text=name)
        box.add(self.entry_name)

        box.add(Gtk.Label(label=_("Command / Script:"), xalign=0))
        exec_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.entry_exec = Gtk.Entry(text=exec_cmd)
        exec_box.pack_start(self.entry_exec, True, True, 0)

        btn_browse = Gtk.Button(label=_("Browse..."))
        btn_browse.connect("clicked", self.on_browse_clicked)
        exec_box.pack_start(btn_browse, False, False, 0)
        box.add(exec_box)

        box.add(Gtk.Label(label=_("Comment:"), xalign=0))
        self.entry_comment = Gtk.Entry(text=comment)
        box.add(self.entry_comment)

        self.show_all()

    def on_browse_clicked(self, widget):
        dialog = Gtk.FileChooserDialog(
            title=_("Select Script or Executable"),
            parent=self,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.ACCEPT)
        
        if dialog.run() == Gtk.ResponseType.ACCEPT:
            self.entry_exec.set_text(dialog.get_filename())
        dialog.destroy()


class AutostartManager(Gtk.Window):
    def __init__(self):
        super().__init__(title=_("Startup Applications"))
        # Width adjusted to 1000px and height to 500px
        self.set_default_size(1000, 500)
        self.set_border_width(12)

        os.makedirs(AUTOSTART_DIR, exist_ok=True)

        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            STYLE_PROVIDER,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.add(vbox)

        self.listbox = Gtk.ListBox()
        self.listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_hexpand(True)
        scrolled.set_vexpand(True)
        scrolled.add(self.listbox)
        vbox.pack_start(scrolled, True, True, 0)

        # Action Buttons
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        vbox.pack_start(hbox, False, False, 0)

        btn_add = Gtk.Button(label=_("Add"))
        btn_add.connect("clicked", self.on_add_clicked)
        hbox.pack_start(btn_add, True, True, 0)

        btn_edit = Gtk.Button(label=_("Edit"))
        btn_edit.connect("clicked", self.on_edit_clicked)
        hbox.pack_start(btn_edit, True, True, 0)

        btn_remove = Gtk.Button(label=_("Remove"))
        btn_remove.connect("clicked", self.on_remove_clicked)
        hbox.pack_start(btn_remove, True, True, 0)

        self.refresh_list()

    def refresh_list(self):
        for child in self.listbox.get_children():
            self.listbox.remove(child)

        files = glob.glob(os.path.join(AUTOSTART_DIR, "*.desktop"))
        for filepath in files:
            enabled = True
            name, exec_cmd, comment = "", "", ""
            
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line_s = line.strip()
                    if line_s.startswith("Name="):
                        name = line_s.split("=", 1)[1]
                    elif line_s.startswith("Exec="):
                        exec_cmd = line_s.split("=", 1)[1]
                    elif line_s.startswith("Comment="):
                        comment = line_s.split("=", 1)[1]
                    elif line_s.startswith("X-GNOME-Autostart-enabled="):
                        val = line_s.split("=", 1)[1].lower()
                        enabled = (val == "true")

            filename = os.path.basename(filepath)
            row = self.create_row_widget(enabled, name or filename, exec_cmd, comment, filename)
            self.listbox.add(row)

        self.listbox.show_all()

    def create_row_widget(self, enabled, name, exec_cmd, comment, filename):
        row = Gtk.ListBoxRow()
        row.filename = filename
        row.enabled = enabled
        row.item_name = name
        row.exec_cmd = exec_cmd
        row.comment = comment

        main_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)

        # Checkbox
        check = Gtk.CheckButton()
        check.set_active(enabled)
        check.connect("toggled", self.on_row_toggled, row)
        main_hbox.pack_start(check, False, False, 0)

        # VBox with text lines
        text_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)

        # 1. Name (Bold)
        lbl_name = Gtk.Label(label=name, xalign=0)
        lbl_name.get_style_context().add_class("name-label")
        text_vbox.pack_start(lbl_name, False, False, 0)

        # 2. Command
        if exec_cmd:
            lbl_exec = Gtk.Label(label=f"{_('Command:')} {exec_cmd}", xalign=0)
            lbl_exec.get_style_context().add_class("exec-label")
            text_vbox.pack_start(lbl_exec, False, False, 0)

        # 3. Comment
        if comment:
            lbl_comment = Gtk.Label(label=comment, xalign=0)
            lbl_comment.get_style_context().add_class("comment-label")
            text_vbox.pack_start(lbl_comment, False, False, 0)

        main_hbox.pack_start(text_vbox, True, True, 0)
        row.add(main_hbox)

        return row

    def save_desktop_file(self, filename, name, exec_cmd, comment, enabled=True):
        filepath = os.path.join(AUTOSTART_DIR, filename)
        content = (
            "[Desktop Entry]\n"
            "Type=Application\n"
            f"Name={name}\n"
            f"Exec={exec_cmd}\n"
            f"Comment={comment}\n"
            f"X-GNOME-Autostart-enabled={'true' if enabled else 'false'}\n"
        )
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        os.chmod(filepath, 0o755)

    def on_row_toggled(self, checkbutton, row):
        new_val = checkbutton.get_active()
        row.enabled = new_val
        self.save_desktop_file(row.filename, row.item_name, row.exec_cmd, row.comment, enabled=new_val)

    def on_add_clicked(self, widget):
        dialog = EditDialog(self)
        if dialog.run() == Gtk.ResponseType.OK:
            name = dialog.entry_name.get_text().strip()
            exec_cmd = dialog.entry_exec.get_text().strip()
            comment = dialog.entry_comment.get_text().strip()

            if name and exec_cmd:
                safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '_', '-')).rstrip().replace(' ', '_').lower()
                filename = f"{safe_name}.desktop"
                self.save_desktop_file(filename, name, exec_cmd, comment, enabled=True)
                self.refresh_list()
        dialog.destroy()

    def on_edit_clicked(self, widget):
        row = self.listbox.get_selected_row()
        if not row:
            return

        dialog = EditDialog(self, name=row.item_name, exec_cmd=row.exec_cmd, comment=row.comment)
        if dialog.run() == Gtk.ResponseType.OK:
            new_name = dialog.entry_name.get_text().strip()
            new_exec = dialog.entry_exec.get_text().strip()
            new_comment = dialog.entry_comment.get_text().strip()

            if new_name and new_exec:
                self.save_desktop_file(row.filename, new_name, new_exec, new_comment, enabled=row.enabled)
                self.refresh_list()
        dialog.destroy()

    def on_remove_clicked(self, widget):
        row = self.listbox.get_selected_row()
        if row:
            filepath = os.path.join(AUTOSTART_DIR, row.filename)
            if os.path.exists(filepath):
                os.remove(filepath)
            self.refresh_list()

if __name__ == "__main__":
    win = AutostartManager()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
