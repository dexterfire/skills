#!/bin/bash
# Live-test one opencode model on text, image input and tool use.
# usage: test_model.sh <provider/model> <outdir> <image.png>
# Writes <outdir>/<model>.json. Tool use runs with --auto inside a scratch dir under <outdir>.
m="$1"; out="$2"; img="$3"
safe=$(echo "$m" | tr '/:' '__'); w="$out/work_$safe"
mkdir -p "$w" && cp "$img" "$w/test.png"
clean(){ sed 's/\x1b\[[0-9;]*m//g' | grep -v '^\s*$' | grep -v '^> ' | tail -3 | tr '\n' ' '; }

t0=$(date +%s)
txt=$(cd "$w" && timeout 120 opencode run -m "$m" "Сколько будет 17*3? Ответь только числом." 2>&1 | clean)
t1=$(date +%s)
# The prompt goes before -f: -f is variadic and would swallow it.
vis=$(cd "$w" && timeout 150 opencode run -m "$m" "Какое число на картинке и какого цвета рамка? Ответь кратко." -f test.png 2>&1 | clean)
tool=$(cd "$w" && timeout 150 opencode run --auto -m "$m" "Создай в текущей папке файл ok.txt с содержимым DONE. Больше ничего не делай." 2>&1 | clean)
[ "$(tr -d '[:space:]' < "$w/ok.txt" 2>/dev/null)" = "DONE" ] && tf=yes || tf=no

python3 -c 'import json,sys; print(json.dumps(dict(zip(["model","text","text_sec","vision","tool_file","tool_out"], sys.argv[1:]), ensure_ascii=False))' \
  "$m" "$txt" "$((t1-t0))" "$vis" "$tf" "$tool" > "$out/$safe.json"
