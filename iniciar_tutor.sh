#!/bin/bash
set -euo pipefail

# Tutor Escolar IA - inicio del servidor de texto con llama.cpp + Vulkan AMD

LLAMA_DIR="${LLAMA_DIR:-$HOME/Documentos/IA/llama-vulkan-bin/llama-b9620}"
MODEL="${MODEL:-$HOME/models/Qwen3.5-0.8B-Q4_K_M.gguf}"
MMPROJ="${MMPROJ:-$HOME/models/qwen35-mmproj-BF16.gguf}"
PORT="${PORT:-8081}"
VISION_PORT="${VISION_PORT:-8082}"
VULKAN_DEVICE="${VULKAN_DEVICE:-Vulkan0}"
CTX_SIZE="${CTX_SIZE:-1024}"
NGPU_LAYERS="${NGPU_LAYERS:-99}"
N_PARALLEL="${N_PARALLEL:-1}"
FIT_TARGET="${FIT_TARGET:-256}"
LOG_FILE="${LOG_FILE:-/tmp/llama-tutor.log}"
RUN_VISION="${RUN_VISION:-false}"
AUTO_ENABLE_DESKLET="${AUTO_ENABLE_DESKLET:-true}"
DESKLET_UUID="${DESKLET_UUID:-tutor-escolar@mint}"
LAUNCH_CLIENT="${LAUNCH_CLIENT:-}"

props_ready() {
    local port="$1"
    curl -fsS "http://127.0.0.1:${port}/props" 2>/dev/null | grep -q '"supports_tool_calls"[[:space:]]*:[[:space:]]*true'
}

wait_ready() {
    local port="$1"
    local intentos="${2:-90}"
    for _ in $(seq 1 "$intentos"); do
        if props_ready "$port"; then
            return 0
        fi
        sleep 1
    done
    return 1
}

enable_desklet() {
    if [[ "$AUTO_ENABLE_DESKLET" != "true" ]]; then
        return 0
    fi

    if ! command -v gsettings >/dev/null 2>&1; then
        echo "gsettings no disponible: no se pudo activar el desklet automaticamente."
        return 0
    fi

    local raw current nuevo
    raw="$(gsettings get org.cinnamon enabled-desklets 2>/dev/null || echo "@as []")"
    current="$raw"
    if [[ "$current" == @as* ]]; then
        current="${current#@as }"
    fi

    nuevo="$(python3 - "$current" "$DESKLET_UUID:0" <<'PY'
import ast
import sys

raw = sys.argv[1]
item = sys.argv[2]
try:
    values = ast.literal_eval(raw)
except Exception:
    values = []
if not isinstance(values, list):
    values = []
if item not in values:
    values.append(item)
print(str(values))
PY
)"

    gsettings set org.cinnamon enabled-desklets "$nuevo"
    echo "Desklet activado: $DESKLET_UUID:0"
}

launch_client() {
    if [[ -z "$LAUNCH_CLIENT" ]]; then
        return 0
    fi

    case "$LAUNCH_CLIENT" in
        tkinter)
            python3 "$HOME/Documentos/IA/tutor_tkinter.py" &
            echo "Cliente Tkinter iniciado."
            ;;
        *)
            echo "LAUNCH_CLIENT desconocido: $LAUNCH_CLIENT"
            ;;
    esac
}

start_server() {
    local port="$1"
    local usar_mmproj="$2"
    local args=(
        -m "$MODEL"
        -c "$CTX_SIZE"
        --host 127.0.0.1
        --port "$port"
        -ngl "$NGPU_LAYERS"
        --device "$VULKAN_DEVICE"
        --fit on
        --fit-target "$FIT_TARGET"
        --reasoning off
        --reasoning-budget 0
        --reasoning-format deepseek
        --jinja
        --no-warmup
        --cache-ram 0
        --prio -1
        -np "$N_PARALLEL"
    )

    if [[ "$usar_mmproj" == "true" ]]; then
        args+=(--mmproj "$MMPROJ")
    fi

    cd "$LLAMA_DIR"
    ./llama-server "${args[@]}" > "$LOG_FILE" 2>&1 &
}

echo "=== Tutor Escolar IA ==="
echo "Modelo: Qwen3.5-0.8B"
echo "GPU Vulkan fija: $VULKAN_DEVICE"
echo "Puerto texto: $PORT"
echo "Puerto vision bajo demanda: $VISION_PORT"
echo ""

if curl -fsS "http://127.0.0.1:$PORT/health" >/dev/null 2>&1; then
    if wait_ready "$PORT" 15; then
        echo "llama-server de texto ya esta corriendo en puerto $PORT"
    else
        echo "Hay algo escuchando en $PORT, pero no responde como servidor listo."
        echo "Revisa: $LOG_FILE"
        exit 1
    fi
else
    echo "Iniciando llama-server de texto con GPU Vulkan AMD..."
    start_server "$PORT" false
    if wait_ready "$PORT" 90; then
        echo "Servidor de texto listo."
    else
        echo "El servidor no quedo listo. Revisa: $LOG_FILE"
        exit 1
    fi
fi

if [[ "$RUN_VISION" == "true" ]]; then
    if curl -fsS "http://127.0.0.1:$VISION_PORT/health" >/dev/null 2>&1 && wait_ready "$VISION_PORT" 15; then
        echo "Servidor de vision ya esta corriendo en puerto $VISION_PORT"
    else
        echo "Iniciando servidor de vision con mmproj..."
        start_server "$VISION_PORT" true
        if wait_ready "$VISION_PORT" 120; then
            echo "Servidor de vision listo."
        else
            echo "El servidor de vision no quedo listo. Revisa: $LOG_FILE"
            exit 1
        fi
    fi
else
    echo "Vision en reposo: el mmproj se iniciara solo si el backend recibe una imagen."
fi

enable_desklet
launch_client

echo ""
echo "=== Configuracion ==="
echo "  Backend texto: http://127.0.0.1:$PORT"
echo "  Backend vision: http://127.0.0.1:$VISION_PORT"
echo "  Vision: bajo demanda"
echo "  Desklet auto: $AUTO_ENABLE_DESKLET"
echo "  Cliente: ${LAUNCH_CLIENT:-ninguno}"
echo "  Tools: si"
echo ""
echo "Para probar desde terminal:"
echo "  echo '{\"texto\": \"Que es la fotosintesis?\"}' | python3 ~/.local/share/cinnamon/desklets/tutor-escolar@mint/tutor_backend.py"
echo ""
echo "Para probar con imagen:"
echo "  echo '{\"texto\": \"Que ves?\", \"imagen\": \"<base64>\"}' | python3 ~/.local/share/cinnamon/desklets/tutor-escolar@mint/tutor_backend.py"
