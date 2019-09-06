#!/bin/bash

PSQL_BIN=/usr/lib/postgresql/10/bin
DATA_PATH=/home/haow/microblog/data
LOG=${DATA_PATH}/logfile
USER=${1:-postgres}
DB_NAME=${2:-test}
PORT=${3:-5432}
DB_HOST=${4:-localhost}

${PSQL_BIN}/pg_ctl stop -D ${DATA_PATH} -l ${LOG} -m fast -o "-p ${PORT}"

