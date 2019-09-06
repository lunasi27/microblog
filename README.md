# microblog
This is a poc of microblog project

1, setup flask run env
    mkdir -t flask
    cd flask
    virtialenv --no-site-packages venv
    source flask/venv/bin/activate
    pip install -r requirements.txt


2, setup database
    # install postgresql
    # stop auto run service: service postgresql stop
    ./db/db_init.sh

    # Connect to database
    psql -U postgres -h localhost -p 5432


3, Invoke flask web server
    python run.py


4, run unitest
    python test/login_tests.py

