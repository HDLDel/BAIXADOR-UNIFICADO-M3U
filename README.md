# BAIXADOR-UNIFICADO-M3U# 
Baixador de Vídeos

## Versão 1.13.9

### Novidades
- Correção na criação de diretórios com caracteres especiais (como ":" em "Tekken: Bloodline")
- Melhor tratamento de nomes de arquivos e pastas no Windows
- Melhorias no modo reserva
- Adicionada funcionalidade de adicionar itens à fila durante o download
- Correções de bugs e melhorias de performance

### Funcionalidades
- Download de vídeos de playlists M3U
- Suporte a múltiplos formatos de vídeo
- Organização automática por conteúdo e temporada
- Interface gráfica moderna e intuitiva
- Suporte a temas personalizáveis
- Player de vídeo integrado (VLC/MPV)
- Download avançado com aria2
- Configuração de User-Agent e DNS
- Pesquisa e filtragem de conteúdo
- Banco de dados local para armazenamento de links
- Suporte a múltiplos servidores

### Botões e Funcionalidades

#### Barra de Ferramentas Principal
- **Pesquisar**: Busca vídeos na playlist ou banco de dados
- **Filtrar**: Filtra resultados por nome, temporada ou tipo
- **Atualizar**: Atualiza a lista de vídeos
- **Configurações**: Acessa as configurações do programa

#### Botões de Download
- **Download Normal**: Inicia download usando o método padrão
- **Download Avançado**: Abre opções de download avançado
  - Configuração de conexões simultâneas
  - Configuração de divisão de arquivos
  - Seleção de protocolos de download
  - Configuração de User-Agent
  - Configuração de DNS
- **Adicionar à Fila**: Adiciona vídeo à fila de downloads
- **Pausar/Retomar**: Controla downloads em andamento
- **Cancelar**: Cancela download selecionado

#### Player de Vídeo
- **Reproduzir**: Inicia reprodução do vídeo
- **Pausar**: Pausa a reprodução
- **Parar**: Para a reprodução
- **Avançar**: Avança 10 segundos
- **Retroceder**: Retrocede 10 segundos
- **Volume**: Controle de volume
- **Tela Cheia**: Alterna modo tela cheia

#### Configurações
- **Pasta de Download**: Define local de salvamento
- **Player Preferido**: Seleciona entre VLC e MPV
- **Tema**: Escolhe tema da interface
- **User-Agent**: Configura User-Agent personalizado
- **DNS**: Configura servidor DNS personalizado
- **Modo Reserva**: Ativa/desativa modo de download alternativo
- **Configurações aria2**: Ajusta parâmetros do aria2

### Requisitos
- Python 3.7+
- VLC Media Player ou MPV
- aria2 (para download avançado)
- Bibliotecas Python:
  - tkinter
  - customtkinter
  - vlc
  - aria2p
  - requests
  - unidecode
  - ttkthemes

### Instalação
1. Instale o Python 3.7 ou superior
2. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```
3. Instale o VLC Media Player ou MPV
4. Instale o aria2 (opcional, para download avançado)

### Uso
1. Execute o programa:
   ```
   python pesquisa_playlist.py
   ```
2. Carregue uma playlist M3U ou banco de dados
3. Pesquise e selecione os vídeos desejados
4. Use os botões de download ou player para interagir com os vídeos

### Configurações
- Pasta de download personalizável
- User-Agent configurável
- DNS personalizável
- Temas de interface
- Player preferido (VLC/MPV)
- Configurações avançadas do aria2

### Notas
- O programa agora lida corretamente com caracteres especiais em nomes de arquivos e pastas
- Recomendado usar o download avançado com aria2 para melhor performance
- Mantenha o programa atualizado para novas funcionalidades e correções

## Versões

### Versão 1.13.4 (2024-03-23)
- Melhorias no modo reserva
- Adicionada funcionalidade de adicionar itens à fila durante o download
- Correções de bugs e melhorias de performance

### Versão 1.13.3 (2024-03-22)
- Correção na criação de diretórios com caracteres especiais
- Melhor tratamento de nomes de arquivos e pastas no Windows
- Atualização da documentação

### Versão 1.13.2 (2024-03-21)
- Adicionados botões de avançar e retroceder no player de vídeo
- Melhorias na interface do player
- Correções de bugs menores

### Versão 1.13.1 (2024-03-21)
- Adicionada opção para usar apenas aria2 no download avançado
- Melhorias na interface do download avançado
- Correções de bugs menores

### Versão 1.13 (2024-03-20)
- Adicionado modo de download avançado com suporte a múltiplos protocolos
- Melhor verificação do status dos downloads
- Notificações mais detalhadas sobre o progresso
- Suporte a retomada de downloads interrompidos
- Interface aprimorada com mais informações sobre os downloads

[Versões anteriores...]

## Contribuição

Contribuições são bem-vindas! Por favor, abra uma issue para discutir mudanças ou envie um pull request.

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para detalhes.
