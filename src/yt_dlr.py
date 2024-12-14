import os
import shutil
import sys
import tempfile
import time
import traceback
import uuid
import ffmpeg_for_python
from ffmpeg_for_python import FFmpeg
from youtube_analyzer import VideoMetadates, PlaylistMetadates
from utils import *
from youtube_analyzer.exeptions import *

user_path = os.path.expanduser('~')
dw_path = os.path.join(user_path, 'Yt-dlr')
temp_dir = tempfile.mkdtemp('Yt-dlr_temp')
os.makedirs(dw_path, exist_ok=True)
MAX_ATTEMPTS = 10
download_video = None
DEBUG = False


def remux(a_path: str, v_path: str, out: str, origem_path: str, include_captions: str = '') -> None:
    """
    Faz o download de um vídeo usando ffmpeg com um timeout opcional.


    Args:

        a_path (str): O parâmetro a_path deve ser o caminho do audio
        v_path (str): O parâmetro v_path deve ser o caminho do video
        out (str): O parâmetro out é a saida temporária de processamento do video
        origem_path (str): O parâmetro origem_path é o caminho final do video
        include_captions (str): O parâmetro include_captions define se deve ou não remuxar com legendas ,
        nele deve ser passado o caminho do arquivo de legendas

    Returns:

        None: Nenhum valor retornado

    Raises:

        FFmpegExceptions: Erros no processamnto de audio e video.

    Examples:

        remux(a_path="caminho/audio/exemplo.mp4",
         v_path="caminho/video/exemplo.mp4",
         out="caminho/processamento/exemplo.mp4",
         origem_path="caminho/final/exemplo.mp4",
         include_captions="caminho/legenda.srt")

    """

    try:
        print('')
        ffmpeg = FFmpeg()
        tot = 0
        if len(include_captions.strip()) > 0:
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
                        f"\r{Colors.WARNING}Gerando Vídeo Com legendas{Colors.RESET} {Colors.ERROR}=>{Colors.RESET}"
                        f" {Colors.GRAY}{formatted_size}s{Colors.RESET} =>"
                        f"{Colors.GRAY} {time}{Colors.RESET}\t")  #
                else:
                    sys.stdout.write(
                        f"\r{Colors.WARNING}Gerando Vídeo =>{Colors.RESET} {Colors.GRAY}{formatted_size}s{Colors.RESET}"
                        f" {Colors.ERROR}=>{Colors.RESET}"
                        f"{Colors.GRAY} {time}{Colors.RESET}\t")
                sys.stdout.flush()
        shutil.move(out, origem_path)
        if os.path.exists(v_path):
            os.remove(v_path)
        if os.path.exists(a_path):
            os.remove(a_path)
        print(f"\n{origem_path} ", end=' ')
        print(f'{Colors.SUCCESS} Baixado!{Colors.RESET}')
    except Exception as e:
        if DEBUG:
            err = traceback.format_exc()
            print_error(
                f"ERRO NÃO TRATADO => {Colors.GRAY}'{err}'{Colors.RESET}")
            sys.exit(1)
        raise ffmpeg_for_python.FFmpegExceptions(f"Erro ao remuxar: {e}")


def captiones(url_video: str, lang: str) -> str | None:
    """
    Obtém legendas de um vídeo do YouTube.

    Args:
        url_video (str): A URL do vídeo que deseja obter as legendas.
        lang (str): O idioma da legenda.

    Returns:
        str: O caminho do arquivo da legenda baixada, ou None se falhar.

    Examples:
        captiones(url_video="url", lang="pt")
    """
    try:
        print("")
        v = VideoMetadates()
        info = v.get_video_info(url_video=url_video)
        caption = info.Captions.get_caption_for_video()
        caption_path = None

        # Verifica se a legenda está disponível
        if len(caption.url) > 1:
            language_code = caption.lang
            if language_code == include_captions:
                caption_path = caption.download(output_dir=temp_dir, logs=True)
            else:
                caption_path = info.Captions.translate(tlang=lang).download(output_dir=temp_dir, logs=True)
            # Verifica se o arquivo foi baixado e não está vazio
            if caption_path and os.path.exists(caption_path) and os.path.getsize(caption_path) > 0:
                return caption_path
            else:
                raise FileNotFoundError("Erro: Arquivo de legenda não encontrado ou está vazio.")

        else:
            return caption_path
    except NotCaptions:
        return None
    except YoutubeRequestError:
        return None
    except Exception as e:
        raise FileNotFoundError(f"Erro ao obter legendas: {e}")


