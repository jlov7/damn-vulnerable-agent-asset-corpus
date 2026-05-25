FROM gcr.io/oss-fuzz-base/base-builder-python@sha256:f1e9235da21d788074f956b2b687a07bf16c5edddfd9fdc24f86154012ae7369

COPY . $SRC/damn-vulnerable-agent-asset-corpus
COPY .clusterfuzzlite/build.sh $SRC/build.sh
WORKDIR $SRC/damn-vulnerable-agent-asset-corpus

RUN pip3 install --no-cache-dir \
    -r runner/requirements.txt \
    atheris \
    pyinstaller \
    && chmod +x "$SRC/build.sh"
