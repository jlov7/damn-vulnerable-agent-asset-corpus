#!/bin/bash -eu

cd "$SRC/damn-vulnerable-agent-asset-corpus"

for fuzzer in fuzz/*_fuzzer.py; do
  fuzzer_basename="$(basename -s .py "$fuzzer")"
  fuzzer_package="${fuzzer_basename}.pkg"

  pyinstaller \
    --paths "$SRC/damn-vulnerable-agent-asset-corpus" \
    --add-data "$SRC/damn-vulnerable-agent-asset-corpus/corpus.manifest.json:." \
    --add-data "$SRC/damn-vulnerable-agent-asset-corpus/corpus.manifest.schema.json:." \
    --add-data "$SRC/damn-vulnerable-agent-asset-corpus/scorecard-template.schema.json:." \
    --add-data "$SRC/damn-vulnerable-agent-asset-corpus/fixtures:fixtures" \
    --distpath "$OUT" \
    --onefile \
    --name "$fuzzer_package" \
    "$fuzzer"

  cat > "$OUT/$fuzzer_basename" <<EOF
#!/bin/sh
# LLVMFuzzerTestOneInput for fuzzer detection.
this_dir=\$(dirname "\$0")
\$this_dir/$fuzzer_package "\$@"
EOF
  chmod +x "$OUT/$fuzzer_basename"
done
