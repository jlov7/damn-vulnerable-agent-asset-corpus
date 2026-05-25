FROM gcr.io/oss-fuzz-base/base-builder-python

COPY . $SRC/damn-vulnerable-agent-asset-corpus
WORKDIR $SRC/damn-vulnerable-agent-asset-corpus

RUN pip3 install --no-cache-dir \
    -r runner/requirements.txt \
    atheris \
    pyinstaller
