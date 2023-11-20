FROM andrejreznik/python-gdal:py3.8.2-gdal3.0.4

# Use the first host's user and group by default
# Permissions related
ARG USER_NAME=user
ARG USER_UID=1000
ARG USER_GID=1000

RUN groupadd -g $USER_GID $USER_NAME \
    && useradd -u $USER_UID -g $USER_GID -m -s /bin/bash $USER_NAME

USER $USER_NAME

WORKDIR /_tilesToGpkgCli
COPY . /_tilesToGpkgCli

RUN pip3 install --no-cache-dir -r requirements.txt

RUN echo "alias tilesToGpkg='python3 /_tilesToGpkgCli/main.py'" >> ~/.bashrc

WORKDIR /data

ENTRYPOINT ["bash"]