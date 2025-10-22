# src/gui.py

import customtkinter as ctk
from customtkinter import filedialog
import threading
import os
from src.core.orchestrator import gerar_analise, gerar_prototipo, gerar_proposta_final
from src.services.transcription_service import TranscriptionService

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Magic Meet Copilot Pro")
        self.geometry("1100x800") # Altura inicial pode ser menor agora
        
        # Variável para armazenar o prompt do protótipo entre as etapas
        self.current_prompt_lovable = None

        # --- CONTAINER PRINCIPAL COM BARRA DE ROLAGEM ---
        # Configura a janela principal para expandir o scrollable frame
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Cria o frame com barra de rolagem que conterá todos os outros widgets
        self.main_frame = ctk.CTkScrollableFrame(self)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Configura o grid DENTRO do scrollable frame
        self.main_frame.grid_rowconfigure(1, weight=1) # Transcrição
        self.main_frame.grid_rowconfigure(3, weight=2) # Resultados
        
        # --- FRAME DE SETUP (DENTRO DO MAIN_FRAME) ---
        setup_frame = ctk.CTkFrame(self.main_frame)
        setup_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        setup_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(setup_frame, text="Nome Cliente:", anchor="w").grid(row=0, column=0, padx=10, pady=5)
        self.client_name_entry = ctk.CTkEntry(setup_frame, placeholder_text="Nome do cliente...")
        self.client_name_entry.grid(row=0, column=1, columnspan=2, padx=10, pady=5, sticky="ew")

        # ... (O resto da criação dos widgets continua igual, mas com 'self.main_frame' como pai)
        
        ctk.CTkLabel(setup_frame, text="Cores (Hex):", anchor="w").grid(row=1, column=0, padx=10, pady=5)
        self.client_colors_entry = ctk.CTkEntry(setup_frame, placeholder_text="#FFFFFF, #000000")
        self.client_colors_entry.grid(row=1, column=1, columnspan=2, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(setup_frame, text="Logo Cliente:", anchor="w").grid(row=2, column=0, padx=10, pady=5)
        self.logo_path_entry = ctk.CTkEntry(setup_frame, placeholder_text="Nenhum arquivo selecionado...")
        self.logo_path_entry.grid(row=2, column=1, padx=(10, 5), pady=5, sticky="ew")
        self.logo_button = ctk.CTkButton(setup_frame, text="Selecionar", width=100, command=self.select_logo_file)
        self.logo_button.grid(row=2, column=2, padx=(0, 10), pady=5)

        self.document_paths = []
        ctk.CTkLabel(setup_frame, text="Docs. Apoio:", anchor="w").grid(row=3, column=0, padx=10, pady=5)
        self.doc_list_entry = ctk.CTkEntry(setup_frame, placeholder_text="Nenhum documento adicionado...")
        self.doc_list_entry.configure(state="disabled")
        self.doc_list_entry.grid(row=3, column=1, padx=(10, 5), pady=5, sticky="ew")
        self.add_doc_button = ctk.CTkButton(setup_frame, text="Adicionar", width=100, command=self.add_documents)
        self.add_doc_button.grid(row=3, column=2, padx=(0, 10), pady=5)
        
        # --- FRAME DE TRANSCRIÇÃO (DENTRO DO MAIN_FRAME) ---
        summary_frame = ctk.CTkFrame(self.main_frame)
        summary_frame.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        summary_frame.grid_rowconfigure(1, weight=1)
        summary_frame.grid_columnconfigure(0, weight=1)
        
        controls_frame = ctk.CTkFrame(summary_frame)
        controls_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        controls_frame.grid_columnconfigure((0, 1), weight=1)
        
        self.transcription_start_button = ctk.CTkButton(controls_frame, text="▶️ Iniciar Transcrição", command=self.start_transcription)
        self.transcription_start_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.transcription_stop_button = ctk.CTkButton(controls_frame, text="⏹️ Parar Transcrição", command=self.stop_transcription, state="disabled")
        self.transcription_stop_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        self.summary_textbox = ctk.CTkTextbox(summary_frame, wrap="word", font=("Calibri", 16))
        self.summary_textbox.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")

        # --- FRAME DE GERAÇÃO (DENTRO DO MAIN_FRAME) ---
        generation_frame = ctk.CTkFrame(self.main_frame)
        generation_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        generation_frame.grid_columnconfigure((0,1,2), weight=1)

        self.analysis_button = ctk.CTkButton(generation_frame, text="1. Gerar Análise da Reunião", command=self.iniciar_thread_analise, height=40)
        self.analysis_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        self.prototype_button = ctk.CTkButton(generation_frame, text="2. Gerar Protótipo (RPA)", state="disabled", command=self.iniciar_thread_prototipo, height=40)
        self.prototype_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.proposal_button = ctk.CTkButton(generation_frame, text="3. Gerar Pré-Proposta (RAG)", state="disabled", command=self.iniciar_thread_proposta, height=40)
        self.proposal_button.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        self.progress_log_textbox = ctk.CTkTextbox(generation_frame, height=120, state="disabled", wrap="word", font=("Consolas", 12))
        self.progress_log_textbox.grid(row=1, column=0, columnspan=3, padx=5, pady=10, sticky="ew")

        # --- FRAME DE RESULTADOS (DENTRO DO MAIN_FRAME) ---
        self.tab_view = ctk.CTkTabview(self.main_frame)
        self.tab_view.grid(row=3, column=0, padx=10, pady=10, sticky="nsew")
        self.tab_view.add("Pré-Análise (Editável)")
        self.tab_view.add("Protótipo (Link)")
        self.tab_view.add("Pré-Proposta (RAG)")
        self.tab_view.set("Pré-Análise (Editável)")
        
        self.configure_tab(self.tab_view.tab("Pré-Análise (Editável)"), "pre_analysis")
        self.configure_tab(self.tab_view.tab("Protótipo (Link)"), "prototype")
        self.configure_tab(self.tab_view.tab("Pré-Proposta (RAG)"), "proposal")

        self.transcription_service = TranscriptionService(on_transcription_update=self.update_transcription_textbox)

    # (O restante do código, com todas as funções, permanece exatamente o mesmo)
    def configure_tab(self, tab, name):
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)
        
        if name == "pre_analysis":
            self.pre_analysis_textbox = ctk.CTkTextbox(tab, wrap="word", state="disabled", font=("Calibri", 15))
            self.pre_analysis_textbox.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
            self.save_analysis_button = ctk.CTkButton(tab, text="Salvar Análise (.txt)", state="disabled", command=self.save_analysis_file)
            self.save_analysis_button.grid(row=1, column=0, padx=10, pady=10, sticky="e")
        elif name == "prototype":
            self.link_textbox = ctk.CTkTextbox(tab, wrap="word", height=50, state="disabled", font=("Calibri", 15))
            self.link_textbox.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        elif name == "proposal":
            self.proposal_textbox = ctk.CTkTextbox(tab, wrap="word", state="disabled", font=("Calibri", 15))
            self.proposal_textbox.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
            self.save_proposal_button = ctk.CTkButton(tab, text="Salvar Proposta (.txt)", state="disabled", command=self.save_proposal_file)
            self.save_proposal_button.grid(row=1, column=0, padx=10, pady=10, sticky="e")
    
    def log_progress(self, message):
        self.after(0, self._append_to_log, message)

    def _append_to_log(self, message):
        self.progress_log_textbox.configure(state="normal")
        self.progress_log_textbox.insert("end", message + "\n")
        self.progress_log_textbox.see("end")
        self.progress_log_textbox.configure(state="disabled")

    def add_documents(self):
        filepaths = filedialog.askopenfilenames(
            title="Selecione os documentos de apoio (PDF, TXT, OGG, MP3, etc.)",
            filetypes=(
                ("Documentos e Áudios", "*.pdf *.txt *.md *.ogg *.mp3 *.m4a *.wav *.mp4 *.mpeg"),
                ("Todos os arquivos", "*.*")
            )
        )
        if filepaths:
            for path in filepaths:
                if path not in self.document_paths: self.document_paths.append(path)
            self.doc_list_entry.configure(state="normal")
            self.doc_list_entry.delete(0, "end")
            self.doc_list_entry.insert(0, f"{len(self.document_paths)} arquivo(s) selecionado(s)")
            self.doc_list_entry.configure(state="disabled")

    def iniciar_thread_analise(self):
        self.analysis_button.configure(state="disabled", text="Gerando Análise...")
        self.prototype_button.configure(state="disabled")
        self.proposal_button.configure(state="disabled")
        self.progress_log_textbox.configure(state="normal"); self.progress_log_textbox.delete("1.0", "end"); self.progress_log_textbox.configure(state="disabled")
        thread = threading.Thread(target=self.run_analysis_process); thread.start()

    def run_analysis_process(self):
        transcription_text = self.summary_textbox.get("1.0", "end-1c")
        client_info = {"nome": self.client_name_entry.get(), "cores": self.client_colors_entry.get()}
        
        pre_analise, prompt_lovable = gerar_analise(
            transcricao=transcription_text, info_cliente=client_info, doc_paths=self.document_paths, 
            progress_callback=self.log_progress
        )
        self.current_prompt_lovable = prompt_lovable
        self.after(0, self.update_gui_after_analysis, pre_analise)

    def update_gui_after_analysis(self, pre_analise):
        self.pre_analysis_textbox.configure(state="normal")
        self.pre_analysis_textbox.delete("1.0", "end"); self.pre_analysis_textbox.insert("1.0", pre_analise)
        
        if "Erro" not in pre_analise and "Falha" not in pre_analise:
            self.save_analysis_button.configure(state="normal")
            self.prototype_button.configure(state="normal")
            self.proposal_button.configure(state="normal")
            self.tab_view.set("Pré-Análise (Editável)")
        
        self.analysis_button.configure(state="normal", text="1. Gerar Análise da Reunião")
    
    def iniciar_thread_prototipo(self):
        self.prototype_button.configure(state="disabled", text="Gerando Protótipo...")
        thread = threading.Thread(target=self.run_prototype_process); thread.start()

    def run_prototype_process(self):
        logo_path = self.logo_path_entry.get()
        link_prototipo = gerar_prototipo(self.current_prompt_lovable, logo_path, self.log_progress)
        self.after(0, self.update_gui_after_prototype, link_prototipo)
        
    def update_gui_after_prototype(self, link_prototipo):
        self.link_textbox.configure(state="normal")
        self.link_textbox.delete("1.0", "end"); self.link_textbox.insert("1.0", link_prototipo)
        self.link_textbox.configure(state="disabled")
        self.tab_view.set("Protótipo (Link)")
        self.prototype_button.configure(state="normal", text="2. Gerar Protótipo (RPA)")
        
    def iniciar_thread_proposta(self):
        self.proposal_button.configure(state="disabled", text="Gerando Proposta...")
        thread = threading.Thread(target=self.run_proposal_process); thread.start()
        
    def run_proposal_process(self):
        analise_editada = self.pre_analysis_textbox.get("1.0", "end-1c")
        if not analise_editada.strip():
            self.log_progress("-> [⚠️] A pré-análise não pode estar vazia para gerar a proposta.")
            self.after(0, lambda: self.proposal_button.configure(state="normal", text="3. Gerar Pré-Proposta (RAG)"))
            return
        texto_proposta = gerar_proposta_final(analise_editada, self.log_progress)
        self.after(0, self.update_gui_after_proposal, texto_proposta)

    def update_gui_after_proposal(self, texto_proposta):
        self.proposal_textbox.configure(state="normal")
        self.proposal_textbox.delete("1.0", "end"); self.proposal_textbox.insert("1.0", texto_proposta)
        self.proposal_textbox.configure(state="disabled")
        if texto_proposta and "Erro" not in texto_proposta:
            self.save_proposal_button.configure(state="normal")
            self.tab_view.set("Pré-Proposta (RAG)")
        self.proposal_button.configure(state="normal", text="3. Gerar Pré-Proposta (RAG)")

    def save_file(self, content_provider, title):
        text_to_save = content_provider()
        if not text_to_save.strip(): return
        client_name = self.client_name_entry.get().strip() or "Cliente"
        suggested_filename = f"{title} - {client_name}.txt"
        filepath = filedialog.asksaveasfilename(
            initialfile=suggested_filename, defaultextension=".txt",
            filetypes=[("Text Documents", "*.txt"), ("All files", "*.*")], title=f"Salvar {title}")
        if filepath:
            try:
                with open(filepath, "w", encoding="utf-8") as file: file.write(text_to_save)
            except Exception as e: print(f"Erro ao salvar arquivo: {e}")

    def save_analysis_file(self): self.save_file(lambda: self.pre_analysis_textbox.get("1.0", "end-1c"), "Pre-Analise")
    def save_proposal_file(self): self.save_file(lambda: self.proposal_textbox.get("1.0", "end-1c"), "Proposta-Comercial")

    def select_logo_file(self):
        filepath = filedialog.askopenfilename(title="Selecione o arquivo de logo")
        if filepath: self.logo_path_entry.delete(0, "end"); self.logo_path_entry.insert(0, filepath)
            
    def update_transcription_textbox(self, full_text): self.after(0, self._update_gui_text, full_text)

    def _update_gui_text(self, full_text):
        self.summary_textbox.delete("1.0", "end"); self.summary_textbox.insert("1.0", full_text); self.summary_textbox.see("end")

    def start_transcription(self):
        self.transcription_service.start_streaming()
        self.transcription_start_button.configure(state="disabled"); self.transcription_stop_button.configure(state="normal")

    def stop_transcription(self):
        self.transcription_service.stop_streaming()
        self.transcription_start_button.configure(state="normal"); self.transcription_stop_button.configure(state="disabled")

if __name__ == "__main__":
    app = App()
    app.mainloop()