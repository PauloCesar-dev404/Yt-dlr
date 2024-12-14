
# YT-DLR
é uma ferramenta de código aberto, feita para facilitar o download de vídeos e playlists do YouTube de forma prática e eficiente.

## Funcionalidades

- **Baixar vídeos individuais**: Permite baixar vídeos do YouTube através da URL.
- **Baixar playlists**: Suporta o download de playlists inteiras do YouTube.
- **Legendas**: É possível incluir legendas, se disponíveis, durante o download do vídeo.


## Modo de Uso

### Baixar um vídeo com legendas

Para baixar um vídeo específico e incluir as legendas (se disponíveis), execute o seguinte comando no terminal ou prompt de comando:

```bash
yt-dlr.exe --download "URL-AQUI" --include-captions "pt" 
```

Este comando irá baixar o vídeo indicado na URL e incluirá a legenda original (caso esteja disponível).

### Baixar uma playlist

Para baixar uma playlist inteira, use a URL da playlist do YouTube. O comando será similar ao comando de download de um único vídeo, mas o programa irá baixar todos os vídeos na playlist:

```bash
yt-dlr.exe --download "URL-DA-PLAYLIST"
```

## Parâmetros

- `--download`: A URL do vídeo ou playlist que você deseja baixar.
- `--include-captions`: Incluirá as legendas disponíveis no vídeo ou playlist. Este parâmetro é opcional.

## Exemplo de uso

1. **Baixar um vídeo com legendas:**

    ```bash
    ./yt-dlr.exe --download "URL-VIDEO" --include-captions
    ```

2. **Baixar uma playlist:**

    ```bash
    ./yt-dlr.exe --download "URL-playlist"
    ```

## Problemas Comuns

- **Vídeo não encontrado**: Se o vídeo ou playlist não for encontrado, verifique a URL e tente novamente.
- **Legendas não disponíveis**: Caso o vídeo não tenha legendas, o parâmetro `--include-captions` será ignorado.

## Contribuições

Se você encontrar algum bug ou tiver sugestões para melhorar o projeto, fique à vontade para abrir uma issue ou contribuir diretamente no repositório do GitHub.

---

### Apoie o Projeto!

**Chainlink**
```
0x0038a0AB79286E882951eEC15c80400868335778
```
**Ethereum**
```
0x87deaB84FA4a9F1982CCeb540591d95FCf850363
```
**Bitcoin**
```
bc1qu8xl22lp0wjvqzne2g4yl46ayl8v5zrav3hzdq
```

---