def download_video_only(url_video: str, temp_dir: str, attempts: int) -> str:
    """
    Baixa o vídeo de forma independente.

    Args:

        url_video (str): O parâmetro url_video é a url do vídeo a ser baixado
        temp_dir (str): O parâmetro temp_dir caminho do diretório onde irá salvar o vídeo.
        attempts (int): O parâmetro attempts tentaivas de download

    Returns:

        str: O valor retornado é o caminho do video

    Raises:

        Exception: Exceção para quando atingir o máximo de tentaivas.

    Examples:

        download_video_only(url_video="url-video", temp_dir="exemplo", attempts=4)

    """
    while attempts < MAX_ATTEMPTS:
        try:
            v = VideoMetadates()
            video_info = v.get_video_info(url_video=url_video)
            print(f"{Colors.INFO}Obtendo vídeo...{Colors.RESET}")
            v_path = video_info.uris_stream.get_highest_resolution().download_video(
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
            print(f"\n{Colors.INFO}Obtendo áudio...{Colors.RESET}")
            a_path = audio_info.uris_stream.get_best_audio_quality().download_audio(
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


def downloader_video(url_video: str, output_dir: str, title: str = None, include_captions: str = ''):
    """
    Faz o download de vídeo e áudio de uma URL, remuxa ambos e salva no diretório especificado.
    :param url_video: URL do vídeo para download.
    :param output_dir: Diretório onde o arquivo final será salvo.
    :param title: Título do arquivo final.
    :param include_captions: Idioma das legendas para incluir, se houver.
    """
    MAX_ATTEMPTS = 10  # Número máximo de tentativas em caso de erro
    attempts = 0  # Contador de tentativas
    os.makedirs(output_dir, exist_ok=True)
    while attempts < MAX_ATTEMPTS:
        try:
            # Inicializar objetos e obter informações do vídeo
            v = VideoMetadates()  # Certifique-se de que essa classe está definida corretamente
            video_info = v.get_video_info(url_video=url_video)
            titlev = video_info.title
            if title:
                filename = f"{sanitize_filename(title)}.mp4"
            else:
                filename = f"{sanitize_filename(titlev)}.mp4"
            final_path = os.path.join(output_dir, filename)

            # Verificar se o vídeo já foi baixado
            if os.path.exists(final_path):
                print_info(f"{filename} => Existente! {Colors.GRAY}Não será baixado novamente.{Colors.RESET}")
                return final_path

            # Baixar vídeo e áudio
            video_path = download_video_only(url_video=url_video,
                                             temp_dir=temp_dir,
                                             attempts=attempts)
            audio_path = download_audio_only(url_video=url_video,
                                             temp_dir=temp_dir,
                                             attempts=attempts)

            # Remuxar vídeo e áudio
            temp_output_path = os.path.join(temp_dir, f"{uuid.uuid4()}.mp4")
            if len(include_captions) > 0:
                caption_path = captiones(url_video=url_video,
                                         lang=include_captions)
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
        except Exception as e:
            if DEBUG:
                err = traceback.format_exc()
                print_error(
                    f"ERRO NÃO TRATADO => {Colors.GRAY}'{err}'{Colors.RESET}")
                sys.exit(1)

            attempts += 1
            if attempts < MAX_ATTEMPTS:
                print(f"{Colors.ERROR}Falha ao baixar o vídeo ({attempts}/{MAX_ATTEMPTS}) => {Colors.GRAY}'{e}'"
                      f" {Colors.RESET}{Colors.WARNING}Tentando novamente...{Colors.RESET}")
                time.sleep(3)
                continue
            else:
                print_error(
                    f"Falha ao baixar o vídeo após {MAX_ATTEMPTS} tentativas => {Colors.GRAY}'{e}'{Colors.RESET}")
                sys.exit(1)


def pl_parser(url_pl, include_captions: str = ''):
    """
    Processa uma playlist e baixa os vídeos.
    :param include_captions:
    :param url_pl: URL da playlist.
    """
    try:
        parser = PlaylistMetadates()
        playlist_info = parser.get_playlist_info(url_pl)
        videos = playlist_info.get_all_videos()
        playlist_title = sanitize_filename(playlist_info.playlist_name.replace(' ', '_'))
        pl_path = os.path.join(dw_path, playlist_title)
        os.makedirs(pl_path, exist_ok=True)

        for video in videos:
            title = video.get('title')
            url_watch = video.get('url_watch')
            video_path = os.path.join(pl_path, f"{title}.mp4")

            if os.path.exists(video_path):
                print(f"{title} EXISTE! Pulando download.")
                continue

            print_warning(f"Baixando -> {title}...")
            if include_captions:
                downloader_video(url_video=url_watch, output_dir=pl_path, title=title,
                                 include_captions=include_captions)
            else:
                downloader_video(url_video=url_watch, output_dir=pl_path, title=title)

        print_success(f"Playlist '{playlist_info.playlist_name}' baixada com sucesso!")
    except InvalidPlaylistError:
        err = traceback.format_exc()
        print_error(f"Ococrreu uma falha ao baixar a playlist é inválida!")
        sys.exit(1)
    except InvalidIdUrlYoutube:
        print_error(f"Ococrreu uma falha a url da playlist é inválida!")
        sys.exit(1)


def help_me():
    print(f"{Colors.INFO}\n\nCOMANDOS:{Colors.RESET}")
    print(f"{Colors.WARNING}--download{Colors.RESET} {Colors.GRAY}<URL>{Colors.RESET}           :"
          f" {Colors.GRAY}Baixa o vídeo ou playlist da URL fornecida.{Colors.RESET}")
    print(f"{Colors.WARNING}--include-captions{Colors.RESET} {Colors.GRAY}<lang>{Colors.RESET}  :"
          f" {Colors.GRAY}Inclui legendas no vídeo (se disponível) no idioma especificado (ISO 639-1).{Colors.RESET}")
    print("\nExemplo de uso:")
    print(
        f"{Colors.ERROR}yt-drl{Colors.RESET} {Colors.WARNING}--download{Colors.RESET} {Colors.GRAY}\"URL\"{Colors.RESET}"
        f" {Colors.WARNING}--include-captions{Colors.RESET} {Colors.GRAY}\"pt\"{Colors.RESET}\n\n")


def validate_youtube_url(url):
    """Valida se a URL fornecida é válida do YouTube."""
    return url.startswith("https://") and (
            "youtube.com" in url or "youtu.be" in url
    )


if __name__ == "__main__":
    try:
        args = sys.argv[1:]

        # Exibir ajuda se não houver argumentos ou com argumento --help
        if not args or "--help" in args:
            help_me()
            sys.exit(0)

        if "--download" in args:
            try:
                download_video = args[args.index("--download") + 1]
                if not validate_youtube_url(download_video):
                    print_error(message=f"URL inválida - {download_video}")
                    sys.exit(1)
            except IndexError:
                print_error(" O argumento '--download' requer uma URL.")
                sys.exit(1)
        else:
            print_error("O argumento '--download' é obrigatório.")
            sys.exit(1)

        # Validar o argumento --include-captions
        include_captions = None
        if "--include-captions" in args:
            try:
                include_captions = args[args.index("--include-captions") + 1]
                if len(include_captions) != 2 or not include_captions.isalpha():
                    raise ValueError("O código de idioma deve estar no formato ISO 639-1 (por exemplo: 'en', 'pt').")
            except (IndexError, ValueError) as e:
                print_error(f"Erro no argumento '--include-captions': {e}")
                sys.exit(1)

        # Processa o download de vídeo ou playlist
        if 'playlist?list=' in download_video:
            pl_parser(url_pl=download_video, include_captions=include_captions)
        else:
            downloader_video(url_video=download_video, output_dir=dw_path, include_captions=include_captions)

    except KeyboardInterrupt:
        print(f"{Colors.ERROR}Interrompido pelo usuário!{Colors.RESET}")
        sys.exit(1)
    except Exception as e:
        if DEBUG:
            err = traceback.format_exc()
            print_error(
                f"ERRO NÃO TRATADO => {Colors.GRAY}'{err}'{Colors.RESET}")
            sys.exit(1)
        print_error(f"não tratado: {e} ,para a url -> '{download_video}'")
        sys.exit(1)
