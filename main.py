import os
import json
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from moviepy.video.io.VideoFileClip import VideoFileClip

APP_DATA_FILE = "data.json"
VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"}


# -------------------------
# i18n
# -------------------------
I18N = {
    "es": {
        "app_title": "WorkHours Tracker",
        "header_title": "Registro de horas trabajadas",
        "header_sub": "Suma automáticamente duraciones de videos y también permite agregar tiempo manual.",
        "card_total": "Total acumulado",
        "card_videos": "Videos guardados",
        "card_manual": "Entradas manuales",
        "actions": "Acciones",
        "folder_title": "Carpeta de videos",
        "choose": "Elegir…",
        "include_sub": "Incluir subcarpetas",
        "scan_save": "Escanear carpeta y guardar nuevos videos",
        "manual_title": "Agregar tiempo manual",
        "manual_time": "Tiempo (m:ss):",
        "manual_desc": "Descripción:",
        "manual_add": "Agregar a la lista",
        "manage": "Gestión",
        "delete_selected": "Eliminar item seleccionado",
        "reset_all": "Resetear TODO",
        "tip": "Tip: la app carga tus datos al abrir.\nNo necesitas escanear de nuevo.",
        "history": "Historial",
        "col_type": "Tipo",
        "col_desc": "Descripción",
        "col_dur": "Duración",
        "col_path": "Ruta",
        "type_video": "Video",
        "type_manual": "Manual",
        "err": "Error",
        "err_folder": "Selecciona una carpeta válida.",
        "err_time_format": "Formato inválido. Usa m:ss (ej: 2:34) o minutos enteros (ej: 25).",
        "err_time_positive": "El tiempo debe ser mayor que 0.",
        "info": "Info",
        "pick_row": "Selecciona un item en la tabla para eliminarlo.",
        "confirm": "Confirmar",
        "confirm_delete": "¿Eliminar el item seleccionado?",
        "confirm_reset": "¿Seguro que quieres borrar TODO el historial?",
        "done": "Listo",
        "scan_added": "Agregados {n} videos nuevos.\nTiempo añadido: {t}",
        "saved": "Guardado",
        "saved_msg": "Se guardaron {n} items.",
        "warn": "Aviso",
        "warn_not_found": "No se encontró el item en los datos (raro).",
        "lang_btn": "EN",
        "manual_default": "entrada manual",
    },
    "en": {
        "app_title": "WorkHours Tracker",
        "header_title": "Worked hours tracker",
        "header_sub": "Automatically sums video durations and lets you add manual time.",
        "card_total": "Total",
        "card_videos": "Saved videos",
        "card_manual": "Manual entries",
        "actions": "Actions",
        "folder_title": "Video folder",
        "choose": "Browse…",
        "include_sub": "Include subfolders",
        "scan_save": "Scan folder and save new videos",
        "manual_title": "Add manual time",
        "manual_time": "Time (m:ss):",
        "manual_desc": "Description:",
        "manual_add": "Add to list",
        "manage": "Manage",
        "delete_selected": "Delete selected item",
        "reset_all": "Reset ALL",
        "tip": "Tip: the app loads your data on startup.\nNo need to scan again.",
        "history": "History",
        "col_type": "Type",
        "col_desc": "Description",
        "col_dur": "Duration",
        "col_path": "Path",
        "type_video": "Video",
        "type_manual": "Manual",
        "err": "Error",
        "err_folder": "Choose a valid folder.",
        "err_time_format": "Invalid format. Use m:ss (e.g., 2:34) or whole minutes (e.g., 25).",
        "err_time_positive": "Time must be greater than 0.",
        "info": "Info",
        "pick_row": "Select an item in the table to delete it.",
        "confirm": "Confirm",
        "confirm_delete": "Delete the selected item?",
        "confirm_reset": "Are you sure you want to delete ALL history?",
        "done": "Done",
        "scan_added": "Added {n} new videos.\nAdded time: {t}",
        "saved": "Saved",
        "saved_msg": "Saved {n} items.",
        "warn": "Warning",
        "warn_not_found": "Item not found in data (weird).",
        "lang_btn": "ES",
        "manual_default": "Manual input",
    }
}


# -------------------------
# Helpers
# -------------------------
def now_ts() -> int:
    return int(time.time())


