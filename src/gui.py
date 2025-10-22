# src/gui.py

import customtkinter as ctk
from customtkinter import filedialog
import threading
import os
import sys
from datetime import datetime
from tkinter import messagebox
from tkinterweb import HtmlFrame

from src.core.orchestrator import run_analysis_and_generate_artifacts, generate_specification_document
from src.services.transcription_service import TranscriptionService
from src.config import TEMPLATES_PATH

# --- BASE DO TEMPLATE COM DOIS PLACEHOLDERS ---
MARKMAP_TEMPLATE_BASE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>body {{ margin: 0; padding: 0; background-color: #2B2B2B; }}</style>
    {js_library}
</head>
<body>
    <div class="markmap" style="width: 100%; height: 100vh;">
        <script type="text/template">
---
markmap:
  colorFreezeLevel: 2
  maxWidth: 300
---
{markdown_content}
        </script>
    </div>
</body>
</html>
"""

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Business Analyst Copilot")
        self.geometry("1200x850")

        # Variáveis de estado
        self.current_mind_map_md = ""
        self.current_spec_content = {}
        self.is_analysis_done = False
        
        # Carrega a biblioteca JS localmente
        self.load_local_js()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- FRAME DE SETUP ---
        setup_frame = ctk.CTkFrame(self)
        setup_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        setup_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(setup_frame, text="Nome Cliente:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.client_name_entry = ctk.CTkEntry(setup_frame, placeholder_text="Nome do cliente...")
        self.client_name_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(setup_frame, text="Docs. Apoio:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.doc_list_label = ctk.CTkLabel(setup_frame, text="Nenhum documento adicionado...", anchor="w")
        self.doc_list_label.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        self.add_doc_button = ctk.CTkButton(setup_frame, text="Adicionar Docs", width=120, command=self.add_documents)
        self.add_doc_button.grid(row=1, column=2, padx=10, pady=5)
        self.document_paths = []

        # --- FRAME PRINCIPAL (TRANSCRIÇÃO E RESULTADOS) ---
        main_frame = ctk.CTkFrame(self)
        main_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)

        # --- Controles de Transcrição e Geração ---
        controls_frame = ctk.CTkFrame(main_frame)
        controls_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        controls_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.transcription_start_button = ctk.CTkButton(controls_frame, text="▶️ Iniciar Transcrição", command=self.start_transcription)
        self.transcription_start_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.transcription_stop_button = ctk.CTkButton(controls_frame, text="⏹️ Parar Transcrição", command=self.stop_transcription, state="disabled")
        self.transcription_stop_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.analysis_button = ctk.CTkButton(controls_frame, text="🚀 Gerar Análise e Artefatos", command=self.start_analysis_thread, height=40)
        self.analysis_button.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        # --- TABS DE RESULTADO ---
        self.tab_view = ctk.CTkTabview(main_frame)
        self.tab_view.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.tab_view.add("Transcrição")
        self.tab_view.add("Mapa Mental")
        self.tab_view.add("Especificação Funcional")

        # --- ABA DE TRANSCRIÇÃO ---
        self.transcription_textbox = ctk.CTkTextbox(self.tab_view.tab("Transcrição"), wrap="word", font=("Calibri", 16))
        self.transcription_textbox.pack(expand=True, fill="both", padx=5, pady=5)

        # --- ABA DE MAPA MENTAL ---
        mind_map_tab = self.tab_view.tab("Mapa Mental")
        mind_map_tab.grid_columnconfigure(1, weight=3)
        mind_map_tab.grid_columnconfigure(0, weight=1)
        mind_map_tab.grid_rowconfigure(0, weight=1)

        editor_frame = ctk.CTkFrame(mind_map_tab)
        editor_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        editor_frame.grid_rowconfigure(1, weight=1)
        editor_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(editor_frame, text="Editor de Markdown").grid(row=0, column=0, padx=5, pady=5)
        self.mind_map_editor = ctk.CTkTextbox(editor_frame, wrap="word", font=("Consolas", 14))
        self.mind_map_editor.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        self.mind_map_editor.bind("<KeyRelease>", self.update_mind_map_view)
        
        mind_map_controls = ctk.CTkFrame(editor_frame)
        mind_map_controls.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        mind_map_controls.grid_columnconfigure((0,1), weight=1)
        self.save_map_html_button = ctk.CTkButton(mind_map_controls, text="Salvar HTML", command=self.save_mind_map_html, state="disabled")
        self.save_map_html_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        viewer_frame = ctk.CTkFrame(mind_map_tab, fg_color="#2B2B2B")
        viewer_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        self.mind_map_viewer = HtmlFrame(viewer_frame, messages_enabled=False)
        self.mind_map_viewer.pack(expand=True, fill="both")

        # --- ABA DE ESPECIFICAÇÃO ---
        spec_tab = self.tab_view.tab("Especificação Funcional")
        spec_tab.grid_columnconfigure(0, weight=1)
        spec_tab.grid_rowconfigure(0, weight=1)
        self.spec_textbox = ctk.CTkTextbox(spec_tab, wrap="word", font=("Calibri", 15), state="disabled")
        self.spec_textbox.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        self.save_spec_button = ctk.CTkButton(spec_tab, text="Salvar Especificação (.txt)", command=self.save_specification_file, state="disabled")
        self.save_spec_button.grid(row=1, column=0, padx=10, pady=10, sticky="e")

        # --- LOG ---
        self.progress_log_textbox = ctk.CTkTextbox(main_frame, height=100, state="disabled", wrap="word", font=("Consolas", 12))
        self.progress_log_textbox.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

        # --- SERVIÇO DE TRANSCRIÇÃO (MOVIDO PARA O FIM) ---
        # Garante que todos os widgets e métodos da UI existam antes de inicializar o serviço
        self.transcription_service = TranscriptionService(on_transcription_update=self.update_transcription_textbox)
        self.log_progress("🚀 Sistema pronto. Inicie a transcrição ou adicione documentos.")

    def load_local_js(self):
        js_lib_path = os.path.join(TEMPLATES_PATH, "js", "markmap-autoloader.min.js")
        try:
            with open(js_lib_path, "r", encoding="utf-8") as f:
                js_content = f.read()
            self.markmap_js_lib = f"<script>{js_content}</script>"
        except FileNotFoundError:
            self.log_progress(f"AVISO: Biblioteca local do mapa mental não encontrada. Usando CDN da internet.")
            self.markmap_js_lib = '<script src="https://cdn.jsdelivr.net/npm/markmap-autoloader@0.15"></script>'

    def log_progress(self, message):
        self.after(0, self._append_to_log, message)

    def _append_to_log(self, message):
        self.progress_log_textbox.configure(state="normal")
        self.progress_log_textbox.insert("end", f"[{datetime.now().strftime('%H:%M:%S')}] {message}\n")
        self.progress_log_textbox.see("end")
        self.progress_log_textbox.configure(state="disabled")

    def add_documents(self):
        filepaths = filedialog.askopenfilenames(title="Selecione documentos de apoio")
        if filepaths:
            self.document_paths.extend(filepaths)
            self.doc_list_label.configure(text=f"{len(self.document_paths)} arquivo(s) selecionado(s)")
            self.log_progress(f"{len(filepaths)} documento(s) adicionado(s).")

    def start_analysis_thread(self):
        if not self.transcription_textbox.get("1.0", "end-1c").strip() and not self.document_paths:
            messagebox.showwarning("Aviso", "Adicione conteúdo para análise.")
            return
        self.analysis_button.configure(state="disabled", text="Analisando...")
        self.log_progress("Iniciando análise da IA...")
        thread = threading.Thread(target=self.run_analysis_process)
        thread.start()

    def run_analysis_process(self):
        transcription_text = self.transcription_textbox.get("1.0", "end-1c")
        client_info = {"nome": self.client_name_entry.get() or "Não informado"}
        mind_map_md, spec_content = run_analysis_and_generate_artifacts(
            transcription=transcription_text,
            info_cliente=client_info,
            doc_paths=self.document_paths,
            progress_callback=self.log_progress
        )
        self.after(0, self.update_gui_after_analysis, mind_map_md, spec_content)

    def update_gui_after_analysis(self, mind_map_md, spec_content):
        self.current_mind_map_md = mind_map_md
        self.current_spec_content = spec_content
        self.is_analysis_done = True

        self.mind_map_editor.delete("1.0", "end")
        self.mind_map_editor.insert("1.0", mind_map_md)
        self.update_mind_map_view()
        self.save_map_html_button.configure(state="normal")

        spec_doc_text = generate_specification_document(spec_content, self.client_name_entry.get() or "Não informado")
        self.spec_textbox.configure(state="normal")
        self.spec_textbox.delete("1.0", "end")
        self.spec_textbox.insert("1.0", spec_doc_text)
        self.spec_textbox.configure(state="disabled")
        self.save_spec_button.configure(state="normal")

        self.analysis_button.configure(state="normal", text="🚀 Gerar Análise e Artefatos")
        self.tab_view.set("Mapa Mental")
        self.log_progress("✅ Análise concluída! Mapa Mental e Especificação gerados.")
        
    def update_mind_map_view(self, event=None):
        markdown_text = self.mind_map_editor.get("1.0", "end-1c")
        html_content = MARKMAP_TEMPLATE_BASE.format(
            js_library=self.markmap_js_lib,
            markdown_content=markdown_text
        )
        self.mind_map_viewer.load_html(html_content)

    def save_mind_map_html(self):
        markdown_text = self.mind_map_editor.get("1.0", "end-1c")
        html_to_save = MARKMAP_TEMPLATE_BASE.format(
            js_library=self.markmap_js_lib,
            markdown_content=markdown_text
        )
        self.save_file(
            content_provider=lambda: html_to_save,
            title="Mapa-Mental",
            defaultextension=".html",
            filetypes=[("HTML File", "*.html")]
        )
        
    def save_specification_file(self):
        self.save_file(
            content_provider=lambda: self.spec_textbox.get("1.0", "end-1c"),
            title="Especificacao-Funcional",
            defaultextension=".txt",
            filetypes=[("Text Documents", "*.txt")]
        )

    def save_file(self, content_provider, title, defaultextension, filetypes):
        content_to_save = content_provider()
        if not content_to_save.strip(): return
        client_name = self.client_name_entry.get().strip() or "Cliente"
        suggested_filename = f"{title}_{client_name}{defaultextension}"
        filepath = filedialog.asksaveasfilename(
            initialfile=suggested_filename,
            defaultextension=defaultextension,
            filetypes=filetypes,
            title=f"Salvar {title}"
        )
        if filepath:
            try:
                with open(filepath, "w", encoding="utf-8") as file:
                    file.write(content_to_save)
                self.log_progress(f"Arquivo '{os.path.basename(filepath)}' salvo com sucesso.")
            except Exception as e:
                self.log_progress(f"❌ Erro ao salvar arquivo: {e}")
                messagebox.showerror("Erro de Salvamento", f"Não foi possível salvar o arquivo:\n{e}")

    def update_transcription_textbox(self, full_text):
        self.after(0, self._update_gui_text, full_text)

    def _update_gui_text(self, full_text):
        self.transcription_textbox.delete("1.0", "end")
        self.transcription_textbox.insert("1.0", full_text)
        self.transcription_textbox.see("end")

    def start_transcription(self):
        self.transcription_service.start_streaming()
        self.transcription_start_button.configure(state="disabled")
        self.transcription_stop_button.configure(state="normal")
        self.log_progress("🎤 Transcrição iniciada...")

    def stop_transcription(self):
        self.transcription_service.stop_streaming()
        self.transcription_start_button.configure(state="normal")
        self.transcription_stop_button.configure(state="disabled")
        self.log_progress("🛑 Transcrição parada.")

if __name__ == "__main__":
    if getattr(sys, 'frozen', False):
        import tkinterweb.native as tkinterweb_native
        tkinterweb_native.SELECT_SETTINGS_HANDLER = lambda: {'accept_language_str': 'en-US,en'}
    app = App()
    app.mainloop()