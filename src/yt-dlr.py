import json
import os
import re
import shutil
import sys
import tempfile
import time
import traceback
import uuid
from ffmpeg_for_python import FFmpeg
from youtube_analyzer import VideoMetadates, PlaylistMetadates

user_path = os.path.expanduser('~')
dw_path = os.path.join(user_path, 'Yt-dlr')
temp_dir = tempfile.mkdtemp('Yt-dlr_temp')
os.makedirs(dw_path, exist_ok=True)


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
    sanitized = re.sub(r'[<>:"/\\|?*+&%$@!\'\s]+', ' ', no_emojis).strip().replace(' ', '_')
    return sanitized


def remux(a_path, v_path, out, origem_path, include_captions=None):
    """
    Faz o download de um vídeo usando ffmpeg com um timeout opcional.
    :param v_path:
    :param origem_path:
    :param a_path:
    :param include_captions:
    :param out: Caminho de saída
    :return: None
    """

    try:
        ffmpeg = FFmpeg()
        tot = 0
        if include_captions:
            process = (ffmpeg
                       .overwrite_output
                       .input(a_path)
                       .input(v_path)
                       .input(include_captions)
                       .args(['-c:s', 'mov_text'])
                       .output(out)
                       .copy_codecs
                       .run()
                       )
        else:
            # Executa o comando de remux do ffmpeg
            process = (ffmpeg
                       .overwrite_output
                       .input(a_path)
                       .input(v_path)
                       .output(out)
                       .copy_codecs
                       .run())

        # Regex para capturar as informações desejadas (progresso)
        pattern = re.compile(
            r'frame=\s*(\d+)\s*fps=\s*(\d+)\s*q=\s*(-?\d+\.\d+)\s*size=\s*(\d+.*)\s*time=\s*(\d+:\d+:\d+.\d+)\s*bitrate=\s*(\d+.*)\s*speed=\s*(\d+.*)')

        # Captura a saída do ffmpeg em tempo real
        for line in process:
            match = pattern.search(line)
            if match:
                frame, fps, quality, size, time, bitrate, speed = match.groups()
                # Extrai o valor numérico do tamanho e acumula no total
                size_value = float(re.search(r'(\d+(\.\d+)?)', size).group())
                tot += size_value

                # Formata o tamanho total acumulado
                formatted_size = format_size(str(tot))
                # Gera a saída formatada
                sys.stdout.flush()
                if include_captions:
                    sys.stdout.write(
                        f"\rGerando Vídeo Com legendas => {formatted_size}s => {time}\t")
                else:
                    sys.stdout.write(
                        f"\rGerando Vídeo => {formatted_size}s => {time}\t")
                sys.stdout.flush()
        ## mover o video final pata o dir dw saida
        shutil.move(out, origem_path)
        if os.path.exists(v_path):
            os.remove(v_path)
        if os.path.exists(a_path):
            os.remove(a_path)
        if include_captions:
            if os.path.exists(include_captions):
                os.remove(include_captions)
        print(f"\n{origem_path} => Baixado!")
    except Exception as e:
        raise ValueError(f"Erro ao remuxar: {e}")


def save_json_to_file(data):
    try:
        # Certifique-se de que 'url_watch' esteja presente no dicionário de dados
        url = data.get('url_watch')
        if not url:
            raise ValueError("A URL do vídeo não foi fornecida.")

        # Extraímos o ID do YouTube da URL
        video_id = extract_youtube_id(url)
        if not video_id:
            raise ValueError("ID do YouTube não encontrado na URL fornecida.")

        # Gerar o caminho do arquivo com o ID extraído
        output_path = os.path.join(temp_dir, f"{video_id}.json")

        # Salvar os dados no arquivo JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        print(f"Arquivo JSON salvo em:{output_path}")
    except Exception as e:
        print(f"Erro ao salvar o arquivo JSON: {e}")


MAX_ATTEMPTS = 10


def captiones(url_video):
    v = VideoMetadates()
    info = v.get_video_info(url_video=url_video)
    caption = info.captions.captions_in_video.get_languages[0]
    caption_path = None
    if len(caption) > 1:
        language_code = caption[0].get('code')
        caption_path = info.captions.captions_in_video.download(language_code=language_code, out_dir='.')

    return caption_path


def download_video_only(url_video: str, temp_dir: str, attempts: int) -> str:
    """
    Baixa o vídeo de forma independente.
    :param url_video: URL do vídeo para download.
    :param temp_dir: Diretório temporário para armazenar o vídeo.
    :param attempts: Contador de tentativas.
    """
    while attempts < MAX_ATTEMPTS:
        try:
            v = VideoMetadates()
            video_info = v.get_video_info(url_video=url_video)
            print("Obtendo vídeo...")
            v_path = video_info.uris_stream.get_highest_resolution.download_video(
                title="V_IEED",
                output_dir=temp_dir,
                overwrite_output=True,  # Não sobrescreve se já existir
                logs=True,
                connections=100
            )
            if v_path:  # Se o caminho foi retornado, o vídeo já foi baixado ou foi baixado agora
                return v_path
            raise Exception("Erro desconhecido ao baixar o vídeo.")
        except Exception as e:
            attempts += 1
            print(f"Tentativa {attempts} de {MAX_ATTEMPTS} falhou. Tentando novamente...")
            time.sleep(2)
            continue
    raise Exception(f"Falha no download do vídeo após {MAX_ATTEMPTS} tentativas.")