def load_data():
    if os.path.exists(APP_DATA_FILE):
        try:
            with open(APP_DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                data.setdefault("items", [])
                return data
        except Exception:
            pass
    return {"items": []}


def save_data(data):
    with open(APP_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def format_hms(seconds: float) -> str:
    s = int(round(seconds))
    h = s // 3600
    m = (s % 3600) // 60
    sec = s % 60
    return f"{h:02d}:{m:02d}:{sec:02d}"


def format_hm(seconds: float) -> str:
    s = int(round(seconds))
    h = s // 3600
    m = (s % 3600) // 60
    return f"{h}h {m}m"


def safe_video_duration_seconds(path: str) -> float:
    try:
        with VideoFileClip(path) as clip:
            return float(clip.duration or 0)
    except Exception:
        return 0.0


def fingerprint(path: str) -> str:
    st = os.stat(path)
    return f"{path}|{st.st_size}|{int(st.st_mtime)}"


def is_video_file(path: str) -> bool:
    return os.path.splitext(path)[1].lower() in VIDEO_EXTS


def parse_manual_time_to_seconds(s: str) -> float | None:
    """
    Acepta:
      - "m:ss"  (2:34)
      - "mm:ss" (12:05)
      - "m" o "mm" (solo minutos) (25)
    """
    s = s.strip()
    if not s:
        return None

    if ":" in s:
        parts = s.split(":")
        if len(parts) != 2:
            return None
        m_str, sec_str = parts[0].strip(), parts[1].strip()
        if not (m_str.isdigit() and sec_str.isdigit()):
            return None
        m = int(m_str)
        sec = int(sec_str)
        if sec < 0 or sec >= 60:
            return None
        total = m * 60 + sec
        return float(total) if total > 0 else None

    # solo minutos
    if s.isdigit():
        m = int(s)
        total = m * 60
        return float(total) if total > 0 else None

    return None


# -------------------------
# App
# -------------------------
class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.lang = "es"
        self.t = lambda k: I18N[self.lang][k]

        self.data = load_data()

        self._setup_style()
        self._build_ui()

        self.refresh_table_and_totals()

    def _setup_style(self):
        self.configure(bg="#121212")
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("TFrame", background="#121212")
        style.configure("Card.TFrame", background="#1b1b1b")
        style.configure("TLabel", background="#121212", foreground="#eaeaea")
        style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"))
        style.configure("Sub.TLabel", font=("Segoe UI", 10), foreground="#cfcfcf")
        style.configure("CardTitle.TLabel", background="#1b1b1b", foreground="#eaeaea",
                        font=("Segoe UI", 11, "bold"))
        style.configure("CardText.TLabel", background="#1b1b1b", foreground="#d8d8d8",
                        font=("Segoe UI", 10))

        style.configure("TButton", font=("Segoe UI", 10), padding=8)

        style.configure("Treeview",
                        background="#1b1b1b",
                        fieldbackground="#1b1b1b",
                        foreground="#eaeaea",
                        rowheight=28,
                        borderwidth=0)
        style.configure("Treeview.Heading",
                        background="#242424",
                        foreground="#eaeaea",
                        font=("Segoe UI", 10, "bold"))
        style.map("Treeview", background=[("selected", "#2e2e2e")])

        style.configure("TProgressbar", troughcolor="#242424", bordercolor="#242424", background="#4a90e2")

    def _build_ui(self):
        self.title(self.t("app_title"))
        self.geometry("860x560")
        self.minsize(860, 560)

        root = ttk.Frame(self)
        root.pack(fill="both", expand=True, padx=16, pady=16)

        # Header row with language button
        header = ttk.Frame(root)
        header.pack(fill="x", pady=(0, 12))

        header_left = ttk.Frame(header)
        header_left.pack(side="left", fill="x", expand=True)

        self.lbl_header_title = ttk.Label(header_left, text=self.t("header_title"), style="Title.TLabel")
        self.lbl_header_title.pack(anchor="w")

        self.lbl_header_sub = ttk.Label(header_left, text=self.t("header_sub"), style="Sub.TLabel")
        self.lbl_header_sub.pack(anchor="w", pady=(4, 0))

        header_right = ttk.Frame(header)
        header_right.pack(side="right")

        self.btn_lang = ttk.Button(header_right, text=self.t("lang_btn"), command=self.toggle_language, width=6)
        self.btn_lang.pack(anchor="e")

        # Cards row
        cards = ttk.Frame(root)
        cards.pack(fill="x", pady=(0, 12))

        self.card_total = self._make_card(cards, self.t("card_total"), "0h 0m")
        self.card_videos = self._make_card(cards, self.t("card_videos"), "0")
        self.card_manual = self._make_card(cards, self.t("card_manual"), "0")

        self.card_total.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.card_videos.pack(side="left", fill="x", expand=True, padx=8)
        self.card_manual.pack(side="left", fill="x", expand=True, padx=(8, 0))

        # Main split
        main = ttk.Frame(root)
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main, style="Card.TFrame")
        left.pack(side="left", fill="y", padx=(0, 12))
        right = ttk.Frame(main, style="Card.TFrame")
        right.pack(side="left", fill="both", expand=True)

        # Left title
        self.lbl_actions = ttk.Label(left, text=self.t("actions"), style="CardTitle.TLabel")
        self.lbl_actions.pack(anchor="w", padx=12, pady=(12, 6))

        # Folder / scan
        folder_box = ttk.Frame(left, style="Card.TFrame")
        folder_box.pack(fill="x", padx=12, pady=(0, 10))

        self.lbl_folder = ttk.Label(folder_box, text=self.t("folder_title"), style="CardText.TLabel")
        self.lbl_folder.pack(anchor="w")

        self.folder_var = tk.StringVar(value="")
        folder_row = ttk.Frame(folder_box, style="Card.TFrame")
        folder_row.pack(fill="x", pady=(6, 0))

        self.folder_entry = ttk.Entry(folder_row, textvariable=self.folder_var)
        self.folder_entry.pack(side="left", fill="x", expand=True)

        self.btn_choose = ttk.Button(folder_row, text=self.t("choose"), command=self.pick_folder)
        self.btn_choose.pack(side="left", padx=(8, 0))

        self.include_sub_var = tk.BooleanVar(value=True)
        self.chk_sub = ttk.Checkbutton(folder_box, text=self.t("include_sub"), variable=self.include_sub_var)
        self.chk_sub.pack(anchor="w", pady=(8, 0))

        self.btn_scan = ttk.Button(folder_box, text=self.t("scan_save"), command=self.scan_and_save)
        self.btn_scan.pack(fill="x", pady=(10, 0))

        # Mini progress bar (hidden until scan)
        self.progress = ttk.Progressbar(folder_box, mode="determinate", length=260)
        self.progress.pack(fill="x", pady=(8, 0))
        self.progress.pack_forget()

        # Manual add
        manual_box = ttk.Frame(left, style="Card.TFrame")
        manual_box.pack(fill="x", padx=12, pady=(0, 10))

        self.lbl_manual_title = ttk.Label(manual_box, text=self.t("manual_title"), style="CardText.TLabel")
        self.lbl_manual_title.pack(anchor="w")

        row1 = ttk.Frame(manual_box, style="Card.TFrame")
        row1.pack(fill="x", pady=(6, 0))

        self.lbl_manual_time = ttk.Label(row1, text=self.t("manual_time"), style="CardText.TLabel")
        self.lbl_manual_time.pack(side="left")

        self.manual_time = tk.StringVar(value="")
        ttk.Entry(row1, textvariable=self.manual_time, width=12).pack(side="left", padx=(8, 0))

        row2 = ttk.Frame(manual_box, style="Card.TFrame")
        row2.pack(fill="x", pady=(6, 0))

        self.lbl_manual_desc = ttk.Label(row2, text=self.t("manual_desc"), style="CardText.TLabel")
        self.lbl_manual_desc.pack(side="left")

        self.manual_label = tk.StringVar(value=self.t("manual_default"))
        ttk.Entry(row2, textvariable=self.manual_label).pack(side="left", fill="x", expand=True, padx=(8, 0))

        self.btn_manual_add = ttk.Button(manual_box, text=self.t("manual_add"), command=self.add_manual)
        self.btn_manual_add.pack(fill="x", pady=(10, 0))

        # Manage
        manage_box = ttk.Frame(left, style="Card.TFrame")
        manage_box.pack(fill="x", padx=12, pady=(0, 12))

        self.lbl_manage = ttk.Label(manage_box, text=self.t("manage"), style="CardText.TLabel")
        self.lbl_manage.pack(anchor="w")

        self.btn_delete = ttk.Button(manage_box, text=self.t("delete_selected"), command=self.delete_selected)
        self.btn_delete.pack(fill="x", pady=(8, 0))

        self.btn_reset = ttk.Button(manage_box, text=self.t("reset_all"), command=self.reset_all)
        self.btn_reset.pack(fill="x", pady=(8, 0))

        self.lbl_tip = ttk.Label(left, text=self.t("tip"), style="CardText.TLabel")
        self.lbl_tip.pack(anchor="w", padx=12, pady=(0, 12))

        # Right: table
        self.lbl_history = ttk.Label(right, text=self.t("history"), style="CardTitle.TLabel")
        self.lbl_history.pack(anchor="w", padx=12, pady=(12, 6))

        cols = ("tipo", "descripcion", "duracion", "ruta")
        self.tree = ttk.Treeview(right, columns=cols, show="headings")
        self.tree.heading("tipo", text=self.t("col_type"))
        self.tree.heading("descripcion", text=self.t("col_desc"))
        self.tree.heading("duracion", text=self.t("col_dur"))
        self.tree.heading("ruta", text=self.t("col_path"))

        self.tree.column("tipo", width=90, anchor="w")
        self.tree.column("descripcion", width=240, anchor="w")
        self.tree.column("duracion", width=110, anchor="center")
        self.tree.column("ruta", width=360, anchor="w")

        self.tree.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        sb = ttk.Scrollbar(self.tree, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.place(relx=1.0, rely=0, relheight=1.0, anchor="ne")

    def _make_card(self, parent, title, value):
        card = ttk.Frame(parent, style="Card.TFrame")
        title_lbl = ttk.Label(card, text=title, style="CardTitle.TLabel")
        title_lbl.pack(anchor="w", padx=12, pady=(10, 0))
        value_lbl = ttk.Label(card, text=value, style="CardText.TLabel", font=("Segoe UI", 18, "bold"))
        value_lbl.pack(anchor="w", padx=12, pady=(4, 10))
        card.title_label = title_lbl
        card.value_label = value_lbl
        return card

    # -------------------------
    # Language
    # -------------------------
    def toggle_language(self):
        self.lang = "en" if self.lang == "es" else "es"
        self.t = lambda k: I18N[self.lang][k]
        self.apply_language()

    def apply_language(self):
        self.title(self.t("app_title"))

        self.lbl_header_title.config(text=self.t("header_title"))
        self.lbl_header_sub.config(text=self.t("header_sub"))

        self.btn_lang.config(text=self.t("lang_btn"))

        self.card_total.title_label.config(text=self.t("card_total"))
        self.card_videos.title_label.config(text=self.t("card_videos"))
        self.card_manual.title_label.config(text=self.t("card_manual"))

        self.lbl_actions.config(text=self.t("actions"))
        self.lbl_folder.config(text=self.t("folder_title"))
        self.btn_choose.config(text=self.t("choose"))
        self.chk_sub.config(text=self.t("include_sub"))
        self.btn_scan.config(text=self.t("scan_save"))

        self.lbl_manual_title.config(text=self.t("manual_title"))
        self.lbl_manual_time.config(text=self.t("manual_time"))
        self.lbl_manual_desc.config(text=self.t("manual_desc"))
        self.btn_manual_add.config(text=self.t("manual_add"))

        self.lbl_manage.config(text=self.t("manage"))
        self.btn_delete.config(text=self.t("delete_selected"))
        self.btn_reset.config(text=self.t("reset_all"))

        self.lbl_tip.config(text=self.t("tip"))
        self.lbl_history.config(text=self.t("history"))

        self.tree.heading("tipo", text=self.t("col_type"))
        self.tree.heading("descripcion", text=self.t("col_desc"))
        self.tree.heading("duracion", text=self.t("col_dur"))
        self.tree.heading("ruta", text=self.t("col_path"))

        # Solo actualiza el placeholder si el usuario no escribió nada custom
        if not self.manual_label.get().strip():
            self.manual_label.set(self.t("manual_default"))

        self.refresh_table_and_totals()

    # -------------------------
    # Actions
    # -------------------------
    def pick_folder(self):
        p = filedialog.askdirectory()
        if p:
            self.folder_var.set(p)

    def list_videos(self, root):
        paths = []
        if self.include_sub_var.get():
            for dirpath, _, filenames in os.walk(root):
                for fn in filenames:
                    full = os.path.join(dirpath, fn)
                    if os.path.isfile(full) and is_video_file(full):
                        paths.append(full)
        else:
            for fn in os.listdir(root):
                full = os.path.join(root, fn)
                if os.path.isfile(full) and is_video_file(full):
                    paths.append(full)
        return paths

    def scan_and_save(self):
        root = self.folder_var.get().strip()
        if not root or not os.path.isdir(root):
            messagebox.showerror(self.t("err"), self.t("err_folder"))
            return

        paths = self.list_videos(root)
        existing_ids = {it.get("id") for it in self.data["items"] if it.get("id")}

        # UI: show progress
        self.progress.pack(fill="x", pady=(8, 0))
        self.progress["value"] = 0
        self.progress["maximum"] = max(len(paths), 1)

        # disable buttons while scanning
        self.btn_scan.config(state="disabled")
        self.btn_manual_add.config(state="disabled")
        self.btn_delete.config(state="disabled")
        self.btn_reset.config(state="disabled")
        self.btn_choose.config(state="disabled")
        self.btn_lang.config(state="disabled")

        added = 0
        added_seconds = 0.0

        try:
            for i, p in enumerate(paths, start=1):
                try:
                    fid = fingerprint(p)
                except Exception:
                    fid = None

                if fid and fid not in existing_ids:
                    dur = safe_video_duration_seconds(p)
                    item = {
                        "id": fid,
                        "type": "video",
                        "label": os.path.basename(p),
                        "duration_sec": dur,
                        "added_at": now_ts(),
                        "path": p
                    }
                    self.data["items"].append(item)
                    existing_ids.add(fid)
                    added += 1
                    added_seconds += dur

                self.progress["value"] = i
                self.update_idletasks()  # refresca la barra

        finally:
            save_data(self.data)
            self.refresh_table_and_totals()

            # re-enable
            self.btn_scan.config(state="normal")
            self.btn_manual_add.config(state="normal")
            self.btn_delete.config(state="normal")
            self.btn_reset.config(state="normal")
            self.btn_choose.config(state="normal")
            self.btn_lang.config(state="normal")

            self.progress.pack_forget()

        messagebox.showinfo(self.t("done"), self.t("scan_added").format(n=added, t=format_hms(added_seconds)))

    def add_manual(self):
        time_str = self.manual_time.get().strip()
        label = self.manual_label.get().strip() or self.t("manual_default")

        sec = parse_manual_time_to_seconds(time_str)
        if sec is None:
            messagebox.showerror(self.t("err"), self.t("err_time_format"))
            return
        if sec <= 0:
            messagebox.showerror(self.t("err"), self.t("err_time_positive"))
            return

        item = {
            "id": f"manual-{now_ts()}-{len(self.data['items'])}",
            "type": "manual",
            "label": label,
            "duration_sec": float(sec),
            "added_at": now_ts(),
            "path": ""
        }
        self.data["items"].append(item)
        save_data(self.data)

        self.manual_time.set("")
        self.refresh_table_and_totals()

    def delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo(self.t("info"), self.t("pick_row"))
            return

        item_id = sel[0]
        if not messagebox.askyesno(self.t("confirm"), self.t("confirm_delete")):
            return

        before = len(self.data["items"])
        self.data["items"] = [it for it in self.data["items"] if it.get("id") != item_id]
        after = len(self.data["items"])

        save_data(self.data)
        self.refresh_table_and_totals()

        if before == after:
            messagebox.showwarning(self.t("warn"), self.t("warn_not_found"))

    def reset_all(self):
        if not messagebox.askyesno(self.t("confirm"), self.t("confirm_reset")):
            return
        self.data = {"items": []}
        save_data(self.data)
        self.refresh_table_and_totals()

    # -------------------------
    # UI refresh
    # -------------------------
    def refresh_table_and_totals(self):
        for iid in self.tree.get_children():
            self.tree.delete(iid)

        total_sec = 0.0
        videos = 0
        manual = 0

        items = sorted(self.data["items"], key=lambda x: x.get("added_at", 0), reverse=True)

        for it in items:
            t = it.get("type", "video")
            label = it.get("label", "")
            dur = float(it.get("duration_sec", 0.0) or 0.0)
            path = it.get("path", "") or ""

            total_sec += dur
            if t == "video":
                videos += 1
            else:
                manual += 1

            self.tree.insert(
                "", "end",
                iid=it.get("id", f"row-{time.time()}"),
                values=(
                    self.t("type_video") if t == "video" else self.t("type_manual"),
                    label,
                    format_hms(dur),
                    path
                )
            )

        self.card_total.value_label.config(text=format_hm(total_sec))
        self.card_videos.value_label.config(text=str(videos))
        self.card_manual.value_label.config(text=str(manual))


if __name__ == "__main__":
    App().mainloop()
