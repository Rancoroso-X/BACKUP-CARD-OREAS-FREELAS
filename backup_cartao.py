import os
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox, font
import threading
import time
from datetime import datetime
from collections import defaultdict
import queue
import re
import platform
import subprocess

# Importação opcional do PIL
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# --------------------------- CONFIGURAÇÃO DE TEMA ---------------------------


class ModernTheme:
    # Cores do tema dark
    BG_PRIMARY = "#0a0a0a"
    BG_SECONDARY = "#1a1a1a"
    BG_TERTIARY = "#2a2a2a"
    BG_HOVER = "#3a3a3a"
    FG_PRIMARY = "#ffffff"
    FG_SECONDARY = "#b0b0b0"
    ACCENT = "#0084ff"
    ACCENT_HOVER = "#0066cc"
    SUCCESS = "#00d26a"
    WARNING = "#ffa116"
    ERROR = "#f85149"

    @staticmethod
    def configure_styles():
        style = ttk.Style()
        if 'clam' not in style.theme_names():
            return  # 'clam' theme not available
        style.theme_use('clam')

        # General background and foreground
        style.configure('.', background=ModernTheme.BG_PRIMARY,
                        foreground=ModernTheme.FG_PRIMARY,
                        font=('Arial', 10))
        style.configure('TFrame', background=ModernTheme.BG_PRIMARY)
        style.configure('TLabel', background=ModernTheme.BG_PRIMARY,
                        foreground=ModernTheme.FG_PRIMARY)

        # Notebook
        style.configure(
            "TNotebook", background=ModernTheme.BG_PRIMARY, borderwidth=0)
        style.configure("TNotebook.Tab", background=ModernTheme.BG_SECONDARY,
                        foreground=ModernTheme.FG_SECONDARY, padding=[10, 5], font=('Arial', 11, 'bold'))
        style.map("TNotebook.Tab",
                  background=[("selected", ModernTheme.ACCENT),
                              ("active", ModernTheme.BG_HOVER)],
                  foreground=[("selected", ModernTheme.FG_PRIMARY), ("active", ModernTheme.FG_PRIMARY)])

        # Configure Checkbutton
        style.configure('TCheckbutton',
                        background=ModernTheme.BG_SECONDARY,
                        foreground=ModernTheme.FG_PRIMARY,
                        focuscolor=ModernTheme.BG_SECONDARY,  # Remove focus highlight
                        font=('Arial', 11))
        style.map('TCheckbutton',
                  background=[('active', ModernTheme.BG_TERTIARY)],
                  foreground=[('disabled', ModernTheme.FG_SECONDARY)])

        # Entry widgets
        style.configure('TEntry', fieldbackground=ModernTheme.BG_TERTIARY,
                        foreground=ModernTheme.FG_PRIMARY,
                        bordercolor=ModernTheme.BG_HOVER,
                        lightcolor=ModernTheme.BG_HOVER,
                        darkcolor=ModernTheme.BG_HOVER,
                        font=('Arial', 10),
                        insertbackground=ModernTheme.FG_PRIMARY)  # Cursor color
        style.map('TEntry', fieldbackground=[('focus', ModernTheme.BG_HOVER)])

        # Buttons
        style.configure('Modern.TButton',
                        background=ModernTheme.ACCENT,
                        foreground='white',
                        font=('Arial', 11, 'bold'),
                        borderwidth=0,
                        focuscolor=ModernTheme.ACCENT_HOVER,
                        relief='flat',
                        padding=(10, 5))
        style.map('Modern.TButton',
                  background=[('active', ModernTheme.ACCENT_HOVER),
                              ('pressed', ModernTheme.ACCENT_HOVER),
                              ('disabled', ModernTheme.BG_HOVER)],
                  foreground=[('disabled', ModernTheme.FG_SECONDARY)])

        # Special Buttons (Success, Warning, Error)
        button_configs = {
            'Success': (ModernTheme.SUCCESS, "#00a854"),
            'Warning': (ModernTheme.WARNING, "#cc7a00"),
            'Error': (ModernTheme.ERROR, "#cc0000")
        }
        for name, (bg, hover_bg) in button_configs.items():
            style.configure(f'{name}.TButton',
                            background=bg,
                            foreground='white',
                            font=('Arial', 11, 'bold'),
                            borderwidth=0,
                            focuscolor=hover_bg,
                            relief='flat',
                            padding=(10, 5))
            style.map(f'{name}.TButton',
                      background=[('active', hover_bg), ('pressed',
                                                         hover_bg), ('disabled', ModernTheme.BG_HOVER)],
                      foreground=[('disabled', ModernTheme.FG_SECONDARY)])

        # Scrollbar styling
        style.configure('TScrollbar',
                        background=ModernTheme.BG_TERTIARY,
                        troughcolor=ModernTheme.BG_SECONDARY,
                        bordercolor=ModernTheme.BG_SECONDARY,
                        arrowcolor=ModernTheme.FG_PRIMARY,
                        relief='flat',
                        width=12)
        style.map('TScrollbar', background=[('active', ModernTheme.ACCENT)])

        # Progressbar styling
        style.configure('Modern.Horizontal.TProgressbar',
                        background=ModernTheme.ACCENT,
                        troughcolor=ModernTheme.BG_SECONDARY,
                        bordercolor=ModernTheme.BG_TERTIARY)

    @staticmethod
    def create_styled_button(parent, text, command, style_name="Modern.TButton", width=None):
        btn = ttk.Button(parent, text=text, command=command, style=style_name)
        if width:
            btn.config(width=width)
        return btn

# --------------------------- QUEUE PARA THREAD SAFETY ---------------------------


class ThreadSafeQueue:
    def __init__(self):
        self.queue = queue.Queue()

    def put(self, item):
        self.queue.put(item)

    def get_all(self):
        items = []
        while not self.queue.empty():
            try:
                items.append(self.queue.get_nowait())
            except queue.Empty:
                break
        return items

