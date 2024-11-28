import nutikacompile

nutikacompile.compile_with_nuitka(pyfile=r'./yt-dlr.py',
                                  copyright='PauloCesar0073',
                                  product_name=r'yt-dlr',
                                  outputdir=r'yt-dlr',
                                  onefile=True,
                                  icon=r'./favicon.ico',
                                  delete_onefile_temp=True,
                                  disable_console=False,
                                  file_version='1.0.1',
                                  file_description='ytb downloader',
                                  arguments2add='--standalone --enable-plugin=tk-inter')
