FROM gcr.io/oss-fuzz-base/base-builder-python

COPY . $SRC/damn-vulnerable-agent-asset-corpus
COPY .clusterfuzzlite/build.sh $SRC/build.sh
WORKDIR $SRC/damn-vulnerable-agent-asset-corpus

RUN pip3 install --no-cache-dir \
    -r runner/requirements.txt \
    atheris \
    pyinstaller \
    && chmod +x "$SRC/build.sh"