# --------------------------- FUNÇÕES AUXILIARES ---------------------------


def get_file_types():
    return {
        'photo': ['.JPG', '.JPEG', '.ARW', '.RAW', '.CR2', '.CR3', '.NEF', '.DNG', '.RAF', '.ORF', '.HEIC', '.TIFF'],
        'video': ['.MP4', '.MOV', '.AVI', '.MTS', '.M2TS', '.MXF', '.BRAW', '.R3D', '.MPEG', '.WMV', '.FLV'],
        'meta': ['.XML', '.XMP']
    }


def listar_arquivos(caminho, incluir_xml):
    file_types = get_file_types()
    tipos_fotos = file_types['photo']
    tipos_videos = file_types['video']
    tipos_xml = file_types['meta'] if incluir_xml else []

    arquivos_fotos, arquivos_videos, arquivos_xml = [], [], []

    excluded_dirs = ['THMBNL', '.Trash',
                     'System Volume Information', 'RECYCLER', '$RECYCLE.BIN']

    for raiz, _, nomes in os.walk(caminho):
        if any(skip in raiz for skip in excluded_dirs):
            continue

        for nome in nomes:
            if nome.startswith(('._', '~$')) or nome == '.DS_Store':
                continue

            full_path = os.path.join(raiz, nome)
            nome_up = nome.upper()

            if any(nome_up.endswith(t) for t in tipos_fotos):
                arquivos_fotos.append(full_path)
            elif any(nome_up.endswith(t) for t in tipos_videos):
                arquivos_videos.append(full_path)
            elif any(nome_up.endswith(t) for t in tipos_xml):
                arquivos_xml.append(full_path)

    return arquivos_fotos, arquivos_videos, arquivos_xml


def extrair_data_arquivo(caminho):
    try:
        return datetime.fromtimestamp(os.path.getmtime(caminho)).strftime('%Y-%m-%d')
    except Exception:
        return 'UNKNOWN-DATE'


def formatar_data_br(data_str):
    if data_str == 'UNKNOWN-DATE':
        return 'Data Desconhecida'
    try:
        return datetime.strptime(data_str, '%Y-%m-%d').strftime('%d/%m/%Y')
    except (ValueError, IndexError):
        return data_str


def checar_espaco(destino):
    try:
        total, _, free = shutil.disk_usage(destino)
        return total, free
    except FileNotFoundError:
        return 0, 0


def tamanho_total_arquivos(arquivos):
    return sum(os.path.getsize(a) for a in arquivos if os.path.exists(a))


def formatar_tamanho(b):
    if b is None:
        return "N/A"
    if b < 1024:
        return f"{b} B"
    kb = b / 1024
    if kb < 1024:
        return f"{kb:.0f} KB"
    mb = kb / 1024
    if mb < 1024:
        return f"{mb:.1f} MB"
    gb = mb / 1024
    return f"{gb:.2f} GB"


def tipo_arquivo(nome):
    nome_up = nome.upper()
    file_types = get_file_types()
    if any(nome_up.endswith(t) for t in file_types['video']):
        return 'VIDEOS'
    if any(nome_up.endswith(t) for t in file_types['photo']):
        return 'FOTOS'
    if any(nome_up.endswith(t) for t in file_types['meta']):
        return 'METADATA'
    return 'OUTROS'


