import os
import time
import subprocess
import requests
import tkinter as tk
from tkinter import messagebox
import threading
from threading import Thread
import aria2p
import shutil

class AdvancedDownloader:
    def __init__(self, root, download_path, user_agent, dns_server):
        self.root = root
        self.download_path = download_path
        self.user_agent = user_agent
        self.dns_server = dns_server
        self.download_queue = []
        self.is_downloading = False
        self.cancel_download = False
        self.use_only_aria2 = True  # Por padrão, usa apenas aria2
        self.reserva_mode = False  # Novo: controla o modo reserva
        
        # Inicializa aria2
        self.aria2 = aria2p.API(aria2p.Client(host="http://localhost", port=6800))
        
        # Verifica se os programas estão instalados
        self.curl_available = shutil.which("curl") is not None
        self.wget_available = shutil.which("wget") is not None
        
        # Protocolos disponíveis
        self.available_protocols = ["aria2"]
        if self.curl_available:
            self.available_protocols.append("curl")
        if self.wget_available:
            self.available_protocols.append("wget")
        self.available_protocols.append("requests")

        # Variáveis para progresso
        self.download_progress = tk.DoubleVar()
        self.download_progress.set(0.0)
        self.progress_label = None
        self.speed_label = None
        self.download_info_label = None

    def set_progress_widgets(self, progress_label, speed_label, download_info_label):
        """Define os widgets de progresso"""
        self.progress_label = progress_label
        self.speed_label = speed_label
        self.download_info_label = download_info_label

    def set_use_only_aria2(self, value):
        """Define se deve usar apenas aria2 ou todos os protocolos"""
        self.use_only_aria2 = value

    def set_reserva_mode(self, value):
        """Define o modo reserva"""
        self.reserva_mode = value

    def download_selected(self, items):
        """Inicia o download avançado dos itens selecionados"""
        if not items:
            messagebox.showwarning("Aviso", "Por favor, selecione um vídeo para download.")
            return

        if not os.path.exists(self.download_path):
            messagebox.showerror("Erro", "Pasta de download inválida.")
            return

        # Adiciona os vídeos selecionados à fila
        for item in items:
            values = item['values']
            nome_video = values[1]
            url = values[5]  # URL está na coluna 5
            
            if url:
                self.download_queue.append((nome_video, url, self.download_path))
            else:
                messagebox.showwarning("Aviso", f"URL não encontrada para o vídeo: {nome_video}")

        # Inicia o processamento da fila
        if not self.is_downloading:
            self.process_download_queue()

    def process_download_queue(self):
        """Processa a fila de downloads"""
        if not self.download_queue:
            self.is_downloading = False
            return

        self.is_downloading = True
        name, url, path = self.download_queue.pop(0)
        Thread(target=self.download_video, args=(name, url, path)).start()

    def get_file_extension(self, url):
        """Detecta a extensão do arquivo a partir da URL"""
        # Tenta extrair a extensão da URL
        extension = os.path.splitext(url)[1].lower()
        
        # Se não encontrou extensão na URL, tenta detectar pelo Content-Type
        if not extension:
            try:
                response = requests.head(url, headers={'User-Agent': self.user_agent})
                content_type = response.headers.get('Content-Type', '').lower()
                
                if 'video/mp4' in content_type:
                    extension = '.mp4'
                elif 'video/x-matroska' in content_type or 'video/mkv' in content_type:
                    extension = '.mkv'
                elif 'video/quicktime' in content_type:
                    extension = '.mov'
                elif 'video/x-msvideo' in content_type:
                    extension = '.avi'
                else:
                    # Se não conseguir detectar, usa .mp4 como padrão
                    extension = '.mp4'
            except:
                # Em caso de erro, usa .mp4 como padrão
                extension = '.mp4'
        
        return extension

    def download_video(self, nome_video, url, download_path):
        """Tenta baixar o vídeo usando os protocolos disponíveis"""
        if self.reserva_mode:
            return self.download_with_webclient(nome_video, url, download_path)
        
        try:
            self.cancel_download = False
            
            # Extrai o nome do conteúdo e a temporada
            content_name, season = self.extract_content_info(nome_video)

            # Cria a pasta do conteúdo
            content_folder = os.path.join(download_path, content_name)
            if not os.path.exists(content_folder):
                os.makedirs(content_folder)

            # Obtém a extensão correta do arquivo
            extension = self.get_file_extension(url)

            # Se for uma série, cria a pasta da temporada
            if season:
                season_folder = os.path.join(content_folder, season)
                if not os.path.exists(season_folder):
                    os.makedirs(season_folder)
                file_path = os.path.join(season_folder, f"{nome_video}{extension}")
            else:
                file_path = os.path.join(content_folder, f"{nome_video}{extension}")

            # Verifica se o arquivo já existe
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                file_size_mb = file_size / (1024 * 1024)  # Converte para MB
                
                # Pergunta ao usuário o que fazer
                response = messagebox.askyesnocancel(
                    "Arquivo Existente",
                    f"O arquivo '{nome_video}' já existe ({file_size_mb:.2f} MB).\n"
                    "Deseja sobrescrever o arquivo existente?\n"
                    "Sim = Sobrescrever\n"
                    "Não = Pular este download\n"
                    "Cancelar = Cancelar todos os downloads"
                )
                
                if response is None:  # Cancelar
                    self.cancel_download = True
                    return
                elif not response:  # Não (Pular)
                    messagebox.showinfo("Download Pulado", f"Download de '{nome_video}' foi pulado.")
                    return
                # Se Sim, continua com o download normalmente

            # Modo normal: tenta diferentes protocolos em ordem
            success = False
            protocols_to_try = ["aria2"] if self.use_only_aria2 else self.available_protocols
            
            for protocol in protocols_to_try:
                if self.cancel_download:
                    break
                    
                try:
                    if protocol == "aria2":
                        success = self.download_with_aria2(url, file_path, nome_video)
                    elif protocol == "curl" and self.curl_available:
                        success = self.download_with_curl(url, file_path, nome_video)
                    elif protocol == "wget" and self.wget_available:
                        success = self.download_with_wget(url, file_path, nome_video)
                    elif protocol == "requests":
                        success = self.download_with_requests(url, file_path, nome_video)
                    
                    if success:
                        break
                except Exception as e:
                    print(f"Erro com protocolo {protocol}: {str(e)}")
                    continue

            if not success:
                messagebox.showerror("Erro", f"Falha ao baixar {nome_video} com todos os protocolos disponíveis")

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao baixar {nome_video}: {e}")
        finally:
            # Processa o próximo download na fila
            self.root.after(1000, self.process_download_queue)

    def download_with_aria2(self, url, file_path, name):
        """Download usando aria2"""
        try:
            # Verifica se o arquivo existe e está incompleto
            file_exists = os.path.exists(file_path)
            file_size = os.path.getsize(file_path) if file_exists else 0
            
            options = {
                "dir": os.path.dirname(file_path),
                "out": os.path.basename(file_path),
                "max-connection-per-server": "16",
                "split": "16",
                "user-agent": self.user_agent,
                "continue": "true",
                "max-concurrent-downloads": "1",
                "auto-file-renaming": "false"  # Desativa renomeação automática
            }

            if self.dns_server:
                options["dns-server"] = self.dns_server

            # Se o arquivo existe, adiciona o tamanho atual como ponto de partida
            if file_exists:
                options["continue"] = "true"
                options["file-allocation"] = "none"  # Evita realocação de arquivo
                options["allow-overwrite"] = "true"

            # Atualiza o label de informação
            if self.download_info_label:
                self.download_info_label.configure(text=f"Baixando: {name}")

            download = self.aria2.add_uris([url], options=options)
            
            # Variáveis para controle de progresso
            last_progress = 0
            no_progress_count = 0
            max_retries = 3
            retry_count = 0
            
            while not self.cancel_download and download.is_active:
                try:
                    download.update()
                    status = download.status
                    downloaded = download.completed_length
                    total = download.total_length
                    
                    if total > 0:
                        progress = (downloaded / total) * 100
                        speed = download.download_speed / (1024 * 1024)  # Converte para MB/s
                        
                        # Atualiza os widgets de progresso
                        if self.download_progress:
                            self.download_progress.set(progress)
                        if self.progress_label:
                            self.progress_label.configure(text=f"{progress:.1f}%")
                        if self.speed_label:
                            self.speed_label.configure(text=f"{speed:.1f} MB/s")
                        
                        # Verifica se o progresso está estagnado
                        if abs(progress - last_progress) < 0.1:
                            no_progress_count += 1
                        else:
                            no_progress_count = 0
                        
                        last_progress = progress
                        
                        # Se o progresso estiver estagnado por muito tempo, tenta retomar
                        if no_progress_count > 30 and retry_count < max_retries:
                            if self.download_info_label:
                                self.download_info_label.configure(text=f"Tentando retomar download: {name}")
                            print(f"Tentando retomar download: {name}")
                            # Não remove o download do aria2, apenas tenta retomar
                            retry_count += 1
                            no_progress_count = 0
                            time.sleep(2)
                    
                    time.sleep(0.1)
                    
                except Exception as e:
                    print(f"Erro durante o download: {str(e)}")
                    if retry_count < max_retries:
                        retry_count += 1
                        time.sleep(2)
                        continue
                    break

            # Atualiza o status final
            if self.cancel_download:
                if self.download_info_label:
                    self.download_info_label.configure(text="Download cancelado")
                # Remove o download do aria2 apenas se foi cancelado
                download.remove(force=True)
            elif download.status == "complete":
                if self.download_info_label:
                    self.download_info_label.configure(text=f"Download concluído: {name}")
                # Remove o download do aria2 apenas se foi concluído
                download.remove(force=True)
            else:
                if self.download_info_label:
                    self.download_info_label.configure(text=f"Download pausado: {name}")
                # Não remove o download do aria2 em caso de falha, permitindo retomada posterior

            # Reseta os widgets de progresso
            if self.download_progress:
                self.download_progress.set(0.0)
            if self.progress_label:
                self.progress_label.configure(text="0%")
            if self.speed_label:
                self.speed_label.configure(text="0 MB/s")

            return download.status == "complete"
        except Exception as e:
            print(f"Erro com aria2: {str(e)}")
            return False

    def download_with_curl(self, url, file_path, name):
        """Download usando curl"""
        try:
            cmd = [
                "curl", "-L", "-C", "-",  # Continua download parcial
                "-A", self.user_agent,    # User-Agent
                "-o", file_path,          # Arquivo de saída
                url                       # URL
            ]
            
            if self.dns_server:
                cmd.extend(["--dns-servers", self.dns_server])
                
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            while process.poll() is None and not self.cancel_download:
                time.sleep(0.1)
                
            if self.cancel_download:
                process.terminate()
                return False
                
            return process.returncode == 0
        except Exception as e:
            print(f"Erro com curl: {str(e)}")
            return False

    def download_with_wget(self, url, file_path, name):
        """Download usando wget"""
        try:
            cmd = [
                "wget", "-c",            # Continua download parcial
                "-U", self.user_agent,   # User-Agent
                "-O", file_path,         # Arquivo de saída
                url                      # URL
            ]
            
            if self.dns_server:
                cmd.extend(["--dns-servers", self.dns_server])
                
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            while process.poll() is None and not self.cancel_download:
                time.sleep(0.1)
                
            if self.cancel_download:
                process.terminate()
                return False
                
            return process.returncode == 0
        except Exception as e:
            print(f"Erro com wget: {str(e)}")
            return False

    def download_with_requests(self, url, file_path, name):
        """Download usando requests"""
        try:
            headers = {
                "User-Agent": self.user_agent
            }
            
            if self.dns_server:
                # Configura DNS para requests (requer dnspython)
                import dns.resolver
                dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
                dns.resolver.default_resolver.nameservers = [self.dns_server]
            
            response = requests.get(url, headers=headers, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            block_size = 1024 * 1024  # 1MB
            
            with open(file_path, 'wb') as f:
                for data in response.iter_content(block_size):
                    if self.cancel_download:
                        return False
                    f.write(data)
                    
            return True
        except Exception as e:
            print(f"Erro com requests: {str(e)}")
            return False

    def download_with_webclient(self, nome_video, url, download_path):
        """Tenta baixar o vídeo usando o WebClient"""
        try:
            # Cria o diretório se não existir
            os.makedirs(download_path, exist_ok=True)
            
            # Obtém a extensão correta do arquivo
            extension = self.get_file_extension(url)
            
            # Define o caminho do arquivo
            file_path = os.path.join(download_path, f"{nome_video}{extension}")
            
            # Configura os headers
            headers = {
                'User-Agent': self.user_agent,
                'Accept': '*/*',
                'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Referer': url,
                'Sec-Fetch-Dest': 'video',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin'
            }
            
            # Faz a requisição
            response = requests.get(url, headers=headers, stream=True)
            response.raise_for_status()
            
            # Obtém o tamanho total do arquivo
            total_size = int(response.headers.get('content-length', 0))
            
            # Inicia o download
            downloaded = 0
            start_time = time.time()
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Atualiza o progresso
                        self.update_progress(downloaded, total_size, start_time)
            
            # Verifica se o arquivo foi baixado corretamente
            if os.path.getsize(file_path) == 0:
                os.remove(file_path)
                raise Exception("Arquivo baixado está vazio")
            
            return True
            
        except Exception as e:
            self.update_progress(0, 0, time.time(), str(e))
            return False

    def update_progress(self, downloaded, total_size, start_time, error=None):
        """Atualiza a interface com o progresso do download"""
        if error:
            self.progress_label.configure(text=f"Erro: {error}")
            self.speed_label.configure(text="")
            self.download_info_label.configure(text="")
            return
        
        if total_size > 0:
            progress = (downloaded / total_size) * 100
            elapsed_time = time.time() - start_time
            speed = downloaded / elapsed_time if elapsed_time > 0 else 0
            
            self.progress_label.configure(text=f"Progresso: {progress:.1f}%")
            self.speed_label.configure(text=f"Velocidade: {self.format_speed(speed)}")
            self.download_info_label.configure(
                text=f"Baixado: {self.format_size(downloaded)} / {self.format_size(total_size)}"
            )
        else:
            self.progress_label.configure(text="Baixando...")
            self.speed_label.configure(text="")
            self.download_info_label.configure(text="")

    def format_speed(self, speed):
        """Formata a velocidade de download"""
        if speed < 1024:
            return f"{speed:.1f} B/s"
        elif speed < 1024 * 1024:
            return f"{speed/1024:.1f} KB/s"
        else:
            return f"{speed/(1024*1024):.1f} MB/s"

    def format_size(self, size):
        """Formata o tamanho do arquivo"""
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size/1024:.1f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size/(1024*1024):.1f} MB"
        else:
            return f"{size/(1024*1024*1024):.1f} GB"

    def _download_with_webclient(self, url, file_path, name):
        """Implementação interna do download com WebClient"""
        try:
            # Configura os headers
            headers = {
                'User-Agent': self.user_agent,
                'Accept': '*/*',
                'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Referer': url,
                'Sec-Fetch-Dest': 'video',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin'
            }
            
            # Faz a requisição
            response = requests.get(url, headers=headers, stream=True)
            response.raise_for_status()
            
            # Obtém o tamanho total do arquivo
            total_size = int(response.headers.get('content-length', 0))
            
            # Inicia o download
            downloaded = 0
            start_time = time.time()
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Atualiza o progresso
                        self.update_progress(downloaded, total_size, start_time)
            
            # Verifica se o arquivo foi baixado corretamente
            if os.path.getsize(file_path) == 0:
                os.remove(file_path)
                raise Exception("Arquivo baixado está vazio")
            
            return True
            
        except Exception as e:
            self.update_progress(0, 0, time.time(), str(e))
            return False

    def extract_content_info(self, name):
        """Extrai informações do conteúdo (nome e temporada)"""
        import re
        match = re.search(r"(.*?)\s*(S\d{2})\s*E\d{2}", name)
        if match:
            content_name = match.group(1).strip()
            season = match.group(2).strip()
            return content_name, season
        else:
            return name, None

    def cancel_current_download(self):
        """Cancela o download atual"""
        self.cancel_download = True 