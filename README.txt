postgresql database:

Setup:
====================================================
export POSTGRESQL=/usr/lib/postgresql/10/bin/pg_ctl
export DATA=/home/haow/microblog/data
export LOG=${DATA}/logfile

$POSTGRESQL -D $DATA -l $LOG initdb
$POSTGRESQL -D $DATA -l $LOG start

Usage:
====================================================
psql -U postgres -h localhost -p 5432