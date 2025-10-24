# src/gui.py

import customtkinter as ctk
from customtkinter import filedialog
import threading
import os
from datetime import datetime
from tkinter import messagebox

# A importação do orchestrator agora inclui a nova função
from src.core.orchestrator import run_analysis_and_generate_artifacts, generate_specification_document, generate_word_document
from src.services.transcription_service import TranscriptionService

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Business Analyst Copilot")
        self.geometry("1200x850")

        self.current_bpmn_xml = ""
        self.current_spec_content = {} # Armazena os dados estruturados
        self.document_paths = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self.setup_ui()

        self.transcription_service = TranscriptionService(on_transcription_update=self.update_transcription_textbox)
        self.log_progress("🚀 Sistema pronto. Inicie a transcrição ou adicione documentos.")

    def setup_ui(self):
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
        
        # --- FRAME PRINCIPAL ---
        main_frame = ctk.CTkFrame(self)
        main_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)

        # --- CONTROLES ---
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
        self.tab_view.add("BPMN")
        self.tab_view.add("Especificação Funcional")

        # --- ABA DE TRANSCRIÇÃO ---
        self.transcription_textbox = ctk.CTkTextbox(self.tab_view.tab("Transcrição"), wrap="word", font=("Calibri", 16))
        self.transcription_textbox.pack(expand=True, fill="both", padx=5, pady=5)

        # --- ABA DE BPMN ---
        bpmn_tab = self.tab_view.tab("BPMN")
        bpmn_tab.grid_columnconfigure(0, weight=1)
        bpmn_tab.grid_rowconfigure(0, weight=1)
        self.bpmn_textbox = ctk.CTkTextbox(bpmn_tab, wrap="word", font=("Consolas", 12))
        self.bpmn_textbox.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.save_bpmn_button = ctk.CTkButton(bpmn_tab, text="Salvar Arquivo .bpmn", command=self.save_bpmn_file, state="disabled")
        self.save_bpmn_button.grid(row=1, column=0, sticky="e", padx=10, pady=10)

        # --- ABA DE ESPECIFICAÇÃO ---
        spec_tab = self.tab_view.tab("Especificação Funcional")
        spec_tab.grid_columnconfigure(0, weight=1)
        spec_tab.grid_rowconfigure(0, weight=1)
        self.spec_textbox = ctk.CTkTextbox(spec_tab, wrap="word", font=("Calibri", 15), state="disabled")
        self.spec_textbox.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Frame para os botões de salvar especificação
        spec_buttons_frame = ctk.CTkFrame(spec_tab, fg_color="transparent")
        spec_buttons_frame.grid(row=1, column=0, sticky="e", padx=10, pady=10)
        
        self.save_spec_txt_button = ctk.CTkButton(spec_buttons_frame, text="Salvar como TXT", command=self.save_specification_txt, state="disabled")
        self.save_spec_txt_button.pack(side="right", padx=(5,0))

        # --- NOVO BOTÃO PARA SALVAR EM WORD ---
        self.save_spec_word_button = ctk.CTkButton(spec_buttons_frame, text="Salvar como Word (.docx)", command=self.save_specification_word, state="disabled")
        self.save_spec_word_button.pack(side="right")

        # --- LOG ---
        self.progress_log_textbox = ctk.CTkTextbox(main_frame, height=100, state="disabled", wrap="word", font=("Consolas", 12))
        self.progress_log_textbox.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

    # (Funções de log, add_documents, start_analysis_thread, run_analysis_process permanecem as mesmas)
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
        bpmn_xml, spec_content = run_analysis_and_generate_artifacts(
            transcription=transcription_text, info_cliente=client_info,
            doc_paths=self.document_paths, progress_callback=self.log_progress
        )
        self.after(0, self.update_gui_after_analysis, bpmn_xml, spec_content)

    def update_gui_after_analysis(self, bpmn_xml, spec_content):
        self.current_bpmn_xml = bpmn_xml
        self.current_spec_content = spec_content # Armazena os dados estruturados
        
        self.bpmn_textbox.delete("1.0", "end")
        self.bpmn_textbox.insert("1.0", bpmn_xml)
        self.save_bpmn_button.configure(state="normal")
        
        spec_doc_text = generate_specification_document(spec_content, self.client_name_entry.get() or "Não informado")
        self.spec_textbox.configure(state="normal")
        self.spec_textbox.delete("1.0", "end")
        self.spec_textbox.insert("1.0", spec_doc_text)
        self.spec_textbox.configure(state="disabled")
        self.save_spec_txt_button.configure(state="normal")
        self.save_spec_word_button.configure(state="normal") # Habilita o novo botão

        self.analysis_button.configure(state="normal", text="🚀 Gerar Análise e Artefatos")
        self.tab_view.set("Especificação Funcional")
        self.log_progress("✅ Análise concluída! Arquivo BPMN e Especificação gerados.")

    # --- FUNÇÃO PARA SALVAR O WORD ---
    def save_specification_word(self):
        client_name = self.client_name_entry.get().strip() or "Cliente"
        suggested_filename = f"Especificacao-Funcional_{client_name.replace(' ', '_')}.docx"
        
        filepath = filedialog.asksaveasfilename(
            initialfile=suggested_filename,
            defaultextension=".docx",
            filetypes=[("Word Document", "*.docx"), ("All Files", "*.*")],
            title="Salvar Especificação como Word"
        )
        if not filepath:
            return

        # Roda a geração do Word em uma thread para não travar a UI
        self.log_progress(f"-> [⚙️] Gerando documento Word...")
        thread = threading.Thread(target=self.run_word_save_process, args=(filepath,))
        thread.start()
    
    def run_word_save_process(self, filepath):
        try:
            doc = generate_word_document(self.current_spec_content)
            doc.save(filepath)
            self.log_progress(f"-> [✅] Documento Word '{os.path.basename(filepath)}' salvo com sucesso.")
        except Exception as e:
            self.log_progress(f"-> [❌] Erro ao salvar documento Word: {e}")
            messagebox.showerror("Erro ao Salvar", f"Não foi possível salvar o arquivo Word:\n{e}")

    # --- Funções de salvar .txt e .bpmn (modificadas para clareza) ---
    def save_specification_txt(self):
        self.save_file(
            content_provider=lambda: self.spec_textbox.get("1.0", "end-1c"),
            title="Especificacao-Funcional",
            defaultextension=".txt",
            filetypes=[("Text Documents", "*.txt")]
        )
    
    def save_bpmn_file(self):
        self.save_file(
            content_provider=lambda: self.current_bpmn_xml,
            title="Processo",
            defaultextension=".bpmn",
            filetypes=[("BPMN Files", "*.bpmn"), ("All Files", "*.*")]
        )

    def save_file(self, content_provider, title, defaultextension, filetypes):
        content_to_save = content_provider()
        if not content_to_save.strip(): return
        client_name = self.client_name_entry.get().strip() or "Cliente"
        suggested_filename = f"{title}_{client_name.replace(' ', '_')}{defaultextension}"
        filepath = filedialog.asksaveasfilename(
            initialfile=suggested_filename, defaultextension=defaultextension,
            filetypes=filetypes, title=f"Salvar {title}"
        )
        if filepath:
            try:
                with open(filepath, "w", encoding="utf-8") as file:
                    file.write(content_to_save)
                self.log_progress(f"Arquivo '{os.path.basename(filepath)}' salvo com sucesso.")
            except Exception as e:
                self.log_progress(f"❌ Erro ao salvar arquivo: {e}")
                messagebox.showerror("Erro de Salvamento", f"Não foi possível salvar o arquivo:\n{e}")

    # (Funções de transcrição permanecem as mesmas)
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
    app = App()
    app.mainloop()