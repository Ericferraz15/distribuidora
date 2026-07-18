#!/usr/bin/env bash
# ============================================================================
# Sobe o sistema no NOTEBOOK-SERVIDOR da loja — comando unico, a prova de erro.
#
#   ./subir_servidor.sh
#
# O que faz, nessa ordem:
#   1. Pede sudo sozinho se o Docker exigir (nao precisa digitar sudo).
#   2. LIMPA a porta 80: derruba containers antigos/orfaos e para servidores
#      web do sistema (apache/nginx) que estejam no caminho.
#   3. Chama o instalar.sh ja no modo rede local (EXPOR_REDE=1).
#
# Nao apaga os dados do banco: o volume do Postgres e preservado sempre.
# ============================================================================
set -euo pipefail

cd "$(dirname "$0")"

# --- 0. Docker instalado? ----------------------------------------------------
if ! command -v docker >/dev/null 2>&1; then
    echo "ERRO: docker nao instalado. Instale com:" >&2
    echo "  curl -fsSL https://get.docker.com | sh" >&2
    echo "e rode este script de novo." >&2
    exit 1
fi

# --- 1. Sudo automatico ------------------------------------------------------
# Se o usuario nao tem acesso ao Docker (grupo docker), reexecuta como root.
if ! docker info >/dev/null 2>&1; then
    if [ "$(id -u)" -ne 0 ]; then
        echo "-> Docker precisa de permissao de root aqui; pedindo senha do sudo..."
        exec sudo bash "$0" "$@"
    fi
    # Ja e root e mesmo assim falhou: daemon parado. Liga agora E habilita no
    # boot — sem o enable, todo reinicio do notebook voltava com o erro
    # "cannot connect to the Docker daemon".
    echo "-> Daemon do Docker parado; ligando e habilitando no boot..."
    systemctl enable --now docker 2>/dev/null \
        || systemctl enable --now snap.docker.dockerd 2>/dev/null || true
    for _ in 1 2 3 4 5 6 7 8 9 10; do
        docker info >/dev/null 2>&1 && break
        sleep 2
    done
    docker info >/dev/null 2>&1 || {
        echo "ERRO: Docker nao subiu. Diagnostico: systemctl status docker" >&2
        exit 1
    }
fi

# Mesmo com o daemon ja rodando, garante que ele liga junto com o sistema.
if command -v systemctl >/dev/null 2>&1 && systemctl cat docker >/dev/null 2>&1 \
   && ! systemctl is-enabled --quiet docker 2>/dev/null; then
    echo "-> Habilitando o Docker no boot..."
    systemctl enable docker >/dev/null 2>&1 || sudo systemctl enable docker >/dev/null 2>&1 \
        || echo "   (nao consegui; rode depois: sudo systemctl enable docker)"
fi

# --- 2. Limpeza da porta 80 --------------------------------------------------
echo "-> Limpando a porta 80..."

# Servidores web instalados no proprio notebook (fora do Docker).
for SVC in apache2 nginx httpd; do
    if command -v systemctl >/dev/null 2>&1 && systemctl is-active --quiet "$SVC" 2>/dev/null; then
        echo "   - Parando e desativando o servico '$SVC' do sistema (ocupava a porta 80)."
        systemctl disable --now "$SVC" 2>/dev/null || sudo systemctl disable --now "$SVC"
    fi
done

# Containers desta stack (inclusive de versoes antigas em outras pastas).
if docker compose version >/dev/null 2>&1; then COMPOSE="docker compose"; else COMPOSE="docker-compose"; fi
$COMPOSE down --remove-orphans >/dev/null 2>&1 || true

# Qualquer outro container ainda publicando a porta 80.
SOBRAS="$(docker ps -aq --filter publish=80)"
if [ -n "$SOBRAS" ]; then
    echo "   - Removendo containers antigos presos na porta 80."
    docker rm -f $SOBRAS >/dev/null
fi

echo "   Porta 80 livre."

# --- 3. Instalacao no modo rede local ---------------------------------------
EXPOR_REDE=1 ./instalar.sh
