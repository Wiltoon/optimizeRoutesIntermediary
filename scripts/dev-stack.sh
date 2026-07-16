#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_DIR="$ROOT_DIR/.run"
BACKEND_PID_FILE="$RUN_DIR/backend.pid"
FRONTEND_PID_FILE="$RUN_DIR/frontend.pid"
BACKEND_LOG="$RUN_DIR/backend.log"
FRONTEND_LOG="$RUN_DIR/frontend.log"

OSRM_PORT="${OSRM_PORT:-5001}"
API_PORT="${API_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"
PYTHON_BIN="${PYTHON_BIN:-/opt/homebrew/bin/python3.11}"
OSRM_PBF_URL="${OSRM_PBF_URL:-https://download.geofabrik.de/south-america/brazil/centro-oeste-latest.osm.pbf}"

OSRM_PBF_FILE="$(basename "$OSRM_PBF_URL")"
OSRM_BASENAME="${OSRM_BASENAME:-${OSRM_PBF_FILE%.osm.pbf}}"
OSRM_DATA_DIR="$ROOT_DIR/resources/osrm-data"

mkdir -p "$RUN_DIR"

is_pid_running() {
  local pid="$1"
  if [[ -z "$pid" ]]; then
    return 1
  fi
  kill -0 "$pid" >/dev/null 2>&1
}

read_pid() {
  local pid_file="$1"
  if [[ -f "$pid_file" ]]; then
    cat "$pid_file"
  else
    echo ""
  fi
}

find_backend_pid() {
  local pid
  pid="$(read_pid "$BACKEND_PID_FILE")"
  if is_pid_running "$pid"; then
    echo "$pid"
    return
  fi

  pid="$(lsof -t -iTCP:"$API_PORT" -sTCP:LISTEN 2>/dev/null | head -n 1 || true)"
  echo "$pid"
}

find_frontend_pid() {
  local pid
  pid="$(read_pid "$FRONTEND_PID_FILE")"
  if is_pid_running "$pid"; then
    echo "$pid"
    return
  fi

  pid="$(lsof -t -iTCP:"$FRONTEND_PORT" -sTCP:LISTEN 2>/dev/null | head -n 1 || true)"
  echo "$pid"
}

start_osrm_redis() {
  if ! command -v docker >/dev/null 2>&1; then
    echo "[erro] Docker nao encontrado. Instale/inicie Docker para subir OSRM/Redis."
    exit 1
  fi

  if ! docker info >/dev/null 2>&1; then
    echo "[erro] Docker daemon nao esta ativo. Inicie o Docker Desktop e tente novamente."
    exit 1
  fi

  mkdir -p "$OSRM_DATA_DIR"

  if [[ ! -f "$OSRM_DATA_DIR/$OSRM_BASENAME.osm.pbf" ]]; then
    echo "[info] Baixando extrato OSM em host: $OSRM_PBF_URL"
    curl -fsSL "$OSRM_PBF_URL" -o "$OSRM_DATA_DIR/$OSRM_BASENAME.osm.pbf"
  else
    echo "[info] Extrato OSM ja existe: $OSRM_DATA_DIR/$OSRM_BASENAME.osm.pbf"
  fi

  if head -c 200 "$OSRM_DATA_DIR/$OSRM_BASENAME.osm.pbf" | grep -qiE '<!doctype html|<html'; then
    echo "[warn] Arquivo baixado nao e PBF valido (recebido HTML). Rebaixando..."
    rm -f "$OSRM_DATA_DIR/$OSRM_BASENAME.osm.pbf"
    curl -fsSL "$OSRM_PBF_URL" -o "$OSRM_DATA_DIR/$OSRM_BASENAME.osm.pbf"
  fi

  if head -c 200 "$OSRM_DATA_DIR/$OSRM_BASENAME.osm.pbf" | grep -qiE '<!doctype html|<html'; then
    echo "[erro] Download do extrato OSM falhou (resposta HTML)."
    echo "       Verifique OSRM_PBF_URL e tente novamente."
    exit 1
  fi

  echo "[info] Preprocessando OSRM (apenas na primeira execucao)..."
  (
    cd "$ROOT_DIR"
    OSRM_PORT="$OSRM_PORT" OSRM_BASENAME="$OSRM_BASENAME" docker compose --profile preprocess run --rm osrm-preprocess
  )

  echo "[info] Subindo OSRM e Redis via Docker Compose..."
  (
    cd "$ROOT_DIR"
    OSRM_PORT="$OSRM_PORT" OSRM_BASENAME="$OSRM_BASENAME" docker compose up -d osrm redis
  )
}