def download_audio_only(url_video: str, temp_dir: str, attempts: int) -> str:
    """
    Baixa o áudio de forma independente.
    :param url_video: URL do vídeo para download.
    :param temp_dir: Diretório temporário para armazenar o áudio.
    :param attempts: Contador de tentativas.
    """
    while attempts < MAX_ATTEMPTS:
        try:
            v = VideoMetadates()
            audio_info = v.get_video_info(url_video=url_video)
            print("\nObtendo áudio...")
            a_path = audio_info.uris_stream.get_best_audio_quality.download_audio(
                title="A_UU",
                output_dir=temp_dir,
                overwrite_output=True,  # Não sobrescreve se já existir
                logs=True,
                connections=100
            )
            if a_path:  # Se o caminho foi retornado, o áudio já foi baixado ou foi baixado agora
                return a_path
            raise Exception("Erro desconhecido ao baixar o áudio.")
        except Exception as e:
            attempts += 1
            print(f"Tentativa {attempts} de {MAX_ATTEMPTS} falhou. Tentando novamente...")
            time.sleep(2)
            continue

    raise Exception(f"Falha no download do áudio após {MAX_ATTEMPTS} tentativas.")


def downloader_video(url_video: str, output_dir: str, title: str = None, include_captions=None):
    """
    Faz o download de vídeo e áudio de uma URL, remuxa ambos e salva no diretório especificado.
    :param url_video: URL do vídeo para download.
    :param output_dir: Diretório onde o arquivo final será salvo.
    :param title: Título do arquivo final.
    """
    attempts = 0
    v = VideoMetadates()
    video_info = v.get_video_info(url_video=url_video)
    titlev = video_info.title
    filename = f"{title or titlev}.mp4"
    final_path = os.path.join(output_dir, filename)

    if os.path.exists(final_path):
        print(f"{filename} => Existente! Não será baixado novamente.")
        return final_path

    # Baixar vídeo e áudio
    video_path = download_video_only(url_video, temp_dir, attempts)
    audio_path = download_audio_only(url_video, temp_dir, attempts)

    # Remuxar vídeo e áudio
    temp_output_path = os.path.join(temp_dir, f"{uuid.uuid4()}.mp4")
    if include_captions:
        caption_path = captiones(url_video=url_video)
        remux(a_path=audio_path,
              v_path=video_path,
              out=temp_output_path,
              origem_path=final_path,
              include_captions=caption_path)
    else:
        remux(a_path=audio_path,
              v_path=video_path,
              out=temp_output_path,
              origem_path=final_path)
    return final_path


def pl_parser(url_pl, include_captions=None):
    """
    Processa uma playlist e baixa os vídeos.
    :param url_pl: URL da playlist.
    """
    parser = PlaylistMetadates()
    playlist_info = parser.get_playlist_info(url_pl)
    videos = playlist_info.get_all_videos
    playlist_title = sanitize_filename(playlist_info.title.replace(' ', '_'))
    pl_path = os.path.join(dw_path, playlist_title)
    os.makedirs(pl_path, exist_ok=True)

    for video in videos:
        title = video.get('title')
        url_watch = video.get('url_watch')
        video_path = os.path.join(pl_path, f"{title}.mp4")

        if os.path.exists(video_path):
            print(f"{title} EXISTE! Pulando download.")
            continue

        print(f"Baixando {title}...")
        if include_captions:
            downloader_video(url_video=url_watch, output_dir=pl_path, title=title, include_captions=True)
        else:
            downloader_video(url_video=url_watch, output_dir=pl_path, title=title)

    print(f"Playlist '{playlist_info.title}' baixada com sucesso!")


def help_me():
    print("COMANDOS:")
    print("--download <URL>     : Baixa o vídeo ou playlist da URL fornecida.")
    print("--include-captions   : Inclui legendas no video (se disponível).")
    print("\nExemplo de uso:")
    print("yt-drl --download <URL> --include-captions")


def validate_youtube_url(url):
    """Valida se a URL fornecida é válida do YouTube."""
    return url.startswith("https://") and (
            "youtube.com" in url or "youtu.be" in url
    )


if __name__ == "__main__":
    try:
        args = sys.argv[1:]
        # Exibir ajuda se não houver argumentos ou com argumento --help
        if "--help" in args:
            help_me()
            sys.exit(0)
        download_video = args[args.index("--download") + 1] if "--download" in args else None
        include_captions = "--include-captions" in args

        if download_video:
            # Validação simples da URL
            if not validate_youtube_url(download_video):
                print(f"URL inválida: {download_video}")
                sys.exit(1)
            # Processa o download de vídeo ou playlist
            if 'playlist?list=' in download_video:
                pl_parser(url_pl=download_video, include_captions=include_captions)
            else:
                downloader_video(url_video=download_video, output_dir=dw_path, include_captions=include_captions)
        else:
            print("Erro: O argumento '--download' é obrigatório.")
            help_me()
            sys.exit(1)
    except KeyboardInterrupt:
        print("Interrompido!")
        sys.exit(0)
    except Exception as e:
        # Exibir erro completo
        erro = traceback.format_exc()
        print(f"Erro não tratado: {erro}")