def gerar_thumbnail(arquivo, tamanho=(100, 100)):
    if not PIL_AVAILABLE or tipo_arquivo(arquivo) != 'FOTOS':
        return None
    try:
        with Image.open(arquivo) as img:
            img.thumbnail(tamanho, Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(img)
    except Exception:
        return None


def abrir_pasta(pasta):
    if not pasta or not os.path.exists(pasta):
        messagebox.showwarning("Pasta não encontrada",
                               "O caminho da pasta de destino não é válido.")
        return
    try:
        if platform.system() == "Windows":
            subprocess.run(["explorer", os.path.normpath(pasta)], check=True)
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", pasta], check=True)
        else:  # Linux
            subprocess.run(["xdg-open", pasta], check=True)
    except Exception as e:
        messagebox.showerror("Erro ao abrir pasta",
                             f"Não foi possível abrir a pasta:\n{e}")


# --------------------------- POPUP DE SELEÇÃO DE DATAS ---------------------------
class PopupSelecaoDatas(tk.Toplevel):
    def __init__(self, parent, datas_info, destino_base, video_icon):
        super().__init__(parent)
        self.parent = parent
        self.datas_info = datas_info
        self.destino_base = destino_base
        self.video_icon = video_icon
        self.result = {}

        self.title("Configuração de Backup por Data")
        self.geometry("1000x700")
        self.configure(bg=ModernTheme.BG_PRIMARY)
        self.minsize(900, 600)

        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.cancelar)

        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

        main_frame = ttk.Frame(self, style='TFrame')
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        main_frame.rowconfigure(1, weight=1)
        main_frame.columnconfigure(0, weight=1)

        ttk.Label(main_frame, text="📅 Configuração de Backup por Data", font=(
            'Arial', 18, 'bold')).grid(row=0, column=0, pady=(0, 20))

        container = ttk.Frame(main_frame)
        container.grid(row=1, column=0, sticky="nsew")
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        canvas = tk.Canvas(
            container, bg=ModernTheme.BG_SECONDARY, highlightthickness=0)
        scrollbar = ttk.Scrollbar(
            container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style='TFrame')

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind("<MouseWheel>", _on_mousewheel)

        self.checkboxes, self.pasta_entries, self.prefixo_entries, self.renomear_vars, self.manter_numeracao_vars, self.exemplo_labels, self.rename_widgets_by_date = {
        }, {}, {}, {}, {}, {}, defaultdict(list)

        for data in sorted(datas_info.keys()):
            self._create_date_entry(scrollable_frame, data, datas_info[data])

        # Action Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=2, column=0, pady=(20, 0))

        ModernTheme.create_styled_button(
            btn_frame, "Selecionar Todas", self.selecionar_todas).pack(side="left", padx=5)
        ModernTheme.create_styled_button(
            btn_frame, "Desmarcar Todas", self.desmarcar_todas).pack(side="left", padx=5)
        ModernTheme.create_styled_button(
            btn_frame, "✓ Confirmar", self.confirmar, "Success.TButton").pack(side="left", padx=5)
        ModernTheme.create_styled_button(
            btn_frame, "✗ Cancelar", self.cancelar, "Error.TButton").pack(side="left", padx=5)

    def _create_date_entry(self, parent, data, info):
        data_frame = ttk.Frame(parent, style='TFrame',
                               relief=tk.RAISED, borderwidth=1, padding=15)
        data_frame.pack(fill="x", padx=15, pady=8, anchor="n")
        data_frame.columnconfigure(1, weight=1)

        # Checkbox and info
        var = tk.BooleanVar(value=True)
        self.checkboxes[data] = var
        ttk.Checkbutton(data_frame, text=f"📅 {formatar_data_br(data)}", variable=var).grid(
            row=0, column=0, sticky="w", pady=(0, 5))
        info_text = f"({len(info['arquivos'])} arquivos - {formatar_tamanho(info['tamanho'])})"
        ttk.Label(data_frame, text=info_text, foreground=ModernTheme.FG_SECONDARY).grid(
            row=0, column=1, sticky="w", padx=10, pady=(0, 5))

        # Previews
        preview_frame = ttk.Frame(data_frame, style='TFrame')
        preview_frame.grid(row=1, column=0, columnspan=2, pady=5, sticky="w")

        has_content = False
        if info.get('previews'):
            for i, (item, ftype) in enumerate(info['previews']):
                if ftype == 'photo':
                    tk.Label(preview_frame, image=item, bg=ModernTheme.BG_TERTIARY).pack(
                        side="left", padx=5)
                elif ftype == 'video':
                    vid_frame = ttk.Frame(
                        preview_frame, style='TFrame', padding=5)
                    tk.Label(vid_frame, image=self.video_icon,
                             bg=ModernTheme.BG_SECONDARY).pack()
                    tk.Label(vid_frame, text=os.path.basename(item), font=(
                        'Arial', 8), foreground=ModernTheme.FG_SECONDARY, bg=ModernTheme.BG_SECONDARY).pack()
                    vid_frame.pack(side="left", padx=5)
                if i == 0 and len(info['previews']) > 1:
                    ttk.Label(preview_frame, text="➜", font=(
                        'Arial', 20), foreground=ModernTheme.FG_SECONDARY).pack(side="left", padx=15)
                has_content = True
        if not has_content:
            preview_frame.grid_remove()

        # Destination folder
        pasta_frame = ttk.Frame(data_frame, style='TFrame')
        pasta_frame.grid(row=2, column=0, columnspan=2,
                         sticky="ew", pady=(8, 5))
        pasta_frame.columnconfigure(1, weight=1)
        ttk.Label(pasta_frame, text="📁 Pasta Destino:", font=(
            'Arial', 11, 'bold')).grid(row=0, column=0, sticky="w", padx=(0, 10))
        pasta_var = tk.StringVar(value=os.path.join(self.destino_base, data))
        ttk.Entry(pasta_frame, textvariable=pasta_var).grid(
            row=0, column=1, sticky="ew", padx=(0, 10))
        self.pasta_entries[data] = pasta_var
        ModernTheme.create_styled_button(pasta_frame, "Escolher", lambda d=data: self.escolher_pasta(
            d)).grid(row=0, column=2, sticky="e")

        # Renaming section
        rename_section_frame = ttk.Frame(data_frame, style='TFrame')
        rename_section_frame.grid(
            row=3, column=0, columnspan=2, sticky="ew", pady=(5, 0))
        renomear_var = tk.BooleanVar(value=False)
        self.renomear_vars[data] = renomear_var
        ttk.Checkbutton(rename_section_frame, text="🏷️ Renomear arquivos", variable=renomear_var,
                        command=lambda d=data: self.toggle_renomear(d)).grid(row=0, column=0, sticky="w")

        # Prefix and options
        prefix_frame = ttk.Frame(data_frame, style='TFrame')
        prefix_frame.grid(row=4, column=0, columnspan=2,
                          sticky="ew", padx=20, pady=5)
        prefix_frame.columnconfigure(1, weight=1)

        ttk.Label(prefix_frame, text="Prefixo:", foreground=ModernTheme.FG_SECONDARY).grid(
            row=0, column=0, sticky="w", padx=(0, 10))
        prefixo_var = tk.StringVar()
        prefixo_entry = ttk.Entry(
            prefix_frame, textvariable=prefixo_var, state='disabled')
        prefixo_entry.grid(row=0, column=1, sticky="ew", padx=(0, 15))
        self.prefixo_entries[data] = prefixo_var

        manter_num_var = tk.BooleanVar(value=True)
        self.manter_numeracao_vars[data] = manter_num_var
        cb_manter = ttk.Checkbutton(prefix_frame, text="Manter numeração original", variable=manter_num_var,
                                    state='disabled', command=lambda d=data: self.atualizar_exemplo(d))
        cb_manter.grid(row=0, column=2, sticky="w")

        # Example
        exemplo_frame = ttk.Frame(data_frame, style='TFrame')
        exemplo_frame.grid(row=5, column=0, columnspan=2,
                           sticky="ew", padx=20, pady=(0, 10))
        ttk.Label(exemplo_frame, text="Exemplo:", font=('Arial', 10, 'bold'),
                  foreground=ModernTheme.FG_SECONDARY).pack(side="left", padx=(0, 10))
        exemplo_label = ttk.Label(exemplo_frame, text="", font=(
            'Arial', 10, 'italic'), foreground=ModernTheme.ACCENT)
        exemplo_label.pack(side="left")

        self.exemplo_labels[data] = exemplo_label
        self.rename_widgets_by_date[data].extend(
            [prefixo_entry, cb_manter, exemplo_label])
        prefixo_var.trace_add('write', lambda *args,
                              d=data: self.atualizar_exemplo(d))
        self.toggle_renomear(data)

    def escolher_pasta(self, data):
        pasta = filedialog.askdirectory(
            title=f"Pasta para {formatar_data_br(data)}")
        if pasta:
            self.pasta_entries[data].set(pasta)

    def toggle_renomear(self, data):
        state = 'normal' if self.renomear_vars[data].get() else 'disabled'
        for widget in self.rename_widgets_by_date[data]:
            if isinstance(widget, (ttk.Entry, ttk.Checkbutton)):
                widget.config(state=state)
        self.atualizar_exemplo(data)

    def atualizar_exemplo(self, data):
        if not self.renomear_vars[data].get():
            self.exemplo_labels[data].config(text="Nomes originais mantidos")
            return

        prefixo = self.prefixo_entries[data].get().strip()
        manter_original = self.manter_numeracao_vars[data].get()

        arquivos = self.datas_info[data]['arquivos']
        if not arquivos:
            self.exemplo_labels[data].config(text="Sem arquivos para exemplo")
            return

        arquivo_exemplo = os.path.basename(next(
            (f for f in arquivos if tipo_arquivo(f) in ['FOTOS', 'VIDEOS']), arquivos[0]))
        nome_original, ext = os.path.splitext(arquivo_exemplo)
        ext = ext.lower()

        match = re.search(r'(\d+)', nome_original)
        num_part = match.group(1).zfill(
            4) if manter_original and match else "0001"

        if prefixo:
            exemplo = f"{prefixo}_{num_part}{ext}"
        else:
            exemplo = f"{nome_original if manter_original and match else f'arquivo_{num_part}'}{
                ext}"

        self.exemplo_labels[data].config(text=exemplo)

    def selecionar_todas(self):
        for var in self.checkboxes.values():
            var.set(True)

    def desmarcar_todas(self):
        for var in self.checkboxes.values():
            var.set(False)

    def confirmar(self):
        self.result = {}
        for data, var in self.checkboxes.items():
            if var.get():
                pasta_destino = self.pasta_entries[data].get().strip()
                if not pasta_destino:
                    messagebox.showerror(
                        "Erro de Configuração", f"A pasta de destino para {formatar_data_br(data)} não pode estar vazia.")
                    return
                self.result[data] = {
                    'pasta': pasta_destino,
                    'prefixo': self.prefixo_entries[data].get().strip() if self.renomear_vars[data].get() else None,
                    'renomear': self.renomear_vars[data].get(),
                    'manter_numeracao': self.manter_numeracao_vars[data].get(),
                    'arquivos': self.datas_info[data]['arquivos']
                }
        if not self.result:
            messagebox.showwarning(
                "Seleção Vazia", "Nenhuma data selecionada para backup. Selecione ao menos uma data ou Cancele.")
            return
        self.destroy()

    def cancelar(self):
        self.result = None
        self.destroy()