start_backend() {
  local current_pid
  current_pid="$(read_pid "$BACKEND_PID_FILE")"
  if is_pid_running "$current_pid"; then
    echo "[info] Backend ja esta rodando (PID $current_pid)."
    return
  fi

  if [[ ! -x "$PYTHON_BIN" ]]; then
    echo "[erro] Python nao encontrado em $PYTHON_BIN"
    echo "       Defina PYTHON_BIN ou ajuste no script."
    exit 1
  fi

  echo "[info] Subindo backend em http://localhost:$API_PORT ..."
  (
    cd "$ROOT_DIR"
    OSRM_HOST="http://localhost:$OSRM_PORT" \
    REDIS_URL="redis://localhost:6379/0" \
    nohup "$PYTHON_BIN" -m uvicorn src.api.main:app --host 0.0.0.0 --port "$API_PORT" >"$BACKEND_LOG" 2>&1 &
    echo $! >"$BACKEND_PID_FILE"
  )
}

start_frontend() {
  local current_pid
  current_pid="$(read_pid "$FRONTEND_PID_FILE")"
  if is_pid_running "$current_pid"; then
    echo "[info] Frontend ja esta rodando (PID $current_pid)."
    return
  fi

  echo "[info] Subindo frontend em http://localhost:$FRONTEND_PORT ..."
  (
    cd "$ROOT_DIR/frontend"

    if [[ -s "$HOME/.nvm/nvm.sh" ]]; then
      # shellcheck disable=SC1090
      source "$HOME/.nvm/nvm.sh"
      nvm use 20 >/dev/null 2>&1 || true
    fi

    nohup npm run dev -- --port "$FRONTEND_PORT" >"$FRONTEND_LOG" 2>&1 &
    echo $! >"$FRONTEND_PID_FILE"
  )
}

stop_backend() {
  local pid
  pid="$(find_backend_pid)"
  if is_pid_running "$pid"; then
    echo "[info] Parando backend (PID $pid)..."
    kill "$pid" || true
  fi
  rm -f "$BACKEND_PID_FILE"
}

stop_frontend() {
  local pid
  pid="$(find_frontend_pid)"
  if is_pid_running "$pid"; then
    echo "[info] Parando frontend (PID $pid)..."
    kill "$pid" || true
  fi
  rm -f "$FRONTEND_PID_FILE"
}

stop_osrm_redis() {
  if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
    echo "[info] Parando OSRM/Redis (docker compose stop)..."
    (
      cd "$ROOT_DIR"
      OSRM_PORT="$OSRM_PORT" OSRM_BASENAME="$OSRM_BASENAME" docker compose stop osrm redis >/dev/null 2>&1 || true
    )
  fi
}

show_status() {
  local backend_pid frontend_pid
  backend_pid="$(find_backend_pid)"
  frontend_pid="$(find_frontend_pid)"

  echo "===== STATUS STACK ====="
  if is_pid_running "$backend_pid"; then
    echo "Backend : ON  (PID $backend_pid)"
  else
    echo "Backend : OFF"
  fi

  if is_pid_running "$frontend_pid"; then
    echo "Frontend: ON  (PID $frontend_pid)"
  else
    echo "Frontend: OFF"
  fi

  if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
    local osrm_state redis_state
    osrm_state="$(docker ps --filter name=optimizeroutes_osrm --format '{{.Names}}' | head -n 1)"
    redis_state="$(docker ps --filter name=optimizeroutes_redis --format '{{.Names}}' | head -n 1)"
    [[ -n "$osrm_state" ]] && echo "OSRM    : ON  (porta $OSRM_PORT)" || echo "OSRM    : OFF"
    [[ -n "$redis_state" ]] && echo "Redis   : ON" || echo "Redis   : OFF"
  else
    echo "OSRM    : OFF (docker indisponivel)"
    echo "Redis   : OFF (docker indisponivel)"
  fi

  echo
  echo "Health checks:"
  curl -sS -m 3 "http://localhost:$API_PORT/health" && echo || echo "backend health: indisponivel"
  curl -fsS -m 5 "http://localhost:$OSRM_PORT/nearest/v1/driving/-47.8825,-15.7942?number=1" >/dev/null 2>&1 && echo "osrm health: ok" || echo "osrm health: indisponivel"
  curl -sS -I -m 3 "http://localhost:$FRONTEND_PORT" | head -n 1 || echo "frontend: indisponivel"

  echo
  echo "Logs:"
  echo "- Backend : $BACKEND_LOG"
  echo "- Frontend: $FRONTEND_LOG"
}

cmd="${1:-}"
case "$cmd" in
  start)
    start_osrm_redis
    start_backend
    start_frontend
    echo "[ok] Stack iniciada."
    show_status
    ;;
  stop)
    stop_frontend
    stop_backend
    stop_osrm_redis
    echo "[ok] Stack parada."
    ;;
  restart)
    "$0" stop
    "$0" start
    ;;
  status)
    show_status
    ;;
  *)
    echo "Uso: $0 {start|stop|restart|status}"
    echo "Variaveis opcionais: OSRM_PORT, API_PORT, FRONTEND_PORT, PYTHON_BIN, OSRM_PBF_URL, OSRM_BASENAME"
    exit 1
    ;;
esac
