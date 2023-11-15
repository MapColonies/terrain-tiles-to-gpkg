FROM andrejreznik/python-gdal:py3.8.2-gdal3.0.4 AS buildStage

WORKDIR /app
COPY . /app

RUN pip3 install --no-cache-dir -r requirements.txt

RUN echo "alias tilesToGpkg='python3 /app/main.py'" >> ~/.bashrc

WORKDIR /data

ENTRYPOINT ["bash"]