# --------------------------- POPUP DE RESUMO FINAL ---------------------------


class PopupResumoFinal(tk.Toplevel):
    def __init__(self, parent, resumo_dados):
        super().__init__(parent)
        self.title("Resumo Final do Backup")
        self.geometry("800x600")
        self.configure(bg=ModernTheme.BG_PRIMARY)
        self.minsize(700, 550)

        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

        main_frame = ttk.Frame(self, style='TFrame', padding=20)
        main_frame.pack(fill="both", expand=True)
        main_frame.rowconfigure(2, weight=1)  # Allow log text to expand
        main_frame.columnconfigure(0, weight=1)

        ttk.Label(main_frame, text="🎉 Backup Finalizado com Sucesso!", font=(
            'Arial', 20, 'bold'), foreground=ModernTheme.SUCCESS).grid(row=0, column=0, pady=(0, 20))

        # Stats
        stats_frame = ttk.Frame(
            main_frame, style='TFrame', relief=tk.RAISED, borderwidth=1, padding=15)
        stats_frame.grid(row=1, column=0, sticky="ew", pady=(0, 20))
        stats_data = [("📁 Arquivos Copiados:", f"{resumo_dados.get('arquivos_copiados', 0)}"),
                      ("💾 Tamanho Total:", resumo_dados.get('tamanho_total', '0 B')),
                      ("⏱️ Tempo Total:",
                       f"{resumo_dados.get('tempo_total', 0)}s"),
                      ("❌ Erros:", f"{resumo_dados.get('erros', 0)}")]
        for i, (label, value) in enumerate(stats_data):
            col = i % 2
            row = i // 2
            stats_frame.columnconfigure(col, weight=1)
            stat_frame = ttk.Frame(stats_frame, style='TFrame')
            stat_frame.grid(row=row, column=col, sticky="w", padx=20, pady=5)
            ttk.Label(stat_frame, text=label,
                      foreground=ModernTheme.FG_SECONDARY).pack(side="left")
            ttk.Label(stat_frame, text=value, font=(
                'Arial', 11, 'bold')).pack(side="left", padx=10)

        # Reminders
        lembrete_frame = ttk.Frame(
            main_frame, style='TFrame', relief=tk.RAISED, borderwidth=1, padding=(15, 5))
        lembrete_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 20))
        lembrete_frame.rowconfigure(1, weight=1)
        lembrete_frame.columnconfigure(0, weight=1)

        ttk.Label(lembrete_frame, text="💡 Lembretes Importantes", font=('Arial', 14, 'bold'),
                  foreground=ModernTheme.WARNING).grid(row=0, column=0, sticky="w", pady=(5, 10))

        lembretes_text = """🧠 LEMBRETE: Salve agora na nuvem pra não dar ruim depois! ☁️🔥

🛡️ SEGURANÇA:
• Este programa NÃO altera arquivos no cartão.
• Apenas leitura e cópia são realizadas.
• Seus arquivos originais estão seguros.

☁️ BACKUP NA NUVEM:
• Faça upload para Google Drive, iCloud, Dropbox, etc.
• Redundância é fundamental!

⚡ PRÓXIMOS PASSOS:
1. Verifique os arquivos copiados.
2. Faça backup na nuvem AGORA.
3. Formate o cartão apenas após confirmar tudo."""

        lembrete_text_widget = scrolledtext.ScrolledText(lembrete_frame, bg=ModernTheme.BG_TERTIARY, fg=ModernTheme.FG_PRIMARY, font=(
            'Consolas', 10), wrap=tk.WORD, relief=tk.FLAT, bd=0, height=10)
        lembrete_text_widget.grid(row=1, column=0, sticky="nsew", pady=(0, 15))
        lembrete_text_widget.insert("1.0", lembretes_text)
        lembrete_text_widget.config(state="disabled")

        # Buttons
        btn_frame = ttk.Frame(main_frame, style='TFrame')
        btn_frame.grid(row=3, column=0, sticky="ew")
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)

        ModernTheme.create_styled_button(btn_frame, "📂 Abrir Pasta Destino", lambda: abrir_pasta(
            resumo_dados.get('pasta_destino')), "Modern.TButton").grid(row=0, column=0, sticky="e", padx=10)
        ModernTheme.create_styled_button(btn_frame, "✅ Entendi!", self.destroy, "Success.TButton").grid(
            row=0, column=1, sticky="w", padx=10)

