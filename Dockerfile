FROM andrejreznik/python-gdal:py3.8.2-gdal3.0.4

WORKDIR /_tilesToGpkgCli
COPY . /_tilesToGpkgCli

RUN pip3 install --no-cache-dir -r requirements.txt

RUN echo "alias tilesToGpkg='python3 /_tilesToGpkgCli/main.py'" >> ~/.bashrc

WORKDIR /data

ENTRYPOINT ["bash"]