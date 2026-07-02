#!/usr/bin/env bash
# ============================================================================
# Backup do banco da distribuidora (PostgreSQL no container distribuidora-db).
#
# O que faz: pg_dump -> comprime (gzip) -> valida -> apaga backups antigos.
#
# Uso manual:
#   ./scripts/backup_banco.sh
#
# Agendamento (todo dia as 03:00, com log):
#   crontab -e   e adicione a linha:
#   0 3 * * * /home/eric/Desktop/projeto_max/scripts/backup_banco.sh >> $HOME/backups-distribuidora/backup.log 2>&1
#
# Restauracao (em um banco vazio):
#   gunzip -c distribuidora_2026-07-02_0300.sql.gz | \
#     docker exec -i distribuidora-db psql -U postgres -d distribuidora
#
# IMPORTANTE: backup que fica so no notebook nao protege contra roubo/HD
# queimado. Copie a pasta de destino para um pendrive ou nuvem regularmente.
# ============================================================================
set -euo pipefail  # para na primeira falha; variavel indefinida e erro

# --- Configuracao (sobrescreva via variavel de ambiente se precisar) --------
CONTAINER="${CONTAINER:-distribuidora-db}"
BANCO="${BANCO:-distribuidora}"
USUARIO_PG="${USUARIO_PG:-postgres}"
DESTINO="${DESTINO:-$HOME/backups-distribuidora}"
DIAS_RETENCAO="${DIAS_RETENCAO:-30}"   # apaga .sql.gz com mais de N dias

mkdir -p "$DESTINO"
ARQUIVO="$DESTINO/distribuidora_$(date +%F_%H%M).sql.gz"

# --clean --if-exists: o dump ja inclui os DROPs, entao restaurar por cima
# de um banco existente tambem funciona.
docker exec "$CONTAINER" pg_dump -U "$USUARIO_PG" --clean --if-exists "$BANCO" \
  | gzip > "$ARQUIVO"

# --- Validacao: melhor descobrir backup quebrado hoje do que no desastre ----
gunzip -t "$ARQUIVO"                                   # gzip integro?
if ! gunzip -c "$ARQUIVO" | head -50 | grep -q "PostgreSQL database dump"; then
  echo "ERRO: '$ARQUIVO' nao parece um dump valido." >&2
  exit 1
fi

# --- Retencao ----------------------------------------------------------------
find "$DESTINO" -name 'distribuidora_*.sql.gz' -mtime +"$DIAS_RETENCAO" -delete

echo "[$(date '+%F %T')] OK: $ARQUIVO ($(du -h "$ARQUIVO" | cut -f1))"