# --------------------------- POPUP DE PROGRESSO ---------------------------


class PopupProgresso(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Progresso do Backup")
        self.geometry("600x400")
        self.configure(bg=ModernTheme.BG_PRIMARY)
        self.resizable(False, False)

        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", lambda: None)

        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

        main_frame = ttk.Frame(self, style='TFrame', padding=20)
        main_frame.pack(fill="both", expand=True)

        self.titulo = ttk.Label(
            main_frame, text="🚀 Realizando Backup...", font=('Arial', 18, 'bold'))
        self.titulo.pack(pady=(0, 20))

        self.info_label = ttk.Label(main_frame, text="Preparando...", font=(
            'Arial', 11), foreground=ModernTheme.FG_SECONDARY, wraplength=550)
        self.info_label.pack(pady=5)

        self.progress = ttk.Progressbar(
            main_frame, length=500, mode='determinate', style='Modern.Horizontal.TProgressbar')
        self.progress.pack(pady=10)

        self.percent_label = ttk.Label(main_frame, text="0%", font=(
            'Arial', 24, 'bold'), foreground=ModernTheme.ACCENT)
        self.percent_label.pack(pady=5)

        self.status_text = scrolledtext.ScrolledText(main_frame, height=8, bg=ModernTheme.BG_SECONDARY, fg=ModernTheme.FG_SECONDARY, font=(
            'Consolas', 9), wrap=tk.WORD, relief=tk.FLAT, bd=0)
        self.status_text.pack(fill="both", expand=True, pady=10)

        self.btn_frame = ttk.Frame(main_frame, style='TFrame')
        self.btn_frame.pack(fill="x", pady=(10, 0))

    def atualizar(self, progresso, info, status):
        progresso = max(0, min(100, progresso))
        self.progress['value'] = progresso
        self.percent_label.config(text=f"{int(progresso)}%")
        self.info_label.config(text=info)
        if status:
            self.status_text.insert(tk.END, status + "\n")
            self.status_text.see(tk.END)

    def finalizar(self, sucesso=True, resumo_dados=None):
        if sucesso:
            self.titulo.config(text="✅ Backup Concluído!",
                               foreground=ModernTheme.SUCCESS)
            self.percent_label.config(
                text="100%", foreground=ModernTheme.SUCCESS)

            btn_inner_frame = ttk.Frame(self.btn_frame)
            btn_inner_frame.pack()
            ModernTheme.create_styled_button(btn_inner_frame, "Ver Resumo Final", lambda: self.mostrar_resumo_final(
                resumo_dados), "Success.TButton").pack(side="left", padx=5)
            ModernTheme.create_styled_button(
                btn_inner_frame, "Fechar", self.destroy, "Modern.TButton").pack(side="left", padx=5)
        else:
            self.titulo.config(text="❌ Erro no Backup",
                               foreground=ModernTheme.ERROR)
            ModernTheme.create_styled_button(
                self.btn_frame, "Fechar", self.destroy, "Error.TButton").pack()

    def mostrar_resumo_final(self, resumo_dados):
        self.destroy()
        if resumo_dados:
            PopupResumoFinal(self.winfo_toplevel(), resumo_dados)

# --------------------------- THREAD DE BACKUP ---------------------------


def copiar_arquivos(app, mapa_datas, popup_progresso):
    copiados, erros, total_tamanho, pastas_criadas = 0, 0, 0, set()
    tempo_inicio = time.time()
    linhas_log = []

    total_arquivos_a_copiar = sum(len(d['arquivos'])
                                  for d in mapa_datas.values())
    if total_arquivos_a_copiar == 0:
        popup_progresso.finalizar(sucesso=True, resumo_dados={
                                  'arquivos_copiados': 0, 'erros': 0, 'tamanho_total': '0 B', 'pastas_criadas': 0, 'tempo_total': 0, 'pasta_destino': None})
        return

    file_counters = defaultdict(lambda: 1)
    for data, dados in mapa_datas.items():
        arquivos_ordenados = sorted(
            dados['arquivos'], key=lambda x: (os.path.getmtime(x), x))

        popup_progresso.atualizar(int((copiados / total_arquivos_a_copiar) * 100),
                                  f"Processando data: {formatar_data_br(data)}", f"\n📅 Iniciando backup de {formatar_data_br(data)} ({len(arquivos_ordenados)} arquivos)")

        for arq in arquivos_ordenados:
            try:
                tipo = tipo_arquivo(arq)
                destino_subpasta = os.path.join(dados['pasta'], tipo)
                if destino_subpasta not in pastas_criadas:
                    os.makedirs(destino_subpasta, exist_ok=True)
                    pastas_criadas.add(destino_subpasta)

                nome_original, ext = os.path.splitext(os.path.basename(arq))
                ext = ext.lower()

                if dados.get('renomear') and dados.get('prefixo'):
                    prefixo = dados['prefixo']
                    if dados['manter_numeracao']:
                        match = re.search(r'(\d+)', nome_original)
                        num_part = match.group(
                            1) if match else f"{file_counters[data]:04d}"
                    else:
                        num_part = f"{file_counters[data]:04d}"
                    novo_nome = f"{prefixo}_{num_part}{ext}"
                else:
                    novo_nome = os.path.basename(arq)

                destino_final = os.path.join(destino_subpasta, novo_nome)

                status = ""
                if os.path.exists(destino_final) and os.path.getsize(destino_final) == os.path.getsize(arq):
                    status = "⏭️ Ignorado (idêntico)"
                else:
                    shutil.copy2(arq, destino_final)
                    tamanho_copiado = os.path.getsize(destino_final)
                    if tamanho_copiado == os.path.getsize(arq):
                        status = "✅ Copiado"
                        total_tamanho += tamanho_copiado
                    else:
                        status = "❌ Erro (tamanho diferente)"
                        erros += 1

            except Exception as e:
                status = f"❌ Erro: {e}"
                erros += 1

            copiados += 1
            progresso_percent = (copiados / total_arquivos_a_copiar) * 100
            popup_progresso.atualizar(
                progresso_percent, f"Copiando: {os.path.basename(arq)}", f"{status} -> {novo_nome}")

            log_msg = f"{os.path.basename(arq)} -> {tipo} -> {novo_nome}: {status}"
            linhas_log.append(log_msg)
            file_counters[data] += 1

    popup_progresso.atualizar(100, "Finalizando...", "\n🔍 Gerando log...")
    time.sleep(1)

    tempo_total = int(time.time() - tempo_inicio)
    resumo_texto = (f"📊 RESUMO DO BACKUP\n{'='*40}\n"
                    f"✅ Arquivos copiados: {copiados - erros}\n"
                    f"❌ Erros: {erros}\n"
                    f"💾 Tamanho total: {formatar_tamanho(total_tamanho)}\n"
                    f"⏱️ Tempo total: {tempo_total} segundos\n{'='*40}")

    destino_log_base = list(mapa_datas.values())[
        0]['pasta'] if mapa_datas else app.destino_var.get()
    log_file_path = os.path.join(
        destino_log_base, f"backup_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    try:
        with open(log_file_path, 'w', encoding='utf-8') as f:
            f.write(
                f"BACKUP LOG - {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write(
                f"Origem: {app.cartao_var.get()}\nDestino: {app.destino_var.get()}\n\n")
            f.write(resumo_texto + "\n\n" + "="*40 +
                    "\nDETALHES\n" + "="*40 + "\n\n")
            f.write("\n".join(linhas_log))
    except Exception as e:
        app.msg_queue.put(('log', f"ERRO: Não foi possível salvar o log: {e}"))

    app.msg_queue.put(('log', resumo_texto))
    app.msg_queue.put(('fim_backup', True))

    resumo_dados = {'arquivos_copiados': copiados - erros, 'erros': erros,
                    'tamanho_total': formatar_tamanho(total_tamanho),
                    'tempo_total': tempo_total, 'pasta_destino': destino_log_base}

    popup_progresso.finalizar(sucesso=(erros == 0), resumo_dados=resumo_dados)

# --------------------------- APLICAÇÃO PRINCIPAL ---------------------------


class BackupCartaoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Backup Cartão Pro v6.1")
        self.geometry("900x650")
        self.configure(bg=ModernTheme.BG_PRIMARY)
        ModernTheme.configure_styles()
        self.minsize(800, 600)

        self.msg_queue = ThreadSafeQueue()
        self.backup_em_andamento = False
        self.datas_info = {}
        self.video_icon = self.create_video_icon()

        # Main layout
        main_frame = ttk.Frame(self, style='TFrame', padding=10)
        main_frame.pack(fill="both", expand=True)
        main_frame.rowconfigure(1, weight=1)
        main_frame.columnconfigure(0, weight=1)

        self.create_header(main_frame)
        self.notebook = self.create_notebook(main_frame)
        self.create_footer(main_frame)

        self.after(100, self.processar_mensagens)

    def create_video_icon(self):
        # Create a simple placeholder image for videos
        if not PIL_AVAILABLE:
            return None
        try:
            img = Image.new('RGBA', (100, 100), ModernTheme.BG_TERTIARY)
            # You can draw on this image using ImageDraw if you want more detail
            return ImageTk.PhotoImage(img)
        except:
            return None

    def create_header(self, parent):
        header_frame = ttk.Frame(parent, style='TFrame')
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ttk.Label(header_frame, text="🚀 Backup de Mídia Profissional",
                  font=('Arial', 24, 'bold')).pack()

    def create_notebook(self, parent):
        notebook = ttk.Notebook(parent, style="TNotebook")
        notebook.grid(row=1, column=0, sticky="nsew")

        self.tab1 = self.create_config_tab(notebook)
        self.tab2 = self.create_analysis_tab(notebook)
        self.tab3 = self.create_log_tab(notebook)

        notebook.add(self.tab1, text=" 1. Configuração ")
        notebook.add(self.tab2, text=" 2. Análise ")
        notebook.add(self.tab3, text=" 3. Log ")

        return notebook

    def create_config_tab(self, parent_notebook):
        tab = ttk.Frame(parent_notebook, style='TFrame', padding=20)
        tab.columnconfigure(1, weight=1)

        # Card
        ttk.Label(tab, text="Origem (Cartão SD):", font=('Arial', 12, 'bold')).grid(
            row=0, column=0, sticky="w", padx=(0, 15), pady=8)
        self.cartao_var = tk.StringVar()
        self.cartao_entry = ttk.Entry(tab, textvariable=self.cartao_var)
        self.cartao_entry.grid(
            row=0, column=1, sticky="ew", padx=(0, 10), pady=8)
        ModernTheme.create_styled_button(
            tab, "Procurar", self.escolher_cartao).grid(row=0, column=2)

        # Destination
        ttk.Label(tab, text="Destino (Backup):", font=('Arial', 12, 'bold')).grid(
            row=1, column=0, sticky="w", padx=(0, 15), pady=8)
        self.destino_var = tk.StringVar()
        self.destino_entry = ttk.Entry(tab, textvariable=self.destino_var)
        self.destino_entry.grid(
            row=1, column=1, sticky="ew", padx=(0, 10), pady=8)
        ModernTheme.create_styled_button(
            tab, "Procurar", self.escolher_destino).grid(row=1, column=2)

        # Options
        options_frame = ttk.Frame(tab, style='TFrame')
        options_frame.grid(row=2, column=0, columnspan=3,
                           sticky='w', pady=(20, 0))
        self.xml_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Incluir arquivos de metadados (XMP/XML)",
                        variable=self.xml_var).pack(anchor="w")

        # Action Buttons
        action_frame = ttk.Frame(tab)
        action_frame.grid(row=3, column=0, columnspan=3, pady=(40, 20))
        self.analise_btn = ModernTheme.create_styled_button(
            action_frame, "Analisar Cartão", self.analisar_cartao, "Warning.TButton", width=20)
        self.analise_btn.pack(side="left", padx=10)

        self.backup_btn = ModernTheme.create_styled_button(
            action_frame, "Iniciar Backup", self.iniciar_backup, "Success.TButton", width=20)
        self.backup_btn.pack(side="left", padx=10)
        self.backup_btn.config(state="disabled")

        return tab

    def create_analysis_tab(self, parent_notebook):
        tab = ttk.Frame(parent_notebook, style='TFrame', padding=20)
        tab.rowconfigure(0, weight=1)
        tab.columnconfigure(0, weight=1)
        self.analise_text = scrolledtext.ScrolledText(
            tab, wrap=tk.WORD, bg=ModernTheme.BG_TERTIARY, fg=ModernTheme.FG_PRIMARY, font=('Consolas', 10), relief=tk.FLAT, bd=0)
        self.analise_text.grid(row=0, column=0, sticky="nsew")
        self.analise_text.insert("1.0", "Aguardando análise do cartão...")
        self.analise_text.config(state="disabled")
        return tab

    def create_log_tab(self, parent_notebook):
        tab = ttk.Frame(parent_notebook, style='TFrame', padding=20)
        tab.rowconfigure(0, weight=1)
        tab.columnconfigure(0, weight=1)
        self.resumo_text = scrolledtext.ScrolledText(
            tab, wrap=tk.WORD, bg=ModernTheme.BG_TERTIARY, fg=ModernTheme.FG_PRIMARY, font=('Consolas', 10), relief=tk.FLAT, bd=0)
        self.resumo_text.grid(row=0, column=0, sticky="nsew")
        self.resumo_text.insert("1.0", "Aguardando operações...")
        self.resumo_text.config(state="disabled")
        return tab

    def create_footer(self, parent):
        footer_frame = ttk.Frame(parent, style='TFrame')
        footer_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))

        ModernTheme.create_styled_button(
            footer_frame, "🔄 Novo Cartão", self.novo_cartao, "Modern.TButton").pack(side="left", padx=10)
        ttk.Label(footer_frame, text="NASCO COMPANY © 2024",
                  foreground=ModernTheme.FG_SECONDARY).pack(side="left", expand=True)
        ModernTheme.create_styled_button(
            footer_frame, "❌ Sair", self.sair_aplicacao, "Error.TButton").pack(side="right", padx=10)

    def processar_mensagens(self):
        for tipo, conteudo in self.msg_queue.get_all():
            if tipo == 'log':
                self.adicionar_log(conteudo)
            elif tipo == 'fim_backup':
                self.backup_em_andamento = False
                self.backup_btn.config(
                    state="normal" if self.datas_info else "disabled")
                self.analise_btn.config(state="normal")
        self.after(100, self.processar_mensagens)

    def escolher_cartao(self):
        if self.backup_em_andamento:
            return
        pasta = filedialog.askdirectory(title="Selecione a pasta do Cartão SD")
        if pasta:
            self.cartao_var.set(pasta)

    def escolher_destino(self):
        if self.backup_em_andamento:
            return
        default_path = os.path.join(os.path.expanduser(
            "~"), "Desktop", f"Backup_Cartao_{datetime.now().strftime('%Y%m%d')}")
        pasta = filedialog.askdirectory(
            title="Selecione a Pasta de Destino", initialdir=default_path)
        if pasta:
            self.destino_var.set(pasta)

    def adicionar_log(self, mensagem):
        self.resumo_text.config(state="normal")
        if "RESUMO DO BACKUP" in mensagem:
            self.resumo_text.delete("1.0", tk.END)
        self.resumo_text.insert(tk.END, mensagem + "\n\n")
        self.resumo_text.see(tk.END)
        self.resumo_text.config(state="disabled")
        self.notebook.select(self.tab3)

    def analisar_cartao(self):
        if self.backup_em_andamento:
            return
        caminho = self.cartao_var.get()
        if not os.path.isdir(caminho):
            messagebox.showerror(
                "Erro", "Selecione um diretório de origem válido!")
            return

        self.analise_text.config(state="normal")
        self.analise_text.delete("1.0", tk.END)
        self.analise_text.insert(
            "1.0", "🔍 Analisando cartão... Isso pode levar um momento.\n")
        self.analise_text.config(state="disabled")
        self.notebook.select(self.tab2)
        self.update_idletasks()

        self.backup_btn.config(state="disabled")
        self.analise_btn.config(state="disabled")

        threading.Thread(target=self._run_analysis_in_thread, args=(
            caminho, self.xml_var.get()), daemon=True).start()

    def _run_analysis_in_thread(self, caminho, incluir_xml):
        try:
            fotos, videos, xmls = listar_arquivos(caminho, incluir_xml)
            all_files = fotos + videos + xmls

            arquivos_por_data = defaultdict(
                lambda: {'arquivos': [], 'tipos': defaultdict(list)})
            for arquivo in all_files:
                data = extrair_data_arquivo(arquivo)
                arquivos_por_data[data]['arquivos'].append(arquivo)
                arquivos_por_data[data]['tipos'][tipo_arquivo(
                    arquivo)].append(arquivo)

            self.datas_info = {}
            for data, info in arquivos_por_data.items():
                fotos_data = sorted(info['tipos'].get(
                    'FOTOS', []), key=os.path.getmtime)
                videos_data = sorted(info['tipos'].get(
                    'VIDEOS', []), key=os.path.getmtime)

                previews = []
                if fotos_data:
                    previews.append((gerar_thumbnail(fotos_data[0]), 'photo'))
                    if len(fotos_data) > 1:
                        previews.append(
                            (gerar_thumbnail(fotos_data[-1]), 'photo'))
                elif videos_data:  # If no photos, show video placeholder
                    previews.append((videos_data[0], 'video'))

                self.datas_info[data] = {'arquivos': info['arquivos'], 'tamanho': tamanho_total_arquivos(
                    info['arquivos']), 'previews': previews, 'tipos': info['tipos']}

            self.after(0, self._update_analysis_ui, fotos, videos, xmls)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror(
                "Erro na Análise", f"Erro ao analisar o cartão:\n{e}"))
            self.after(0, lambda: self.analise_btn.config(state="normal"))

    def _update_analysis_ui(self, fotos, videos, xmls):
        self.analise_text.config(state="normal")
        self.analise_text.delete("1.0", tk.END)

        total_arquivos = len(fotos) + len(videos) + len(xmls)
        total_tamanho = tamanho_total_arquivos(fotos + videos + xmls)

        analise = f"📊 ANÁLISE DO CARTÃO\n{'='*50}\n\n"
        analise += f"📁 Arquivos Encontrados: {total_arquivos}\n"
        analise += f"💾 Tamanho Total: {formatar_tamanho(total_tamanho)}\n\n"
        analise += f"📷 Fotos: {len(fotos)} ({formatar_tamanho(tamanho_total_arquivos(fotos))})\n"
        analise += f"🎥 Vídeos: {len(videos)} ({formatar_tamanho(tamanho_total_arquivos(videos))})\n"
        analise += f"📄 Metadados: {len(xmls)} ({formatar_tamanho(tamanho_total_arquivos(xmls))})\n\n"
        analise += f"📅 Detalhes por Data ({len(self.datas_info)} dias):\n{'-'*40}\n"

        for data in sorted(self.datas_info.keys()):
            info = self.datas_info[data]
            analise += f"• {formatar_data_br(data)}: {len(info['arquivos'])} arquivos ({formatar_tamanho(info['tamanho'])})\n"

        self.analise_text.insert("1.0", analise)
        self.analise_text.config(state="disabled")

        self.backup_btn.config(
            state="normal" if total_arquivos > 0 else "disabled")
        self.analise_btn.config(state="normal")
        self.notebook.select(self.tab2)

    def iniciar_backup(self):
        if self.backup_em_andamento:
            return
        if not self.cartao_var.get() or not self.destino_var.get():
            messagebox.showerror(
                "Erro", "As pastas de Origem e Destino devem ser selecionadas.")
            return
        if not self.datas_info:
            messagebox.showwarning("Atenção", "Analise o cartão primeiro!")
            return

        total_necessario = sum(info['tamanho']
                               for info in self.datas_info.values())
        _, espaco_livre = checar_espaco(self.destino_var.get())
        if espaco_livre < total_necessario * 1.05:
            if not messagebox.askyesno("Espaço Insuficiente", f"Espaço necessário: {formatar_tamanho(total_necessario)}\nEspaço livre: {formatar_tamanho(espaco_livre)}\n\nDeseja continuar mesmo assim?"):
                return

        popup = PopupSelecaoDatas(
            self, self.datas_info, self.destino_var.get(), self.video_icon)
        self.wait_window(popup)

        if popup.result:
            self.backup_em_andamento = True
            self.backup_btn.config(state="disabled")
            self.analise_btn.config(state="disabled")
            self.adicionar_log("🚀 Backup iniciado...")

            popup_progresso = PopupProgresso(self)
            threading.Thread(target=copiar_arquivos, args=(
                self, popup.result, popup_progresso), daemon=True).start()

    def novo_cartao(self):
        if self.backup_em_andamento:
            messagebox.showwarning(
                "Atenção", "Aguarde o backup em andamento terminar!")
            return
        self.cartao_var.set("")
        self.destino_var.set("")
        self.xml_var.set(True)
        self.datas_info = {}
        self.backup_btn.config(state="disabled")

        for tab, text in [(self.tab2, "Aguardando análise..."), (self.tab3, "Aguardando operações...")]:
            widget = tab.winfo_children()[0]
            widget.config(state="normal")
            widget.delete("1.0", tk.END)
            widget.insert("1.0", text)
            widget.config(state="disabled")

        self.notebook.select(self.tab1)
        messagebox.showinfo(
            "Pronto", "Configurações limpas. Pronto para um novo cartão.")

    def sair_aplicacao(self):
        if self.backup_em_andamento and not messagebox.askyesno("Backup em Andamento", "Um backup está em andamento. Deseja realmente sair?"):
            return
        self.quit()


# --------------------------- MAIN ---------------------------
if __name__ == "__main__":
    app = BackupCartaoApp()
    app.mainloop()
