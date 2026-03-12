# src/gui.py

import customtkinter as ctk
from customtkinter import filedialog
import threading
import time
import os
from datetime import datetime
from tkinter import messagebox

# A importação do orchestrator agora inclui a nova função
from src.core.orchestrator import run_analysis_and_generate_artifacts, generate_specification_document, generate_word_document
from src.services.transcription_service import TranscriptionService, list_audio_devices

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
        self.audio_devices = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self.setup_ui()

        self.transcription_service = TranscriptionService(
            on_transcription_update=self.update_transcription_textbox,
            on_error=self.log_error,
            on_audio_level=self.update_vu_meter
        )
        self.last_vu_update = 0  # Timestamp para limitar a taxa de atualização do VU Meter
        self.load_audio_devices()
        self.log_progress("🚀 Sistema pronto. Inicie a transcrição ou adicione documentos.")

    def setup_ui(self):
        # Configuração da grid principal (2 colunas: Sidebar e Main)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # ==========================================
        # SIDEBAR (ESQUERDA)
        # ==========================================
        sidebar_frame = ctk.CTkFrame(self, width=320, corner_radius=0, fg_color="#18181A")
        sidebar_frame.grid(row=0, column=0, sticky="nsew")
        sidebar_frame.grid_rowconfigure(8, weight=1) # Espaço vazio no meio

        # --- LOGO / TÍTULO ---
        title_label = ctk.CTkLabel(sidebar_frame, text="Magic Meet", font=ctk.CTkFont(size=26, weight="bold", family="Segoe UI"))
        title_label.grid(row=0, column=0, padx=20, pady=(30, 0), sticky="w")
        subtitle_label = ctk.CTkLabel(sidebar_frame, text="Business Analyst Copilot", text_color="#2FA572", font=ctk.CTkFont(size=13, slant="italic"))
        subtitle_label.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="w")

        # --- SEPARADOR ---
        separator1 = ctk.CTkFrame(sidebar_frame, height=2, fg_color="#2C2C2E")
        separator1.grid(row=2, column=0, sticky="ew", padx=20, pady=5)

        # --- CONFIGURAÇÕES DA REUNIÃO ---
        settings_frame = ctk.CTkFrame(sidebar_frame, fg_color="transparent")
        settings_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        
        ctk.CTkLabel(settings_frame, text="Nome do Cliente:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(5, 5))
        self.client_name_entry = ctk.CTkEntry(settings_frame, placeholder_text="Ex: Projeto XPTO", height=35, corner_radius=6)
        self.client_name_entry.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(settings_frame, text="Documentos de Apoio:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(0, 5))
        self.add_doc_button = ctk.CTkButton(settings_frame, text="➕ Adicionar Arquivos", command=self.add_documents, fg_color="transparent", border_width=1, border_color="#555555", text_color="#DDDDDD", hover_color="#333333", height=32)
        self.add_doc_button.pack(fill="x", pady=5)
        self.doc_list_label = ctk.CTkLabel(settings_frame, text="Nenhum arquivo anexado.", text_color="#888888", font=ctk.CTkFont(size=11))
        self.doc_list_label.pack(anchor="w", pady=(0, 5))

        # --- SEPARADOR ---
        separator2 = ctk.CTkFrame(sidebar_frame, height=2, fg_color="#2C2C2E")
        separator2.grid(row=4, column=0, sticky="ew", padx=20, pady=5)

        # --- CONTROLES DE ÁUDIO ---
        audio_frame = ctk.CTkFrame(sidebar_frame, fg_color="transparent")
        audio_frame.grid(row=5, column=0, padx=20, pady=10, sticky="ew")
        
        ctk.CTkLabel(audio_frame, text="Entrada de Áudio:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", pady=(5, 5))
        self.audio_device_var = ctk.StringVar(value="Carregando...")
        self.audio_device_dropdown = ctk.CTkOptionMenu(audio_frame, variable=self.audio_device_var, values=["Carregando..."], dynamic_resizing=False, command=self.on_device_change, height=35, fg_color="#333333", button_color="#444444", button_hover_color="#555555")
        self.audio_device_dropdown.pack(fill="x", pady=(0, 15))

        # --- VU METER (TESTADOR DE VOLUME) ---
        vu_frame = ctk.CTkFrame(audio_frame, fg_color="#212124", corner_radius=8)
        vu_frame.pack(fill="x", pady=(0, 5), ipady=5)
        ctk.CTkLabel(vu_frame, text=" Sinal de Áudio", font=ctk.CTkFont(size=11, slant="italic"), text_color="#AAAAAA").pack(side="left", padx=10)
        self.vu_meter = ctk.CTkProgressBar(vu_frame, height=8, progress_color="#2FA572", fg_color="#333333")
        self.vu_meter.set(0)
        self.vu_meter.pack(side="right", fill="x", expand=True, padx=(0, 10))

        # --- CONTROLES DE TRANSCRIÇÃO ---
        transcription_frame = ctk.CTkFrame(sidebar_frame, fg_color="transparent")
        transcription_frame.grid(row=6, column=0, padx=20, pady=20, sticky="ew")
        
        self.transcription_start_button = ctk.CTkButton(transcription_frame, text="▶ INICIAR REUNIÃO", command=self.start_transcription, height=45, font=ctk.CTkFont(weight="bold", size=13), fg_color="#2FA572", hover_color="#248259", corner_radius=8)
        self.transcription_start_button.pack(fill="x", pady=(0, 10))
        
        self.transcription_stop_button = ctk.CTkButton(transcription_frame, text="⏹ PARAR REUNIÃO", command=self.stop_transcription, height=45, font=ctk.CTkFont(weight="bold", size=13), fg_color="#2C2C2E", hover_color="#C93B3B", state="disabled", corner_radius=8)
        self.transcription_stop_button.pack(fill="x")

        # --- BOTÃO PRINCIPAL (ANÁLISE) ---
        self.analysis_button = ctk.CTkButton(sidebar_frame, text="✨ GERAR DOCUMENTAÇÃO", command=self.start_analysis_thread, height=55, font=ctk.CTkFont(size=14, weight="bold"), fg_color="#3B71CA", hover_color="#2D5BA3", corner_radius=8)
        self.analysis_button.grid(row=9, column=0, padx=20, pady=30, sticky="ew")


        # ==========================================
        # MAIN CONTENT (DIREITA)
        # ==========================================
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)  # TabView ganha mais espaço
        main_frame.grid_rowconfigure(1, weight=0)  # Log ganha espaço fixo

        # --- TABS DE RESULTADO ---
        self.tab_view = ctk.CTkTabview(main_frame)
        self.tab_view.grid(row=0, column=0, padx=5, pady=0, sticky="nsew")
        self.tab_view.add("📝 Transcrição da Reunião")
        self.tab_view.add("📊 Fluxo BPMN")
        self.tab_view.add("📄 Especificação Funcional")

        # --- ABA DE TRANSCRIÇÃO ---
        transc_tab = self.tab_view.tab("📝 Transcrição da Reunião")
        transc_tab.grid_columnconfigure(0, weight=1)
        transc_tab.grid_rowconfigure(0, weight=1)
        self.transcription_textbox = ctk.CTkTextbox(transc_tab, wrap="word", font=("Calibri", 16))
        self.transcription_textbox.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # --- ABA DE BPMN ---
        bpmn_tab = self.tab_view.tab("📊 Fluxo BPMN")
        bpmn_tab.grid_columnconfigure(0, weight=1)
        bpmn_tab.grid_rowconfigure(0, weight=1)
        self.bpmn_textbox = ctk.CTkTextbox(bpmn_tab, wrap="word", font=("Consolas", 12))
        self.bpmn_textbox.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.save_bpmn_button = ctk.CTkButton(bpmn_tab, text="💾 Salvar Arquivo .bpmn", command=self.save_bpmn_file, state="disabled")
        self.save_bpmn_button.grid(row=1, column=0, sticky="e", padx=10, pady=10)

        # --- ABA DE ESPECIFICAÇÃO ---
        spec_tab = self.tab_view.tab("📄 Especificação Funcional")
        spec_tab.grid_columnconfigure(0, weight=1)
        spec_tab.grid_rowconfigure(0, weight=1)
        self.spec_textbox = ctk.CTkTextbox(spec_tab, wrap="word", font=("Calibri", 15), state="disabled")
        self.spec_textbox.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        spec_buttons_frame = ctk.CTkFrame(spec_tab, fg_color="transparent")
        spec_buttons_frame.grid(row=1, column=0, sticky="e", padx=10, pady=10)
        
        self.save_spec_txt_button = ctk.CTkButton(spec_buttons_frame, text="💾 Salvar como TXT", command=self.save_specification_txt, state="disabled")
        self.save_spec_txt_button.pack(side="right", padx=(5,0))
        
        self.save_spec_word_button = ctk.CTkButton(spec_buttons_frame, text="📝 Salvar como Word (.docx)", command=self.save_specification_word, state="disabled", fg_color="#2B579A", hover_color="#1E3E6E")
        self.save_spec_word_button.pack(side="right")

        # --- LOG DO SISTEMA ---
        log_frame = ctk.CTkFrame(main_frame, height=120)
        log_frame.grid(row=1, column=0, padx=5, pady=(10, 5), sticky="ew")
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_propagate(False) # Mantém altura fixa
        
        self.progress_log_textbox = ctk.CTkTextbox(log_frame, state="disabled", wrap="word", font=("Consolas", 12), text_color="#A0A0A0")
        self.progress_log_textbox.pack(fill="both", expand=True, padx=5, pady=5)

    # (Funções de log, add_documents, start_analysis_thread, run_analysis_process permanecem as mesmas)
    def log_progress(self, message):
        self.after(0, self._append_to_log, message)
    def log_error(self, message):
        self.after(0, self._append_to_log, f"❌ ERRO: {message}")

    def _append_to_log(self, message):
        self.progress_log_textbox.configure(state="normal")
        self.progress_log_textbox.insert("end", f"[{datetime.now().strftime('%H:%M:%S')}] {message}\n")
        self.progress_log_textbox.see("end")
        self.progress_log_textbox.configure(state="disabled")

    def load_audio_devices(self):
        try:
            self.audio_devices = list_audio_devices()
            mic_devices = [d for d in self.audio_devices if not d['is_loopback']]
            
            if mic_devices:
                device_names = [d['name'] for d in mic_devices]
                self.audio_device_dropdown.configure(values=device_names)
                
                # Tenta selecionar um microfone padrão sensato
                default_name = device_names[0]
                self.audio_device_var.set(default_name)
        except Exception as e:
            self.log_error(f"Erro ao carregar dispositivos de áudio: {e}")
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
        try:
            transcription_text = self.transcription_textbox.get("1.0", "end-1c")
            client_info = {"nome": self.client_name_entry.get() or "Não informado"}
            bpmn_xml, spec_content = run_analysis_and_generate_artifacts(
                transcription=transcription_text, info_cliente=client_info,
                doc_paths=self.document_paths, progress_callback=self.log_progress
            )
            self.after(0, self.update_gui_after_analysis, bpmn_xml, spec_content)
        except Exception as e:
            self.log_error(f"Falha na análise: {e}")
            self.after(0, self._reset_analysis_button)

    def _reset_analysis_button(self):
        self.analysis_button.configure(state="normal", text="🚀 Gerar Análise e Artefatos")

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

        self.analysis_button.configure(state="normal", text="🚀 Gerar Especificação & BPMN")
        self.tab_view.set("📄 Especificação Funcional")
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
    def on_device_change(self, *args):
        # Se estiver rodando, reinicia com a nova fonte de áudio
        if self.transcription_service.is_running:
            self.stop_transcription()
            self.after(500, self.start_transcription) # Pequeno atraso para liberar o recurso

    def update_vu_meter(self, rms_value):
        # Limita a atualização para +- 20fps via time para não travar a GUI principal
        current_time = time.time()
        if (current_time - self.last_vu_update) < 0.05:
            return
        self.last_vu_update = current_time

        # Transforma o nível linear numa curva suave de 0 a 1
        normalized_level = min(rms_value / 2500, 1.0)
        self.after(0, self._set_vu_meter, normalized_level)

    def _set_vu_meter(self, level):
        self.vu_meter.set(level)

    def update_transcription_textbox(self, full_text):
        self.after(0, self._update_gui_text, full_text)
    def _update_gui_text(self, full_text):
        self.transcription_textbox.delete("1.0", "end")
        self.transcription_textbox.insert("1.0", full_text)
        self.transcription_textbox.see("end")

    def start_transcription(self):
        # Encontra o ID do dispositivo de mic selecionado
        selected_mic_name = self.audio_device_var.get()
        mic_id = None
        for d in self.audio_devices:
            if d['name'] == selected_mic_name:
                mic_id = d['index']
                break
                
        self.transcription_service.set_audio_source(mic_device_index=mic_id)
        self.transcription_service.start_streaming()
        self.transcription_start_button.configure(state="disabled")
        self.transcription_stop_button.configure(state="normal")
        self.audio_device_dropdown.configure(state="disabled")
        self.log_progress("🎤 Captura de áudio & Reunião iniciada...")

    def stop_transcription(self):
        self.transcription_service.stop_streaming()
        self.transcription_start_button.configure(state="normal")
        self.transcription_stop_button.configure(state="disabled")
        self.audio_device_dropdown.configure(state="normal")
        self.vu_meter.set(0)
        self.log_progress("🛑 Captura de áudio parada.")
        
    def on_closing(self):
        self.stop_transcription()
        self.quit()

if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()