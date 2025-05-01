# Versão 1.13.11

## Histórico de Mudanças

### 1.13.11
- Atualização de versão

### 1.13.10
- Adicionado botão "Retomar Downloads" para retomar downloads incompletos
- Reorganização da interface com botões de ação antes das opções de configuração
- Melhorias no sistema de download com aria2
- Correção no comportamento de remoção de downloads (agora só remove em caso de conclusão ou cancelamento)

### 1.13.9
- Implementação do modo reserva
- Melhorias no sistema de download
- Correções de bugs

### 1.13.8
- Adicionado suporte a múltiplos protocolos de download
- Melhorias na interface do usuário
- Otimizações de performance

# Histórico de Versões

## Versão 1.13.5 (2024-03-23)
Melhorias no aria2.conf

## Versão 1.13.4 (2024-03-23)
- Melhorias no modo reserva
- Adicionada funcionalidade de adicionar itens à fila durante o download
- Correções de bugs e melhorias de performance

## Versão 1.13.3 (2024-03-22)
### Correções
- Corrigido problema na criação de diretórios com caracteres especiais (como ":" em "Tekken: Bloodline")
- Melhorado o tratamento de nomes de arquivos e pastas no Windows
- Adicionada função sanitize_directory_name para remover caracteres inválidos

## Versão 1.13.2 (2024-03-21)
### Novidades
- Adicionados botões de avançar e retroceder no player de vídeo
- Melhorias na interface do player
### Correções
- Ajustes na barra de progresso do vídeo
- Correções de bugs menores na interface

## Versão 1.13.1 (2024-03-21)
### Novidades
- Adicionada opção para usar apenas aria2 no download avançado
- Melhorias na interface do download avançado
### Correções
- Ajustes na configuração do aria2
- Correções de bugs menores no download avançado

## Versão 1.13 (2024-03-20)
### Novidades
- Adicionado modo de download avançado com suporte a múltiplos protocolos
- Melhor verificação do status dos downloads
- Notificações mais detalhadas sobre o progresso
- Suporte a retomada de downloads interrompidos
- Interface aprimorada com mais informações sobre os downloads
### Melhorias
- Otimização do uso de memória
- Melhor tratamento de erros
- Interface mais responsiva

## Versão 1.12 (2024-03-19)
### Novidades
- Adicionado suporte a MPV como player alternativo
- Implementado sistema de temas personalizáveis
- Adicionada opção de DNS personalizado
### Melhorias
- Melhor organização do código
- Otimização do banco de dados
- Interface mais moderna

## Versão 1.11 (2024-03-18)
### Novidades
- Adicionado banco de dados local para armazenamento de links
- Implementada pesquisa avançada
- Adicionado suporte a múltiplos servidores
### Melhorias
- Melhor performance na pesquisa
- Interface mais intuitiva
- Melhor tratamento de erros

## Versão 1.10 (2024-03-17)
### Novidades
- Primeira versão estável
- Interface gráfica básica
- Suporte a playlists M3U
- Download básico de vídeos
- Player de vídeo integrado

## Versão 1.9 (2024-03-20)
- Adicionado modo de download avançado com suporte a múltiplos protocolos (aria2, curl, wget, requests)
- Melhor verificação do status dos downloads
- Notificações mais detalhadas sobre o progresso
- Suporte a retomada de downloads interrompidos
- Interface aprimorada com mais informações sobre os downloads

## Versão 1.8 (2024-03-20)
- Atualizado sistema de versionamento automático para monitorar todos os arquivos do projeto
- Removida lista fixa de arquivos monitorados
- Implementado monitoramento global do repositório Git
- Versionamento automático de qualquer arquivo modificado
- Detecção mais precisa de mudanças usando git status
- Mensagens de commit mais detalhadas com lista de arquivos
- Melhor feedback visual das operações Git
- Detecção e notificação de arquivos não rastreados

## Versão 1.7 (2024-03-20)
- Implementado sistema de versionamento automático com Git
- Adicionado script auto_git.ps1 para monitoramento automático de mudanças
- Monitoramento automático dos arquivos principais do projeto
- Commits automáticos com timestamp e nome do arquivo modificado
- Versionamento automático de:
  * pesquisa_playlist.py
  * aria2.conf
  * config.json
- Feedback visual colorido das operações Git
- Verificação de mudanças não rastreadas
- Tratamento de erros nos commits automáticos

## Versão 1.6 (2024-03-19)
- Modificado o carregamento de arquivos M3U para funcionar apenas em memória
- Melhorado o processamento de arquivos M3U para extrair corretamente os nomes dos canais
- Removida a interação com o banco de dados durante o carregamento de M3U
- Otimizada a pesquisa para trabalhar apenas com dados em memória
- Melhor desempenho no carregamento de arquivos M3U
- Extração mais precisa dos nomes de canais e vídeos
- Pesquisa mais rápida por trabalhar apenas com dados em memória
- Redução do uso do banco de dados

## Versão 1.5 (2024-03-19)
- Adicionado suporte a DNS personalizado para downloads
- Melhorado sistema de User-Agent com opções pré-definidas
- Interface atualizada com novos controles de rede
- Documentação atualizada com novas funcionalidades
- Implementada fila de downloads
- Melhorias na interface do usuário
- Correções de bugs

## Versão 1.4 (2024-03-18)
- Melhorada a função normalize_text para lidar com caracteres especiais
- Adicionado suporte a pontuação e aspas na normalização
- Melhorada a busca para lidar com diferentes formatos de texto
- Adicionado suporte a caracteres latinos e especiais
- Implementada normalização de pontuação
- Melhorado o tratamento de espaços e hífens
- Busca mais flexível com diferentes formatos de texto
- Melhor suporte a caracteres especiais
- Preservação dos caracteres originais na exibição
- Melhorada a performance da normalização de texto

## Versão 1.3 (2024-03-17)
- Melhorado o carregamento de arquivos M3U locais
- Integrada a lógica de inserção diretamente na função
- Adicionada contagem de registros antes e depois da inserção
- Melhorada a mensagem de feedback
- Otimizado o processo de inserção usando executemany
- Adicionada verificação de conexão existente
- Melhorado o tratamento de erros na conexão
- Adicionada verificação de permissões de escrita
- Implementado commit automático após inserções
- Adicionada barra de progresso mais informativa
- Melhoradas mensagens de feedback para o usuário

## Versão 1.2 (2024-03-16)
- Versão inicial do programa
- Funcionalidades básicas de pesquisa e download
- Suporte a playlists M3U

## Versão 1.13.8 (2024-03-24)
- Atualização da função de pesquisa para usar normalização de texto
- Correções de bugs e melhorias de performance
- Atualização de documentação e versão do aplicativo

## Versão 1.13.9 (2024-03-25)
- Implementação de log para playlists que falharam ao serem baixadas
- Correções de bugs e melhorias de performance
- Atualização de documentação e versão do aplicativo