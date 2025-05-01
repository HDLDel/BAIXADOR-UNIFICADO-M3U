import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import re
import requests
import threading
from threading import Thread
import concurrent.futures
import customtkinter as ctk
import vlc
import os
import webbrowser
import unicodedata
import aria2p
import subprocess
import time
import json
from unidecode import unidecode
from ttkthemes import ThemedTk
from advanced_downloader import AdvancedDownloader

"""
Baixador de Vídeos - Versão 1.13.11
Autor: [Seu Nome]
Data: 30/04/2024
"""

class DownloadQueueWindow:
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("Fila de Downloads")
        self.window.geometry("1000x800")
        
        # Frame principal
        self.main_frame = ctk.CTkFrame(self.window)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Treeview para mostrar a fila
        self.tree = ttk.Treeview(
            self.main_frame,
            columns=("Nome", "Progresso", "Velocidade", "Status"),
            show="headings"
        )
        
        # Configurar colunas
        self.tree.heading("Nome", text="Nome")
        self.tree.heading("Progresso", text="Progresso")
        self.tree.heading("Velocidade", text="Velocidade")
        self.tree.heading("Status", text="Status")
        
        # Configurar larguras das colunas
        self.tree.column("Nome", width=300)
        self.tree.column("Progresso", width=150)
        self.tree.column("Velocidade", width=150)
        self.tree.column("Status", width=150)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.main_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Posicionar Treeview e Scrollbar
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Frame para botões
        self.button_frame = ctk.CTkFrame(self.main_frame)
        self.button_frame.pack(fill=tk.X, pady=5)
        
        # Botões
        self.btn_cancel = ctk.CTkButton(
            self.button_frame,
            text="Cancelar Download",
            command=self.cancel_selected
        )
        self.btn_cancel.pack(side=tk.LEFT, padx=5)
        
        self.btn_clear = ctk.CTkButton(
            self.button_frame,
            text="Limpar Concluídos",
            command=self.clear_completed
        )
        self.btn_clear.pack(side=tk.LEFT, padx=5)
        
        # Dicionário para armazenar os downloads
        self.downloads = {}
        
        # Centralizar a janela
        self.center_window()
        
    def center_window(self):
        """Centraliza a janela na tela"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'+{x}+{y}')
        
    def add_download(self, name, url, path):
        """Adiciona um novo download à fila"""
        item_id = self.tree.insert('', 'end', values=(name, "0%", "0 MB/s", "Aguardando"))
        self.downloads[item_id] = {
            'name': name,
            'url': url,
            'path': path,
            'status': 'waiting'
        }
        
    def update_download(self, item_id, progress, speed, status):
        """Atualiza as informações de um download"""
        if item_id in self.downloads:
            self.tree.set(item_id, "Progresso", f"{progress:.1f}%")
            self.tree.set(item_id, "Velocidade", f"{speed:.1f} MB/s")
            self.tree.set(item_id, "Status", status)
            self.downloads[item_id]['status'] = status
            
    def cancel_selected(self):
        """Cancela o download selecionado"""
        selected = self.tree.selection()
        if not selected:
            return
            
        for item_id in selected:
            if item_id in self.downloads:
                self.downloads[item_id]['status'] = 'cancelled'
                self.tree.set(item_id, "Status", "Cancelado")
                
    def clear_completed(self):
        """Remove os downloads concluídos da lista"""
        to_remove = []
        for item_id in self.downloads:
            if self.downloads[item_id]['status'] in ['completed', 'cancelled']:
                to_remove.append(item_id)
                
        for item_id in to_remove:
            self.tree.delete(item_id)
            del self.downloads[item_id]

class PesquisaPlaylist:
    def __init__(self):
        self.root = ThemedTk(theme="arc")
        self.root.title("Pesquisa de Servidores v1.13.11")
        self.root.geometry("1200x800")
        
        # Configuração do tema escuro
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        
        # Variáveis
        self.dados_m3u = []
        self.dados_db = []
        self.conn = None
        self.cursor = None
        self.current_url = None
        self.download_path = tk.StringVar(value=os.getcwd())
        self.user_agent = tk.StringVar(value="Mozilla/5.0")
        self.dns_server = tk.StringVar(value="")  # DNS padrão vazio (usa o DNS do sistema)
        self.download_progress = tk.DoubleVar()
        self.download_progress.set(0.0)
        self.cancel_download = False
        self.download_queue = []
        self.is_downloading = False
        self.config_file = "config.json"
        self.reserva_mode = False  # Novo: controla o modo reserva
        
        # Configuração do player
        self.player_type = "vlc"  # Player padrão é VLC
        self.mpv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mpv', 'mpv.exe')  # Caminho para o executável do MPV
        self.mpv_process = None  # Processo do MPV (quando em uso)
        
        # Lista de temas disponíveis
        self.available_themes = ["arc", "equilux", "breeze", "clearlooks", "elegance", "radiance"]
        
        # Inicializa aria2
        self.start_aria2c()
        self.aria2 = aria2p.API(aria2p.Client(host="http://localhost", port=6800))
        
        # Inicializa VLC
        self.instance = vlc.Instance('--no-xlib')
        self.player = self.instance.media_player_new()
        self.is_playing = False
        
        # Configura o volume inicial
        self.player.audio_set_volume(100)
        
        # Cache em memória para o banco de dados
        self.db_cache = {}
        self.db_cache_loaded = False
        
        # Carrega configurações
        self.load_config()
        
        # Inicializa o banco de dados
        self.init_database()
        
        # Criar interface
        self.criar_interface()

        self.advanced_downloader = AdvancedDownloader(
            self.root,
            self.download_path.get(),
            self.user_agent.get(),
            self.dns_server.get()
        )

        self.download_queue_window = None

    def start_aria2c(self):
        """Inicia o servidor aria2c"""
        try:
            subprocess.Popen(["aria2c", "--enable-rpc", "--rpc-listen-all=true"], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
            time.sleep(2)  # Aguarda o servidor iniciar
        except FileNotFoundError:
            messagebox.showerror("Erro", "aria2c não encontrado. Por favor, instale o aria2 primeiro.")
            sys.exit(1)

    def load_config(self):
        """Carrega as configurações do arquivo"""
        try:
            config = {}
            if os.path.exists('config.json'):
                with open('config.json', 'r') as f:
                    config = json.load(f)
            
            # Carrega o caminho de download padrão
            default_download_path = config.get('default_download_path', os.path.join(os.path.expanduser("~"), "Downloads"))
            self.download_path.set(default_download_path)
            
            # Carrega o User-Agent
            self.user_agent.set(config.get('user_agent', 'Mozilla/5.0'))
            
            # Carrega o DNS
            self.dns_server.set(config.get('dns_server', ''))
            
        except Exception as e:
            print(f"Erro ao carregar configurações: {e}")
            # Em caso de erro, usa a pasta Downloads do usuário
            default_download_path = os.path.join(os.path.expanduser("~"), "Downloads")
            self.download_path.set(default_download_path)

    def save_config(self):
        """Salva as configurações no arquivo"""
        try:
            config = {
                'default_download_path': self.download_path.get(),
                'user_agent': self.user_agent.get(),
                'dns_server': self.dns_server.get()
            }
            
            with open('config.json', 'w') as f:
                json.dump(config, f)
                
        except Exception as e:
            print(f"Erro ao salvar configurações: {e}")

    def browse_directory(self):
        """Abre diálogo para selecionar pasta de download"""
        directory = filedialog.askdirectory(initialdir=self.download_path.get())
        if directory:
            self.download_path.set(directory)
            # Salva automaticamente a nova configuração
            self.save_config()

    def get_url_from_selection(self, item=None):
        """Obtém a URL do item selecionado de forma segura"""
        if item is None:
            selected_items = self.tree.selection()
            if not selected_items:
                return None
            item = selected_items[0]
            
        values = self.tree.item(item)['values']
        nome_video = values[1]
        
        # Busca primeiro no banco de dados
        for item_db in self.dados_db:
            if item_db[1] == nome_video:  # item_db[1] é o nome
                return item_db[2]  # item_db[2] é a URL
        
        # Se não encontrou no banco, busca nos dados M3U
        for item_m3u in self.dados_m3u:
            if item_m3u[0] == nome_video:
                return item_m3u[5]  # item_m3u[5] é a URL
        
        return None

    def download_selected(self):
        """Inicia o download dos itens selecionados"""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("Aviso", "Por favor, selecione um vídeo para download.")
            return

        download_path = self.download_path.get()
        if not os.path.exists(download_path):
            messagebox.showerror("Erro", "Pasta de download inválida.")
            return

        # Adiciona os vídeos selecionados à fila
        for item in selected_items:
            values = self.tree.item(item)['values']
            nome_video = values[1]
            url = self.get_url_from_selection(item)
            
            if url:
                self.download_queue.append((nome_video, url, download_path))
                # Adiciona à janela da fila se estiver aberta
                if self.download_queue_window and self.download_queue_window.window.winfo_exists():
                    self.download_queue_window.add_download(nome_video, url, download_path)
            else:
                messagebox.showwarning("Aviso", f"URL não encontrada para o vídeo: {nome_video}")

        # Inicia o processamento da fila se não houver download em andamento
        if not self.is_downloading:
            self.process_download_queue()

    def process_download_queue(self):
        """Processa a fila de downloads"""
        if not self.download_queue:
            self.is_downloading = False
            return

        self.is_downloading = True
        name, url, path = self.download_queue.pop(0)
        Thread(target=self.download_video_with_callback, args=(name, url, path)).start()

    def download_video_with_callback(self, name, url, path):
        """Download com callback para processar a fila"""
        try:
            self.download_video(name, url, path)
        finally:
            self.root.after(1000, self.process_download_queue)

    def sanitize_directory_name(self, name):
        """Remove caracteres inválidos de nomes de diretórios"""
        # Lista de caracteres inválidos no Windows
        invalid_chars = '<>:"/\\|?*'
        # Substitui cada caractere inválido por um espaço
        for char in invalid_chars:
            name = name.replace(char, ' ')
        # Remove espaços extras e normaliza
        name = ' '.join(name.split())
        return name

    def download_video(self, name, url, path):
        """Realiza o download do vídeo"""
        try:
            self.cancel_download = False
            self.download_info_label.configure(text=f"Baixando: {name}")
            
            # Extrai o nome do conteúdo e a temporada
            content_name, season = self.extract_content_info(name)

            # Sanitiza os nomes dos diretórios
            content_name = self.sanitize_directory_name(content_name)
            if season:
                season = self.sanitize_directory_name(season)

            # Cria a pasta do conteúdo
            content_folder = os.path.join(path, content_name)
            if not os.path.exists(content_folder):
                os.makedirs(content_folder)

            # Se for uma série, cria a pasta da temporada
            if season:
                season_folder = os.path.join(content_folder, season)
                if not os.path.exists(season_folder):
                    os.makedirs(season_folder)
                file_path = os.path.join(season_folder, f"{self.sanitize_directory_name(name)}.mp4")
            else:
                file_path = os.path.join(content_folder, f"{self.sanitize_directory_name(name)}.mp4")

            # Configuração do download com aria2
            options = {
                "dir": os.path.dirname(file_path),
                "out": os.path.basename(file_path),
                "max-connection-per-server": "16",
                "split": "16",
                "user-agent": self.user_agent.get(),
                "continue": "true",
                "max-concurrent-downloads": "1"
            }

            # Adiciona DNS se configurado
            dns_server = self.dns_server.get().strip()
            if dns_server:
                options["dns-server"] = dns_server

            # Inicia o download
            download = self.aria2.add_uris([url], options=options)
            
            # Encontra o item na janela da fila
            queue_item = None
            if self.download_queue_window and self.download_queue_window.window.winfo_exists():
                for item_id in self.download_queue_window.downloads:
                    if self.download_queue_window.downloads[item_id]['name'] == name:
                        queue_item = item_id
                        break
            
            while not self.cancel_download and download.is_active:
                try:
                    download.update()
                    downloaded = download.completed_length
                    total = download.total_length
                    
                    if total > 0:
                        progress = (downloaded / total) * 100
                        speed = download.download_speed / (1024 * 1024)  # Converte para MB/s
                        
                        self.download_progress.set(progress)
                        self.progress_label.configure(text=f"{progress:.1f}%")
                        self.speed_label.configure(text=f"{speed:.1f} MB/s")
                        
                        # Atualiza a janela da fila
                        if queue_item:
                            self.download_queue_window.update_download(
                                queue_item,
                                progress,
                                speed,
                                "Baixando"
                            )
                        
                        self.root.update_idletasks()
                    
                    time.sleep(0.1)
                except Exception:
                    break

            if self.cancel_download:
                download.remove(force=True)
                if os.path.exists(file_path):
                    os.remove(file_path)
                self.download_info_label.configure(text="Download cancelado")
                if queue_item:
                    self.download_queue_window.update_download(
                        queue_item,
                        0,
                        0,
                        "Cancelado"
                    )
                return

            # Atualiza status para concluído
            if queue_item:
                self.download_queue_window.update_download(
                    queue_item,
                    100,
                    0,
                    "Concluído"
                )

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao baixar {name}: {e}")
            if queue_item:
                self.download_queue_window.update_download(
                    queue_item,
                    0,
                    0,
                    "Erro"
                )
        finally:
            self.download_progress.set(0.0)
            self.progress_label.configure(text="0%")
            self.speed_label.configure(text="0 MB/s")
            self.download_info_label.configure(text="")

    def extract_content_info(self, name):
        """Extrai informações do conteúdo (nome e temporada)"""
        match = re.search(r"(.*?)\s*(S\d{2})\s*E\d{2}", name)
        if match:
            content_name = match.group(1).strip()
            season = match.group(2).strip()
            return content_name, season
        else:
            return name, None

    def cancel_current_download(self):
        """Cancela o download atual"""
        if self.is_downloading:
            self.cancel_download = True
            self.download_info_label.configure(text="Cancelando download...")

    def clean_folders(self):
        """Limpa as pastas de download"""
        try:
            if not messagebox.askyesno("Confirmar", "Tem certeza que deseja limpar todas as pastas de download?"):
                return

            base_dir = self.download_path.get()
            items_to_remove = []
            
            for root, dirs, files in os.walk(base_dir):
                for file in files:
                    if file.endswith(('.mp4', '.mkv', '.avi', '.mov')):
                        items_to_remove.append(os.path.join(root, file))
                
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    if not os.listdir(dir_path):
                        items_to_remove.append(dir_path)
            
            for item in items_to_remove:
                try:
                    if os.path.isfile(item):
                        os.remove(item)
                    elif os.path.isdir(item):
                        os.rmdir(item)
                except Exception as e:
                    print(f"Erro ao remover {item}: {e}")
            
            messagebox.showinfo("Sucesso", "Pastas de download limpas com sucesso!")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao limpar pastas: {e}")

    def criar_interface(self):
        # Frame principal
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Frame superior para botões e entrada
        self.top_frame = ctk.CTkFrame(self.main_frame)
        self.top_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Botão Carregar DB
        self.btn_carregar_db = ctk.CTkButton(
            self.top_frame,
            text="Carregar Banco de Dados",
            command=self.carregar_banco
        )
        self.btn_carregar_db.pack(side=tk.LEFT, padx=5)
        
        # Frame para URL e botão M3U
        self.url_frame = ctk.CTkFrame(self.top_frame)
        self.url_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Entrada de URL
        self.url_entry = ctk.CTkEntry(
            self.url_frame,
            placeholder_text="Digite a URL do arquivo M3U"
        )
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Botão Carregar M3U
        self.btn_carregar_m3u = ctk.CTkButton(
            self.url_frame,
            text="Carregar M3U",
            command=self.carregar_m3u
        )
        self.btn_carregar_m3u.pack(side=tk.LEFT, padx=5)
        
        # Botão Adicionar Links
        self.btn_adicionar_links = ctk.CTkButton(
            self.url_frame,
            text="Adicionar Links",
            command=self.load_multiple_links
        )
        self.btn_adicionar_links.pack(side=tk.LEFT, padx=5)

        # Botão Carregar M3U Local
        self.btn_carregar_m3u_local = ctk.CTkButton(
            self.url_frame,
            text="Carregar M3U Local",
            command=self.carregar_m3u_local
        )
        self.btn_carregar_m3u_local.pack(side=tk.LEFT, padx=5)

        # Frame para configurações de download
        self.download_config_frame = ctk.CTkFrame(self.top_frame)
        self.download_config_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Pasta de download
        self.download_path_label = ctk.CTkLabel(self.download_config_frame, text="Pasta de Download:")
        self.download_path_label.pack(side=tk.LEFT, padx=5)
        
        self.download_path_entry = ctk.CTkEntry(
            self.download_config_frame,
            textvariable=self.download_path
        )
        self.download_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.btn_browse = ctk.CTkButton(
            self.download_config_frame,
            text="Escolher Pasta",
            command=self.browse_directory
        )
        self.btn_browse.pack(side=tk.LEFT, padx=5)

        # Frame para User-Agent e DNS
        self.network_config_frame = ctk.CTkFrame(self.top_frame)
        self.network_config_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # User-Agent
        self.ua_label = ctk.CTkLabel(self.network_config_frame, text="User-Agent:")
        self.ua_label.pack(side=tk.LEFT, padx=5)
        
        self.ua_combo = ctk.CTkOptionMenu(
            self.network_config_frame,
            values=[
                "Mozilla/5.0",  # User-Agent padrão
                "VLC/3.0.18 LibVLC/3.0.18",  # User-Agent do VLC
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",  # User-Agent do Chrome
                "Lavf/58.76.100",  # User-Agent do FFmpeg
                "Mozilla/5.0 (SMART-TV; Linux; Tizen 2.4.0) AppleWebkit/538.1",  # User-Agent de Smart TV
                "Custom..."  # Opção para User-Agent personalizado
            ],
            command=self.change_user_agent
        )
        self.ua_combo.pack(side=tk.LEFT, padx=5)
        self.ua_combo.set(self.user_agent.get())  # Define o valor atual

        # Campo para User-Agent personalizado
        self.ua_entry = ctk.CTkEntry(
            self.network_config_frame,
            placeholder_text="Digite o User-Agent personalizado"
        )

        # DNS Server
        self.dns_label = ctk.CTkLabel(self.network_config_frame, text="DNS:")
        self.dns_label.pack(side=tk.LEFT, padx=5)
        
        self.dns_entry = ctk.CTkEntry(
            self.network_config_frame,
            textvariable=self.dns_server,
            placeholder_text="Ex: 8.8.8.8"
        )
        self.dns_entry.pack(side=tk.LEFT, padx=5)

        # Menu de temas
        self.theme_label = ctk.CTkLabel(self.download_config_frame, text="Tema:")
        self.theme_label.pack(side=tk.LEFT, padx=5)
        
        self.theme_menu = ctk.CTkOptionMenu(
            self.download_config_frame,
            values=self.available_themes,
            command=self.change_theme
        )
        self.theme_menu.pack(side=tk.LEFT, padx=5)
        # Define o tema atual no menu
        current_theme = self.root.get_themes()[0]
        self.theme_menu.set(current_theme)
        
        self.btn_save_config = ctk.CTkButton(
            self.download_config_frame,
            text="Salvar Config",
            command=self.save_config
        )
        self.btn_save_config.pack(side=tk.LEFT, padx=5)
        
        # Frame para pesquisa
        self.search_frame = ctk.CTkFrame(self.main_frame)
        self.search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Campo de pesquisa
        self.search_entry = ctk.CTkEntry(
            self.search_frame,
            placeholder_text="Digite o termo de pesquisa"
        )
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Botão Pesquisar
        self.btn_pesquisar = ctk.CTkButton(
            self.search_frame,
            text="Pesquisar",
            command=self.filtrar_resultados
        )
        self.btn_pesquisar.pack(side=tk.LEFT, padx=5)

        # Frame para progresso do download
        self.progress_frame = ctk.CTkFrame(self.main_frame)
        self.progress_frame.pack(fill=tk.X, padx=5, pady=5)

        # Barra de progresso
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, variable=self.download_progress)
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        # Labels de informação
        self.progress_info_frame = ctk.CTkFrame(self.progress_frame)
        self.progress_info_frame.pack(fill=tk.X)
        
        self.progress_label = ctk.CTkLabel(self.progress_info_frame, text="0%")
        self.progress_label.pack(side=tk.LEFT, padx=5)
        
        self.speed_label = ctk.CTkLabel(self.progress_info_frame, text="0 MB/s")
        self.speed_label.pack(side=tk.LEFT, padx=5)
        
        self.download_info_label = ctk.CTkLabel(self.progress_info_frame, text="")
        self.download_info_label.pack(side=tk.LEFT, padx=5)
        
        self.btn_cancel = ctk.CTkButton(
            self.progress_info_frame,
            text="Cancelar",
            command=self.cancel_current_download
        )
        self.btn_cancel.pack(side=tk.RIGHT, padx=5)
        
        # Frame para conteúdo (lista e player)
        self.content_frame = ctk.CTkFrame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Frame esquerdo para lista
        self.left_frame = ctk.CTkFrame(self.content_frame)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Frame para botões da lista
        self.list_buttons_frame = ctk.CTkFrame(self.left_frame)
        self.list_buttons_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Botão Abrir no Navegador
        self.btn_abrir = ctk.CTkButton(
            self.list_buttons_frame,
            text="Abrir no Navegador",
            command=self.open_selected_in_browser
        )
        self.btn_abrir.pack(side=tk.LEFT, padx=5)
        
        # Botão Copiar Link
        self.btn_copiar = ctk.CTkButton(
            self.list_buttons_frame,
            text="Copiar Link",
            command=self.copy_selected_link
        )
        self.btn_copiar.pack(side=tk.LEFT, padx=5)
        
        # Botão Download
        self.btn_download = ctk.CTkButton(
            self.list_buttons_frame,
            text="Download",
            command=self.download_selected
        )
        self.btn_download.pack(side=tk.LEFT, padx=5)
        
        # Botão Download Avançado
        self.btn_download_advanced = ctk.CTkButton(
            self.list_buttons_frame,
            text="Download Avançado",
            command=self.download_selected_advanced
        )
        self.btn_download_advanced.pack(side=tk.LEFT, padx=5)

        # Botão Adicionar à Fila
        self.btn_add_to_queue = ctk.CTkButton(
            self.list_buttons_frame,
            text="Adicionar à Fila",
            command=self.add_to_download_queue
        )
        self.btn_add_to_queue.pack(side=tk.LEFT, padx=5)

        # Botão Retomar Downloads
        self.btn_retomar = ctk.CTkButton(
            self.list_buttons_frame,
            text="Retomar Downloads",
            command=self.retomar_downloads
        )
        self.btn_retomar.pack(side=tk.LEFT, padx=5)

        # Checkbox para usar apenas aria2
        self.use_only_aria2_var = tk.BooleanVar(value=True)
        self.use_only_aria2_checkbox = ctk.CTkCheckBox(
            self.list_buttons_frame,
            text="Aria2",
            variable=self.use_only_aria2_var,
            command=self.toggle_use_only_aria2
        )
        self.use_only_aria2_checkbox.pack(side=tk.LEFT, padx=5)

        # Checkbox para modo reserva
        self.reserva_var = tk.BooleanVar(value=False)
        self.reserva_checkbox = ctk.CTkCheckBox(
            self.list_buttons_frame,
            text="Reserva",
            variable=self.reserva_var,
            command=self.toggle_reserva_mode
        )
        self.reserva_checkbox.pack(side=tk.LEFT, padx=5)

        # Botão Limpar Pastas
        self.btn_limpar = ctk.CTkButton(
            self.list_buttons_frame,
            text="Limpar Pastas",
            command=self.clean_folders
        )
        self.btn_limpar.pack(side=tk.LEFT, padx=5)

        # Separador
        ttk.Separator(self.list_buttons_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)

        # Menu de seleção do player
        self.player_label = ctk.CTkLabel(self.list_buttons_frame, text="Player:")
        self.player_label.pack(side=tk.LEFT, padx=5)
        
        self.player_menu = ctk.CTkOptionMenu(
            self.list_buttons_frame,
            values=["VLC", "MPV"],
            command=self.change_player
        )
        self.player_menu.pack(side=tk.LEFT, padx=5)
        self.player_menu.set("VLC")  # Define VLC como padrão

        # Separador
        ttk.Separator(self.list_buttons_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)

        # Frame direito para player
        self.right_frame = ctk.CTkFrame(self.content_frame)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Treeview para resultados
        self.tree = ttk.Treeview(
            self.left_frame,
            columns=("Nº", "Nome", "Tipo", "Temporada", "Servidor", "Link de Origem"),
            show="headings"
        )
        
        # Configurar colunas
        self.tree.heading("Nº", text="Nº", command=lambda: self.sort_treeview("Nº"))
        self.tree.heading("Nome", text="Nome", command=lambda: self.sort_treeview("Nome"))
        self.tree.heading("Tipo", text="Tipo", command=lambda: self.sort_treeview("Tipo"))
        self.tree.heading("Temporada", text="Temporada", command=lambda: self.sort_treeview("Temporada"))
        self.tree.heading("Servidor", text="Servidor", command=lambda: self.sort_treeview("Servidor"))
        self.tree.heading("Link de Origem", text="Link de Origem", command=lambda: self.sort_treeview("Link de Origem"))
        
        # Configurar larguras das colunas
        self.tree.column("Nº", width=50)
        self.tree.column("Nome", width=400)
        self.tree.column("Tipo", width=100)
        self.tree.column("Temporada", width=100)
        self.tree.column("Servidor", width=200)
        self.tree.column("Link de Origem", width=300)
        
        # Scrollbar para a lista
        scrollbar = ttk.Scrollbar(self.left_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Posicionar Treeview e Scrollbar
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Frame do player VLC
        self.vlc_frame = tk.Frame(self.right_frame, bg="black")
        self.vlc_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Frame dos controles do player
        self.controls_frame = ctk.CTkFrame(self.right_frame)
        self.controls_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Botões de controle do player
        self.play_button = ctk.CTkButton(
            self.controls_frame,
            text="▶",
            width=30,
            command=self.toggle_play
        )
        self.play_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ctk.CTkButton(
            self.controls_frame,
            text="⏹",
            width=30,
            command=self.stop_video
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)

        # Botão retroceder
        self.rewind_button = ctk.CTkButton(
            self.controls_frame,
            text="⏮",
            width=30,
            command=self.rewind_video
        )
        self.rewind_button.pack(side=tk.LEFT, padx=5)

        # Botão avançar
        self.forward_button = ctk.CTkButton(
            self.controls_frame,
            text="⏭",
            width=30,
            command=self.forward_video
        )
        self.forward_button.pack(side=tk.LEFT, padx=5)
        
        # Barra de progresso do vídeo
        self.video_progress = ctk.CTkProgressBar(self.controls_frame)
        self.video_progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.video_progress.set(0)
        
        # Label de tempo
        self.time_label = ctk.CTkLabel(self.controls_frame, text="00:00 / 00:00")
        self.time_label.pack(side=tk.LEFT, padx=5)
        
        # Controle de volume
        self.volume_slider = ctk.CTkSlider(
            self.controls_frame,
            from_=0,
            to=100,
            command=self.set_volume
        )
        self.volume_slider.pack(side=tk.LEFT, padx=5)
        self.volume_slider.set(100)
        
        # Configurar estilo para tema escuro
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", 
                       background="#2b2b2b",
                       foreground="white",
                       fieldbackground="#2b2b2b")
        style.configure("Treeview.Heading",
                       background="#1f538d",
                       foreground="white")
        
        # Bind eventos
        self.search_entry.bind("<Return>", lambda e: self.filtrar_resultados())
        self.tree.bind("<Double-Button-1>", self.on_tree_double_click)
        
        # Variável para controlar a ordenação
        self.sort_reverse = False
        self.last_sort_column = None
        
        # Botão para abrir janela da fila de downloads
        self.btn_queue = ctk.CTkButton(
            self.list_buttons_frame,
            text="Fila de Downloads",
            command=self.show_download_queue
        )
        self.btn_queue.pack(side=tk.LEFT, padx=5)

    def on_tree_double_click(self, event):
        """Manipula duplo clique na treeview"""
        selected_items = self.tree.selection()
        if not selected_items:
            return
            
        url = self.get_url_from_selection(selected_items[0])
        if url:
            self.play_video(url)
        else:
            messagebox.showinfo("Aviso", "URL não encontrada para este vídeo.")
        
    def play_video(self, url):
        """Reproduz um vídeo"""
        try:
            # Para qualquer reprodução atual
            self.stop_video()
            
            if self.player_type == "vlc":
                # Cria media com opções específicas
                media = self.instance.media_new(url)
                media.add_option('--no-video-title-show')  # Não mostra título do vídeo
                media.add_option(':network-caching=1000')  # Cache de rede
                media.add_option(f':http-user-agent={self.user_agent.get()}')  # Define User-Agent
                
                # Se tiver DNS configurado, adiciona
                if self.dns_server.get().strip():
                    media.add_option(f':dns-server={self.dns_server.get().strip()}')
                
                self.player.set_media(media)
                
                # Configura janela de reprodução
                if os.name == 'nt':  # Windows
                    self.player.set_hwnd(self.vlc_frame.winfo_id())
                else:  # Linux/Mac
                    self.player.set_xwindow(self.vlc_frame.winfo_id())
                
                # Inicia reprodução
                self.player.play()
                self.is_playing = True
                self.play_button.configure(text="⏸")
                
                # Salva a URL atual
                self.current_url = url
                
                # Inicia atualização do progresso
                self.root.after(1000, self.update_video_progress)
                
            else:  # MPV
                # Configura os argumentos do MPV
                args = [
                    self.mpv_path,
                    f'--user-agent={self.user_agent.get()}',
                    '--force-window=yes',
                    '--keep-open=yes',
                    '--no-terminal',
                    f'--wid={self.vlc_frame.winfo_id()}',
                    '--volume=100'
                ]
                
                # Adiciona DNS se configurado
                if self.dns_server.get().strip():
                    args.append(f'--dns-server={self.dns_server.get().strip()}')
                
                # Adiciona a URL por último
                args.append(url)
                
                # Inicia o processo do MPV
                self.mpv_process = subprocess.Popen(args)
                self.is_playing = True
                self.current_url = url
                self.play_button.configure(text="⏸")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao reproduzir vídeo: {str(e)}")
            print(f"Erro detalhado: {str(e)}")  # Log para debug
    
    def toggle_play(self):
        """Alterna entre play e pause"""
        if self.player_type == "vlc":
            if self.player.is_playing():
                self.player.pause()
                self.is_playing = False
                self.play_button.configure(text="▶")
            else:
                self.player.play()
                self.is_playing = True
                self.play_button.configure(text="⏸")
        else:  # MPV
            if self.mpv_process:
                if self.is_playing:
                    # Envia comando de pause
                    subprocess.run([self.mpv_path, '--input-ipc-server=/tmp/mpv-socket', 'cycle', 'pause'], check=False)
                    self.is_playing = False
                    self.play_button.configure(text="▶")
                else:
                    # Envia comando de play
                    subprocess.run([self.mpv_path, '--input-ipc-server=/tmp/mpv-socket', 'cycle', 'pause'], check=False)
                    self.is_playing = True
                    self.play_button.configure(text="⏸")
    
    def stop_video(self):
        """Para a reprodução"""
        if self.player_type == "vlc":
            self.player.stop()
            self.is_playing = False
            self.play_button.configure(text="▶")
            self.video_progress.set(0)
            self.time_label.configure(text="00:00 / 00:00")
        else:  # MPV
            if self.mpv_process:
                self.mpv_process.terminate()
                self.mpv_process = None
            self.is_playing = False
            self.play_button.configure(text="▶")
            self.video_progress.set(0)
            self.time_label.configure(text="00:00 / 00:00")
    
    def set_volume(self, value):
        """Ajusta o volume"""
        if self.player_type == "vlc":
            self.player.audio_set_volume(int(value))
        else:  # MPV
            if self.mpv_process:
                subprocess.run([self.mpv_path, '--input-ipc-server=/tmp/mpv-socket', 'set', 'volume', str(int(value))], check=False)
    
    def update_video_progress(self):
        """Atualiza a barra de progresso e o tempo"""
        if self.player_type == "vlc" and self.player.is_playing():
            # Atualiza progresso
            length = self.player.get_length()
            time = self.player.get_time()
            
            if length > 0:
                progress = time / length
                self.video_progress.set(progress)
                
                # Formata tempo
                current = time // 1000  # Converte para segundos
                total = length // 1000
                current_str = f"{current//60:02d}:{current%60:02d}"
                total_str = f"{total//60:02d}:{total%60:02d}"
                self.time_label.configure(text=f"{current_str} / {total_str}")
            
            # Agenda próxima atualização
            self.root.after(1000, self.update_video_progress)
            
    def conectar_banco(self):
        """Conecta ao banco de dados"""
        try:
            # Se já existe uma conexão ativa, retorna True
            if self.conn is not None:
                return True

            print("Tentando conectar ao banco de dados...")
            db_path = os.path.abspath('videos.db')
            print(f"Caminho do banco: {db_path}")
            
            # Verifica se o diretório tem permissão de escrita
            db_dir = os.path.dirname(db_path)
            if not os.access(db_dir, os.W_OK):
                print(f"Sem permissão de escrita no diretório: {db_dir}")
                messagebox.showerror("Erro", "Sem permissão de escrita no diretório do banco de dados")
                return False

            self.conn = sqlite3.connect('videos.db')
            self.cursor = self.conn.cursor()
            
            # Verifica se a tabela existe
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS videos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    url TEXT NOT NULL UNIQUE,
                    type TEXT NOT NULL,
                    season TEXT NOT NULL,
                    username TEXT,
                    downloaded INTEGER DEFAULT 0
                )
            """)
            self.conn.commit()
            
            print("Conexão com o banco estabelecida com sucesso")
            return True
            
        except Exception as e:
            print(f"Erro ao conectar ao banco: {str(e)}")
            messagebox.showerror("Erro", f"Erro ao conectar ao banco de dados: {str(e)}")
            return False

    def carregar_banco(self):
        """Carrega dados do banco de dados usando o cache em memória"""
        try:
            if not self.conectar_banco():
                return
                
            # Carrega todos os dados do banco
            self.cursor.execute('SELECT * FROM videos')
            self.dados_db = self.cursor.fetchall()
            
            # Limpa a lista M3U para mostrar apenas dados do banco
            self.dados_m3u = []
            
            # Limpa a interface
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            messagebox.showinfo("Sucesso", f"Banco de dados carregado com sucesso! {len(self.dados_db)} registros disponíveis para pesquisa.")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar banco de dados: {str(e)}")

    def atualizar_interface_banco(self):
        """Atualiza a interface com os dados do banco"""
        # Limpa a Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Contador para numeração
        contador = 1
        
        # Adiciona os dados do banco
        for item in self.dados_db:
            # Extrai servidor e username da URL
            servidor, username = self.extrair_servidor_e_username(item[2])
            
            # Ordem: Nº, Nome, Tipo, Temporada, Servidor, Link de Origem
            self.tree.insert('', 'end', values=(contador, item[1], item[3], item[4], servidor, item[2]))
            contador += 1

    def carregar_m3u(self):
        """Carrega dados do arquivo M3U via URL"""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Aviso", "Por favor, insira uma URL válida.")
            return
            
        def process_m3u():
            try:
                # Faz o download do arquivo M3U
                response = requests.get(url, headers={'User-Agent': self.user_agent.get()})
                response.raise_for_status()
                
                # Processa o conteúdo
                conteudo = response.text
                linhas = conteudo.split('\n')
                
                # Limpa a lista de dados M3U
                self.dados_m3u = []
                
                # Processa cada linha
                nome = None
                for i, linha in enumerate(linhas):
                    linha = linha.strip()
                    if linha.startswith('#EXTINF:'):
                        # Extrai o nome do cabeçalho EXTINF
                        if 'tvg-name="' in linha:
                            nome = re.search('tvg-name="([^"]*)"', linha)
                            if nome:
                                nome = nome.group(1)
                        if not nome and ',' in linha:
                            nome = linha.split(',', 1)[1].strip()
                    elif linha and not linha.startswith('#') and nome:
                        # Esta é a linha da URL
                        tipo = "Filme"
                        temporada = "None"
                        
                        # Verifica se é uma série
                        if nome:
                            match = re.search(r"(.*?)\s*(S\d{2})\s*E\d{2}", nome)
                            if match:
                                tipo = "Série"
                                temporada = match.group(2)
                        
                        # Extrai servidor e username da URL
                        servidor, username = self.extrair_servidor_e_username(linha)
                        
                        # Adiciona aos dados M3U
                        self.dados_m3u.append((nome, tipo, temporada, servidor, username, linha))
                        nome = None  # Reset para próximo item
            
                # Atualiza a interface na thread principal
                self.root.after(0, lambda: self.atualizar_interface())
                self.root.after(0, lambda: messagebox.showinfo("Sucesso", "Arquivo M3U carregado com sucesso!"))
                
            except Exception as error:
                error_msg = str(error)
                self.root.after(0, lambda msg=error_msg: messagebox.showerror("Erro", f"Erro ao carregar arquivo M3U: {msg}"))
        
        # Inicia o processamento em uma thread separada
        threading.Thread(target=process_m3u, daemon=True).start()

    def extrair_servidor_e_username(self, url):
        """Extrai o nome do servidor e username da URL"""
        try:
            # Remove o protocolo (http:// ou https://)
            url_sem_protocolo = re.sub(r'^https?://', '', url)
            
            # Divide a URL em partes
            partes = url_sem_protocolo.split('/')
            
            # Pega o servidor (primeira parte)
            servidor = partes[0].split(':')[0]
            
            # Tenta extrair o username da URL
            username = "N/A"
            if "username=" in url:
                # Procura por username= seguido de números
                match = re.search(r'username=(\d+)', url)
                if match:
                    username = match.group(1)
                else:
                    # Se não encontrou números, tenta pegar qualquer valor após username=
                    match = re.search(r'username=([^&]+)', url)
                    if match:
                        username = match.group(1)
            
            return servidor, username
        except:
            return "Desconhecido", "N/A"
            
    def normalize_text(self, text):
        """Remove acentos, caracteres especiais e normaliza pontuação do texto"""
        # Converte para string se não for
        text = str(text)
        
        # Remove espaços extras e normaliza pontuação
        text = ' '.join(text.split())  # Remove espaços extras
        text = text.replace("'", "")   # Remove aspas simples
        text = text.replace('"', '')   # Remove aspas duplas
        text = text.replace(',', ' ')  # Substitui vírgulas por espaços
        text = text.replace(';', ' ')  # Substitui ponto e vírgula por espaços
        text = text.replace(':', ' ')  # Substitui dois pontos por espaços
        text = text.replace('.', ' ')  # Substitui pontos por espaços
        text = text.replace('!', ' ')  # Substitui exclamação por espaços
        text = text.replace('?', ' ')  # Substitui interrogação por espaços
        text = text.replace('-', ' ')  # Substitui hífens por espaços
        text = text.replace('_', ' ')  # Substitui underscores por espaços
        
        # Normaliza o texto (NFD) e remove os diacríticos
        text = unicodedata.normalize('NFD', text)
        # Remove caracteres não ASCII e converte para minúsculas
        text = ''.join(c for c in text if not unicodedata.category(c) == 'Mn')
        text = text.lower()
        
        # Substitui caracteres especiais comuns
        replacements = {
            'ç': 'c',
            'ñ': 'n',
            'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a',
            'é': 'e', 'è': 'e', 'ê': 'e',
            'í': 'i', 'ì': 'i', 'î': 'i',
            'ó': 'o', 'ò': 'o', 'õ': 'o', 'ô': 'o',
            'ú': 'u', 'ù': 'u', 'û': 'u',
            'ý': 'y', 'ÿ': 'y',
            'ä': 'a', 'ë': 'e', 'ï': 'i', 'ö': 'o', 'ü': 'u',
            'ß': 'ss',
            'æ': 'ae', 'œ': 'oe',
            'ð': 'd', 'þ': 'th',
            'ł': 'l', 'ø': 'o', 'å': 'a'
        }
        
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        
        # Remove espaços extras novamente após todas as substituições
        text = ' '.join(text.split())
        
        return text

    def filtrar_resultados(self):
        """Filtra os resultados usando os dados M3U em memória e banco de dados"""
        termo_busca = self.normalize_text(self.search_entry.get())  # Normaliza o termo de busca
        
        # Limpa a Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        try:
            # Lista para armazenar todos os resultados
            resultados = []
            
            # Filtra os dados M3U
            for item in self.dados_m3u:
                if termo_busca in self.normalize_text(item[0]):  # Normaliza o nome do item
                    resultados.append((item[0], item[1], item[2], item[3], item[5]))
            
            # Filtra os dados do banco
            if self.dados_db:
                for item in self.dados_db:
                    # item[1] é o nome, item[2] é a url, item[3] é o tipo, item[4] é a temporada
                    if termo_busca in self.normalize_text(str(item[1])):  # Normaliza o nome do item
                        servidor, username = self.extrair_servidor_e_username(item[2])
                        resultados.append((item[1], item[3], item[4], servidor, item[2]))
            
            # Exibe os resultados
            contador = 1
            for item in resultados:
                # Ordem: Nº, Nome, Tipo, Temporada, Servidor, Link de Origem
                self.tree.insert('', 'end', values=(contador, item[0], item[1], item[2], item[3], item[4]))
                contador += 1
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao filtrar resultados: {str(e)}")

    def load_multiple_links(self):
        """Carrega múltiplos links M3U ao mesmo tempo"""
        try:
            # Cria uma nova janela
            multi_url_window = tk.Toplevel(self.root)
            multi_url_window.title("Adicionar Múltiplos Links")
            multi_url_window.geometry("1200x600")
            
            # Frame principal com split
            main_frame = ttk.Frame(multi_url_window)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            # Frame esquerdo para links
            left_frame = ttk.Frame(main_frame)
            left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
            
            # Frame direito para terminal
            right_frame = ttk.Frame(main_frame)
            right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
            
            # Adiciona um texto explicativo
            ttk.Label(left_frame, 
                     text="Cole aqui seus links M3U (um por linha):",
                     wraplength=550,
                     padding=10).pack(fill=tk.X)
            
            # Cria um campo de texto com barra de rolagem para links
            text_frame = ttk.Frame(left_frame)
            text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            text_scroll = ttk.Scrollbar(text_frame)
            text_scroll.pack(side=tk.RIGHT, fill=tk.Y)
            
            text_area = tk.Text(text_frame, 
                               wrap=tk.WORD, 
                               yscrollcommand=text_scroll.set,
                               height=15)
            text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            text_scroll.config(command=text_area.yview)

            # Frame para progresso
            progress_frame = ttk.LabelFrame(left_frame, text="Progresso", padding="5")
            progress_frame.pack(fill=tk.X, padx=5, pady=5)

            # Barra de progresso
            progress_var = tk.DoubleVar()
            progress_bar = ttk.Progressbar(progress_frame, variable=progress_var, maximum=100)
            progress_bar.pack(fill=tk.X, pady=5)

            # Labels para informações
            info_frame = ttk.Frame(progress_frame)
            info_frame.pack(fill=tk.X)

            progress_label = ttk.Label(info_frame, text="0%")
            progress_label.pack(side=tk.LEFT, padx=5)

            status_label = ttk.Label(info_frame, text="", wraplength=500)
            status_label.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            
            # Frame para os botões
            button_frame = ttk.Frame(left_frame)
            button_frame.pack(fill=tk.X, padx=5, pady=5)
            
            # Frame para o terminal
            terminal_frame = ttk.LabelFrame(right_frame, text="Terminal", padding="5")
            terminal_frame.pack(fill=tk.BOTH, expand=True)
            
            # Terminal
            terminal_scroll = ttk.Scrollbar(terminal_frame)
            terminal_scroll.pack(side=tk.RIGHT, fill=tk.Y)
            
            terminal = tk.Text(terminal_frame,
                             wrap=tk.WORD,
                             yscrollcommand=terminal_scroll.set,
                             bg='black',
                             fg='white',
                             font=('Consolas', 10),
                             height=20)
            terminal.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            terminal_scroll.config(command=terminal.yview)
            
            # Configura o terminal como somente leitura
            terminal.config(state='disabled')
            
            # Função para adicionar texto ao terminal
            def append_to_terminal(text, color='white'):
                try:
                    if multi_url_window.winfo_exists() and terminal.winfo_exists():
                        terminal.config(state='normal')
                        terminal.tag_configure(color, foreground=color)
                        terminal.insert(tk.END, f"{text}\n", color)
                        terminal.see(tk.END)
                        terminal.config(state='disabled')
                        terminal.update_idletasks()
                except Exception as e:
                    print(f"Erro ao atualizar terminal: {str(e)}")

            # Variável para controlar o cancelamento
            cancel_process = False
            
            # Função para atualizar a interface de forma segura
            def safe_update_interface(text, progress=None):
                try:
                    if multi_url_window.winfo_exists():
                        if text:
                            status_label.config(text=text)
                            append_to_terminal(text)
                        if progress is not None:
                            progress_var.set(progress)
                            progress_label.config(text=f"{progress:.1f}%")
                        multi_url_window.update_idletasks()
                except Exception as e:
                    print(f"Erro ao atualizar interface: {str(e)}")
            
            # Função para processar os links
            def process_links():
                nonlocal cancel_process
                cancel_process = False
                
                try:
                    # Cria uma nova conexão com o banco de dados para esta thread
                    thread_conn = sqlite3.connect('videos.db')
                    thread_cursor = thread_conn.cursor()
                    
                    # Verifica se a tabela existe, se não, cria
                    thread_cursor.execute('''
                        CREATE TABLE IF NOT EXISTS videos (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT NOT NULL,
                            url TEXT NOT NULL UNIQUE,
                            type TEXT NOT NULL,
                            season TEXT NOT NULL,
                            username TEXT,
                            downloaded INTEGER DEFAULT 0
                        )
                    ''')
                    thread_conn.commit()
                    
                    # Verifica o tamanho inicial do banco
                    thread_cursor.execute("SELECT COUNT(*) FROM videos")
                    initial_count = thread_cursor.fetchone()[0]
                    if multi_url_window.winfo_exists():
                        append_to_terminal(f"Total de vídeos no banco antes: {initial_count}", 'cyan')
                    
                    # Obtém os links
                    links = text_area.get("1.0", tk.END).strip().split("\n")
                    links = [link.strip() for link in links if link.strip()]
                    
                    if not links:
                        if multi_url_window.winfo_exists():
                            safe_update_interface("Nenhum link encontrado!", 'yellow')
                        return
                    
                    # Desabilita os botões durante o processamento
                    if multi_url_window.winfo_exists():
                        if process_button.winfo_exists():
                            process_button.config(state="disabled")
                        if cancel_button.winfo_exists():
                            cancel_button.config(state="normal")
                    
                    total_links = len(links)
                    if multi_url_window.winfo_exists():
                        append_to_terminal(f"Iniciando download de {total_links} links M3U...", 'cyan')
                    
                    # Configuração otimizada do requests
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                        "Accept": "*/*",
                        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
                        "Connection": "keep-alive",
                        "Cache-Control": "no-cache",
                        "Pragma": "no-cache"
                    }
                    
                    # Baixa todas as M3U em paralelo
                    m3u_contents = {}  # Dicionário para armazenar conteúdo por URL
                    failed_downloads = []  # Lista para armazenar URLs que falharam
                    
                    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                        future_to_url = {executor.submit(requests.get, url, headers=headers, timeout=30, verify=False): url 
                                       for url in links}
                        
                        for future in concurrent.futures.as_completed(future_to_url):
                            url = future_to_url[future]
                            try:
                                response = future.result()
                                response.raise_for_status()
                                m3u_contents[url] = response.text.splitlines()
                                if multi_url_window.winfo_exists():
                                    append_to_terminal(f"Download concluído: {url}", 'green')
                            except Exception as e:
                                failed_downloads.append(url)  # Adiciona ao log de falhas
                                if multi_url_window.winfo_exists():
                                    append_to_terminal(f"Erro ao baixar {url}: {str(e)}", 'red')
                    
                    if not m3u_contents:
                        if multi_url_window.winfo_exists():
                            safe_update_interface("Nenhum conteúdo encontrado nos links!", 'red')
                        return
                    
                    if multi_url_window.winfo_exists():
                        append_to_terminal(f"\nProcessando {sum(len(content) for content in m3u_contents.values())} linhas...", 'cyan')
                    
                    # Desabilita temporariamente as restrições do banco de dados
                    thread_cursor.execute("PRAGMA foreign_keys=OFF")
                    thread_cursor.execute("PRAGMA synchronous=OFF")
                    thread_cursor.execute("PRAGMA journal_mode=MEMORY")
                    
                    # Prepara a query de inserção em lote
                    insert_query = '''
                        INSERT OR IGNORE INTO videos (name, url, type, season, username)
                        VALUES (?, ?, ?, ?, ?)
                    '''
                    
                    # Lista para armazenar os dados em lote
                    batch_data = []
                    batch_size = 1000
                    total_processed = 0
                    total_added = 0
                    last_save = 0
                    
                    # Processa cada M3U separadamente
                    for m3u_url, content in m3u_contents.items():
                        if cancel_process:
                            break
                            
                        if multi_url_window.winfo_exists():
                            append_to_terminal(f"\nProcessando M3U: {m3u_url}", 'cyan')
                        
                        # Processa em chunks para melhor performance
                        chunk_size = 10000
                        for i in range(0, len(content), chunk_size):
                            if cancel_process:
                                break
                                
                            chunk = content[i:i + chunk_size]
                            progress = (i / len(content)) * 100
                            
                            # Atualiza a interface em uma thread separada
                            def update_ui():
                                if multi_url_window.winfo_exists():
                                    safe_update_interface(f"Processando chunk {i//chunk_size + 1}...", progress)
                            
                            threading.Thread(target=update_ui, daemon=True).start()
                            
                            # Processa o chunk
                            for j in range(len(chunk)):
                                if chunk[j].startswith("#EXTINF:"):
                                    try:
                                        # Extrai informações do vídeo
                                        name = None
                                        if 'tvg-name="' in chunk[j]:
                                            name = chunk[j].split('tvg-name="')[1].split('"')[0]
                                        elif ',' in chunk[j]:
                                            name = chunk[j].split(',', 1)[1].strip()
                                        
                                        if not name or j + 1 >= len(chunk):
                                            continue
                                            
                                        url_video = chunk[j + 1].strip()
                                        if not url_video or url_video.startswith('#'):
                                            continue
                                        
                                        # Determina o tipo e temporada
                                        content_type = "Filme"
                                        season = "-"
                                        
                                        match = re.search(r"(.*?)\s*(S\d{2})\s*E\d{2}", name)
                                        if match:
                                            content_type = "Série"
                                            season = match.group(2)
                                        
                                        total_processed += 1
                                        batch_data.append((name, url_video, content_type, season, m3u_url))
                                        
                                        # Quando o lote atinge o tamanho definido, insere no banco
                                        if len(batch_data) >= batch_size:
                                            thread_cursor.executemany(insert_query, batch_data)
                                            thread_conn.commit()
                                            total_added += len(batch_data)
                                            batch_data = []
                                            
                                        # Salva a cada 10% do progresso
                                        current_progress = (i + j) / len(content) * 100
                                        if current_progress - last_save >= 10:
                                            thread_conn.commit()
                                            last_save = current_progress
                                            
                                            # Atualiza o terminal em uma thread separada
                                            def update_terminal():
                                                if multi_url_window.winfo_exists():
                                                    append_to_terminal(f"Progresso: {current_progress:.1f}% - Salvando...", 'cyan')
                                            
                                            threading.Thread(target=update_terminal, daemon=True).start()
                                            
                                    except Exception as e:
                                        if multi_url_window.winfo_exists():
                                            append_to_terminal(f"Erro ao processar item: {str(e)}", 'red')
                                        continue
                    
                    # Insere o lote restante
                    if batch_data:
                        thread_cursor.executemany(insert_query, batch_data)
                        thread_conn.commit()
                        total_added += len(batch_data)
                    
                    # Reativa as restrições do banco de dados
                    thread_cursor.execute("PRAGMA foreign_keys=ON")
                    thread_cursor.execute("PRAGMA synchronous=NORMAL")
                    thread_cursor.execute("PRAGMA journal_mode=DELETE")
                    
                    # Verifica o tamanho final do banco
                    thread_cursor.execute("SELECT COUNT(*) FROM videos")
                    final_count = thread_cursor.fetchone()[0]
                    
                    # Atualiza interface após conclusão
                    if multi_url_window.winfo_exists():
                        if process_button.winfo_exists():
                            process_button.config(state="normal")
                        if cancel_button.winfo_exists():
                            cancel_button.config(state="disabled")
                    
                    if not cancel_process:
                        if multi_url_window.winfo_exists():
                            append_to_terminal(f"\n{'='*50}", 'cyan')
                            append_to_terminal("RESUMO DO PROCESSAMENTO", 'cyan')
                            append_to_terminal(f"{'='*50}", 'cyan')
                            append_to_terminal(f"Total de vídeos no banco antes: {initial_count}", 'cyan')
                            append_to_terminal(f"Total de vídeos no banco após: {final_count}", 'cyan')
                            append_to_terminal(f"Novos vídeos adicionados: {final_count - initial_count}", 'green')
                            append_to_terminal(f"Total de itens processados: {total_processed}", 'yellow')
                            append_to_terminal(f"{'='*50}\n", 'cyan')
                            
                            final_msg = (f"Processamento concluído!\n"
                                       f"Total processado: {total_processed}\n"
                                       f"Novos itens: {total_added}\n"
                                       f"Total no banco: {final_count}")
                            safe_update_interface(final_msg, 'green')
                            
                            if total_processed > 0:
                                # Aguarda 3 segundos antes de fechar
                                multi_url_window.after(3000, multi_url_window.destroy)

                    # Cria um log das falhas após o processamento
                    if failed_downloads:
                        with open('failed_downloads.log', 'w') as log_file:
                            log_file.write("Playlists que falharam ao serem baixadas:\n")
                            for failed_url in failed_downloads:
                                log_file.write(f"{failed_url}\n")
                            append_to_terminal("Log de falhas criado: failed_downloads.log", 'yellow')
                
                finally:
                    # Garante que todas as alterações foram salvas
                    try:
                        thread_conn.commit()
                    except:
                        pass
                    # Fecha a conexão da thread
                    thread_conn.close()
            
            def cancel_processing():
                nonlocal cancel_process
                cancel_process = True
                safe_update_interface("Cancelando...", 'yellow')
                append_to_terminal("Cancelando processamento...", 'yellow')
                if multi_url_window.winfo_exists():
                    cancel_button.config(state="disabled")
            
            # Botões
            process_button = ttk.Button(button_frame, 
                                      text="Processar Links", 
                                      command=lambda: threading.Thread(target=process_links).start())
            process_button.pack(side=tk.RIGHT, padx=5)
            
            cancel_button = ttk.Button(button_frame, 
                                     text="Cancelar", 
                                     command=cancel_processing,
                                     state="disabled")
            cancel_button.pack(side=tk.RIGHT, padx=5)
            
            # Torna a janela modal
            multi_url_window.transient(self.root)
            multi_url_window.grab_set()
            
            # Centraliza a janela
            multi_url_window.update_idletasks()
            width = multi_url_window.winfo_width()
            height = multi_url_window.winfo_height()
            x = (multi_url_window.winfo_screenwidth() // 2) - (width // 2)
            y = (multi_url_window.winfo_screenheight() // 2) - (height // 2)
            multi_url_window.geometry(f'+{x}+{y}')
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir janela de múltiplos links: {str(e)}")
            
    def init_database(self):
        """Inicializa o banco de dados e carrega na memória"""
        try:
            # Verifica se o arquivo do banco existe
            db_exists = os.path.exists('videos.db')
            
            # Conecta ao banco de dados com configurações otimizadas
            self.conn = sqlite3.connect('videos.db')
            self.cursor = self.conn.cursor()
            
            # Otimizações para carregamento rápido
            self.cursor.execute("PRAGMA synchronous = OFF")
            self.cursor.execute("PRAGMA journal_mode = MEMORY")
            self.cursor.execute("PRAGMA cache_size = -5000000")  # 5GB de cache
            self.cursor.execute("PRAGMA temp_store = MEMORY")
            
            # Cria tabela se não existir
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS videos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    url TEXT NOT NULL UNIQUE,
                    type TEXT NOT NULL,
                    season TEXT NOT NULL,
                    username TEXT,
                    downloaded INTEGER DEFAULT 0
                )
            ''')
            
            self.conn.commit()
            
            print("Banco de dados inicializado com sucesso")
            
            # Apenas verifica a quantidade de registros sem carregar todos os dados
            self.cursor.execute('SELECT COUNT(*) FROM videos')
            total_records = self.cursor.fetchone()[0]
            
            if not db_exists:
                print("Banco de dados criado com sucesso")
            else:
                print(f"Banco de dados conectado com sucesso. Total de registros: {total_records}")
            
        except Exception as e:
            print(f"Erro ao inicializar banco de dados: {str(e)}")
            raise

    def run(self):
        """Inicia o programa"""
        self.root.mainloop()

    def sort_treeview(self, col):
        """Ordena a Treeview pela coluna clicada"""
        # Obtém todos os itens
        items = [(self.tree.set(item, col), item) for item in self.tree.get_children('')]
        
        # Se clicou na mesma coluna, inverte a ordem
        if self.last_sort_column == col:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_reverse = False
            self.last_sort_column = col
        
        # Ordena os itens
        items.sort(reverse=self.sort_reverse)
        
        # Reordena os itens na Treeview
        for index, (val, item) in enumerate(items):
            self.tree.move(item, '', index)
            
        # Atualiza o indicador de ordenação nas colunas
        for column in self.tree['columns']:
            if column == col:
                self.tree.heading(column, text=f"{column} {'↓' if self.sort_reverse else '↑'}")
            else:
                self.tree.heading(column, text=column)

    def copy_selected_link(self):
        """Copia o link do vídeo selecionado para a área de transferência"""
        url = self.get_url_from_selection()
        if not url:
            messagebox.showinfo("Aviso", "Por favor, selecione um vídeo da lista.")
            return
            
        self.root.clipboard_clear()
        self.root.clipboard_append(url)
        messagebox.showinfo("Sucesso", "Link copiado para a área de transferência!")
    
    def open_selected_in_browser(self):
        """Abre o vídeo selecionado na lista no navegador"""
        url = self.get_url_from_selection()
        if not url:
            messagebox.showinfo("Aviso", "Por favor, selecione um vídeo da lista.")
            return
            
        webbrowser.open(url)

    def change_theme(self, theme_name):
        """Muda o tema da aplicação"""
        try:
            self.root.set_theme(theme_name)
            # Salva a configuração automaticamente
            self.save_config()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao mudar o tema: {e}")

    def change_player(self, player_name):
        """Muda o player da aplicação"""
        self.player_type = player_name
        if player_name == "MPV":
            self.mpv_process = subprocess.Popen([self.mpv_path])
        else:
            self.player.stop()
            self.is_playing = False
            self.play_button.configure(text="▶")
            self.video_progress.set(0)
            self.time_label.configure(text="00:00 / 00:00")

    def change_user_agent(self, choice):
        """
        Gerencia a mudança de User-Agent.
        - Se for "Custom...", mostra campo para entrada personalizada
        - Caso contrário, define o User-Agent selecionado
        """
        if choice == "Custom...":
            # Mostra campo para User-Agent personalizado
            self.ua_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            self.ua_entry.bind("<Return>", lambda e: self.set_custom_user_agent())
        else:
            # Esconde campo personalizado e define User-Agent
            self.ua_entry.pack_forget()
            self.user_agent.set(choice)
            self.save_config()  # Salva a configuração automaticamente
            
    def set_custom_user_agent(self):
        """
        Define um User-Agent personalizado.
        - Obtém o valor do campo de entrada
        - Remove espaços em branco
        - Define como User-Agent atual
        """
        custom_ua = self.ua_entry.get().strip()
        if custom_ua:
            self.user_agent.set(custom_ua)
            self.ua_entry.pack_forget()
            self.save_config()  # Salva a configuração automaticamente

    def carregar_m3u_local(self):
        """Carrega dados de um arquivo M3U local"""
        file_path = filedialog.askopenfilename(
            title="Selecione o arquivo M3U",
            filetypes=[("Arquivos M3U", "*.m3u"), ("Todos os arquivos", "*.*")]
        )
        if not file_path:
            return

        def process_m3u_local():
            try:
                # Lê o arquivo M3U
                with open(file_path, 'r', encoding='utf-8') as file:
                    linhas = file.readlines()
                
                # Limpa a lista de dados M3U e dados do banco
                self.dados_m3u = []
                self.dados_db = []  # Limpa dados do banco para evitar duplicatas na pesquisa
                
                # Processa cada linha
                nome = None
                total_items = 0
                
                for i, linha in enumerate(linhas):
                    linha = linha.strip()
                    if linha.startswith('#EXTINF:'):
                        # Extrai o nome do cabeçalho EXTINF
                        if 'tvg-name="' in linha:
                            nome = re.search('tvg-name="([^"]*)"', linha)
                            if nome:
                                nome = nome.group(1)
                        if not nome and ',' in linha:
                            nome = linha.split(',', 1)[1].strip()
                    elif linha and not linha.startswith('#') and nome:
                        # Esta é a linha da URL
                        tipo = "Filme"
                        temporada = "None"
                        
                        # Verifica se é uma série
                        if nome:
                            match = re.search(r"(.*?)\s*(S\d{2})\s*E\d{2}", nome)
                            if match:
                                tipo = "Série"
                                temporada = match.group(2)
                        
                        # Extrai servidor e username da URL
                        servidor, username = self.extrair_servidor_e_username(linha)
                        
                        # Adiciona aos dados M3U
                        self.dados_m3u.append((nome, tipo, temporada, servidor, username, linha))
                        total_items += 1
                        nome = None  # Reset para próximo item
                
                # Atualiza a interface na thread principal
                self.root.after(0, lambda: self.atualizar_interface())
                self.root.after(0, lambda: messagebox.showinfo("Sucesso", 
                    f"Arquivo M3U local carregado com sucesso!\nTotal de itens: {total_items}"))
                
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Erro", 
                    f"Erro ao carregar arquivo M3U local: {str(e)}"))
        
        # Inicia o processamento em uma thread separada
        threading.Thread(target=process_m3u_local, daemon=True).start()

    def atualizar_interface(self):
        """Atualiza a interface com os dados atuais"""
        # Limpa a Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Contador para numeração
        contador = 1
        
        # Adiciona os dados M3U
        for item in self.dados_m3u:
            # Ordem: Nº, Nome, Tipo, Temporada, Servidor, Link de Origem
            self.tree.insert('', 'end', values=(contador, item[0], item[1], item[2], item[3], item[5]))
            contador += 1
        
        # Se não houver dados M3U mas houver dados do banco, mostra os dados do banco
        if not self.dados_m3u and self.dados_db:
            for item in self.dados_db:
                servidor, username = self.extrair_servidor_e_username(item[2])
                self.tree.insert('', 'end', values=(contador, item[1], item[3], item[4], servidor, item[2]))
                contador += 1

    def __del__(self):
        """Destrutor da classe - garante que a conexão seja fechada corretamente"""
        try:
            if hasattr(self, 'conn') and self.conn:
                self.conn.commit()
                self.conn.close()
                print("Conexão com o banco fechada corretamente")
        except Exception as e:
            print(f"Erro ao fechar conexão: {str(e)}")

    def atualizar_cache(self, nome, dados):
        """Atualiza o cache em memória com novos dados"""
        if self.db_cache_loaded:
            self.db_cache[nome] = dados

    def remover_do_cache(self, nome):
        """Remove um item do cache em memória"""
        if self.db_cache_loaded and nome in self.db_cache:
            del self.db_cache[nome]

    def inserir_no_banco(self, nome, url, tipo, temporada, username=None):
        """Insere um novo registro no banco e atualiza o cache"""
        try:
            # Garante que temporada não seja None
            if temporada is None:
                temporada = "-"  # Valor padrão quando não há temporada
            
            # Verifica se o vídeo já existe
            self.cursor.execute('SELECT COUNT(*) FROM videos WHERE name = ?', (nome,))
            if self.cursor.fetchone()[0] > 0:
                # Se existir, atualiza
                self.cursor.execute('''
                    UPDATE videos 
                    SET url = ?, type = ?, season = ?, username = ?
                    WHERE name = ?
                ''', (url, tipo, temporada, username, nome))
            else:
                # Se não existir, insere
                self.cursor.execute('''
                    INSERT INTO videos (name, url, type, season, username)
                    VALUES (?, ?, ?, ?, ?)
                ''', (nome, url, tipo, temporada, username))
            
            self.conn.commit()
            
            # Atualiza o cache
            if self.db_cache_loaded:
                self.cursor.execute('SELECT * FROM videos WHERE name = ?', (nome,))
                novo_registro = self.cursor.fetchone()
                if novo_registro:
                    self.atualizar_cache(nome, novo_registro)
            
            return True
        except Exception as e:
            print(f"Erro ao inserir/atualizar no banco: {str(e)}")
            return False

    def atualizar_no_banco(self, nome, url, tipo, temporada, username=None):
        """Atualiza um registro existente no banco e no cache"""
        try:
            # Garante que temporada não seja None
            if temporada is None:
                temporada = "-"  # Valor padrão quando não há temporada
                
            self.cursor.execute('''
                UPDATE videos 
                SET url = ?, type = ?, season = ?, username = ?
                WHERE name = ?
            ''', (url, tipo, temporada, username, nome))
            self.conn.commit()
            
            # Atualiza o cache
            if self.db_cache_loaded and nome in self.db_cache:
                registro_atual = self.db_cache[nome]
                novo_registro = (registro_atual[0], nome, url, tipo, temporada, username, registro_atual[6])
                self.atualizar_cache(nome, novo_registro)
            
            return True
        except Exception as e:
            print(f"Erro ao atualizar no banco: {str(e)}")
            return False

    def deletar_do_banco(self, nome):
        """Remove um registro do banco e do cache"""
        try:
            self.cursor.execute('DELETE FROM videos WHERE name = ?', (nome,))
            self.conn.commit()
            
            # Remove do cache
            self.remover_do_cache(nome)
            
            return True
        except Exception as e:
            print(f"Erro ao deletar do banco: {str(e)}")
            return False

    def download_selected_advanced(self):
        """Inicia o download avançado dos itens selecionados"""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("Aviso", "Por favor, selecione um vídeo para download.")
            return

        download_path = self.download_path.get()
        if not os.path.exists(download_path):
            messagebox.showerror("Erro", "Pasta de download inválida.")
            return

        # Cria uma instância do AdvancedDownloader se não existir
        if not hasattr(self, 'advanced_downloader') or not self.advanced_downloader:
            self.advanced_downloader = AdvancedDownloader(
                self.root,
                download_path,
                self.user_agent.get(),
                self.dns_server.get()
            )

        # Configura o modo reserva
        self.advanced_downloader.set_reserva_mode(self.reserva_mode)

        # Configura o uso de apenas aria2
        self.advanced_downloader.set_use_only_aria2(self.use_only_aria2_var.get())

        # Passa os widgets de progresso
        self.advanced_downloader.set_progress_widgets(
            self.progress_label,
            self.speed_label,
            self.download_info_label
        )

        # Passa a janela da fila de downloads se estiver aberta
        if self.download_queue_window and self.download_queue_window.window.winfo_exists():
            self.advanced_downloader.set_download_queue_window(self.download_queue_window)

        # Adiciona os vídeos selecionados à fila
        for item in selected_items:
            values = self.tree.item(item)['values']
            nome_video = values[1]
            url = self.get_url_from_selection(item)
            
            if url:
                self.advanced_downloader.add_to_queue(nome_video, url, download_path)
            else:
                messagebox.showwarning("Aviso", f"URL não encontrada para o vídeo: {nome_video}")

        # Inicia o processamento da fila se não houver download em andamento
        if not self.advanced_downloader.is_downloading:
            self.advanced_downloader.process_download_queue()

    def add_to_download_queue(self):
        """Adiciona itens selecionados à fila de download atual"""
        if not hasattr(self, 'advanced_downloader') or not self.advanced_downloader:
            messagebox.showwarning("Aviso", "Nenhum download em andamento.")
            return

        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("Aviso", "Por favor, selecione um vídeo para adicionar à fila.")
            return

        download_path = self.download_path.get()
        if not os.path.exists(download_path):
            messagebox.showerror("Erro", "Pasta de download inválida.")
            return

        # Adiciona os vídeos selecionados à fila
        for item in selected_items:
            values = self.tree.item(item)['values']
            nome_video = values[1]
            url = self.get_url_from_selection(item)
            
            if url:
                self.advanced_downloader.download_queue.append((nome_video, url, download_path))
                messagebox.showinfo("Sucesso", f"Vídeo '{nome_video}' adicionado à fila de download.")
            else:
                messagebox.showwarning("Aviso", f"URL não encontrada para o vídeo: {nome_video}")

    def toggle_use_only_aria2(self):
        """Alterna o uso de apenas aria2 ou todos os protocolos"""
        if hasattr(self, 'advanced_downloader'):
            self.advanced_downloader.set_use_only_aria2(self.use_only_aria2_var.get())

    def rewind_video(self):
        """Retrocede 10 segundos no vídeo"""
        if self.player_type == "vlc":
            if self.player.is_playing():
                current_time = self.player.get_time()
                self.player.set_time(max(0, current_time - 10000))  # 10 segundos
        else:  # MPV
            if self.mpv_process:
                subprocess.run([self.mpv_path, '--input-ipc-server=/tmp/mpv-socket', 'seek', '-10'], check=False)

    def forward_video(self):
        """Avança 10 segundos no vídeo"""
        if self.player_type == "vlc":
            if self.player.is_playing():
                current_time = self.player.get_time()
                total_time = self.player.get_length()
                self.player.set_time(min(total_time, current_time + 10000))  # 10 segundos
        else:  # MPV
            if self.mpv_process:
                subprocess.run([self.mpv_path, '--input-ipc-server=/tmp/mpv-socket', 'seek', '10'], check=False)

    def toggle_reserva_mode(self):
        """Alterna o modo reserva"""
        self.reserva_mode = self.reserva_var.get()
        if self.reserva_mode:
            # Desativa aria2 quando em modo reserva
            self.use_only_aria2_var.set(False)
            self.use_only_aria2_checkbox.configure(state="disabled")
        else:
            # Reativa aria2 quando sai do modo reserva
            self.use_only_aria2_checkbox.configure(state="normal")

    def retomar_downloads(self):
        """Retoma todos os downloads incompletos"""
        try:
            # Verifica se o aria2 está disponível
            if not hasattr(self, 'aria2'):
                messagebox.showerror("Erro", "aria2 não está disponível")
                return

            # Obtém todos os downloads ativos e pausados
            downloads = self.aria2.get_downloads()
            downloads_incompletos = [d for d in downloads if d.status != "complete"]

            if not downloads_incompletos:
                messagebox.showinfo("Informação", "Não há downloads para retomar")
                return

            # Retoma cada download incompleto
            for download in downloads_incompletos:
                try:
                    # Obtém o nome do arquivo
                    nome_arquivo = download.files[0].path.split('/')[-1]
                    
                    # Remove a extensão para obter o nome do vídeo
                    nome_video = os.path.splitext(nome_arquivo)[0]
                    
                    # Obtém a URL do download
                    url = download.files[0].uris[0].uri
                    
                    # Adiciona à fila de download
                    self.advanced_downloader.download_queue.append((nome_video, url, self.download_path.get()))
                    
                    # Retoma o download
                    download.resume()
                    
                except Exception as e:
                    print(f"Erro ao retomar download {nome_arquivo}: {str(e)}")
                    continue

            # Inicia o processamento da fila se não estiver em andamento
            if not self.advanced_downloader.is_downloading:
                self.advanced_downloader.process_download_queue()

            messagebox.showinfo("Sucesso", f"{len(downloads_incompletos)} downloads retomados")

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao retomar downloads: {str(e)}")

    def show_download_queue(self):
        """Mostra a janela da fila de downloads"""
        if not self.download_queue_window or not self.download_queue_window.window.winfo_exists():
            self.download_queue_window = DownloadQueueWindow(self.root)
        else:
            self.download_queue_window.window.lift()

if __name__ == "__main__":
    app = PesquisaPlaylist()
    app.run()