# Constantes de cores ANSI
import re


class Colors:
    ERROR = "\u001b[31m"  # Vermelho
    WARNING = "\u001b[33m"  # Amarelo
    SUCCESS = "\u001b[32m"  # Verde
    INFO = "\u001b[34m"  # Azul
    RESET = "\u001b[0m"  # Resetar cor para padrão
    GRAY = "\u001b[90m"  # Cinza


# Funções de mensagem formatada
def print_error(message):
    print(f"{Colors.ERROR}Erro: {message}{Colors.RESET}")


def print_warning(message):
    print(f"{Colors.WARNING}Aviso: {message}{Colors.RESET}")


def print_success(message):
    print(f"{Colors.SUCCESS}Sucesso: {message}{Colors.RESET}")


def print_info(message):
    print(f"{Colors.INFO}Info: {message}{Colors.RESET}")


def format_size(size_str):
    size_units = ["B", "KB", "MB", "GB", "TB"]
    size_value = float(re.search(r'(\d+(\.\d+)?)', size_str).group())  # Extrai o número do tamanho
    unit = "B"

    for unit in size_units:
        if size_value < 1024.0:
            break
        size_value /= 1024.0

    return f"{size_value:.2f} {unit}"


def extract_youtube_id(url):
    try:
        # Verifica se a URL é de um vídeo
        video_pattern = r'(?:https?://(?:www\.)?youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})'
        playlist_pattern = r'(?:https?://(?:www\.)?youtube\.com/playlist\?list=)([a-zA-Z0-9_-]+)'

        # Tenta extrair o ID do vídeo
        video_match = re.search(video_pattern, url)
        if video_match:
            return video_match.group(1)

        # Tenta extrair o ID da playlist
        playlist_match = re.search(playlist_pattern, url)
        if playlist_match:
            return playlist_match.group(1)

        # Se nenhuma correspondência for encontrada
        return {"error": "URL inválida ou tipo desconhecido."}

    except Exception as e:
        return {"error": f"Erro ao extrair ID: {e}"}


def sanitize_filename(filename: str) -> str:
    """
    Sanitiza um nome de arquivo, removendo emojis e caracteres inválidos
    para nomes de arquivos, mas preservando acentos e outros caracteres permitidos.
    """
    # Remove emojis
    no_emojis = re.sub(r'[\U00010000-\U0010FFFF]', '', filename)
    # Remove caracteres inválidos para nomes de arquivos
    sanitized = re.sub(r'[<>:"/\\|?*+&%$@!\'\s]+', ' ', no_emojis).strip()
    return sanitized
