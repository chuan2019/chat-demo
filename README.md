# chat demo

Usage: the usage below has been tested on mac os and ubuntu 20.04.1

step 1: start redis sever

```
 $ docker-compose up -d --build
```

step 2: create virtual environment locally, and install dependencies

```
 $ python -m venv .env
 
 $ source .env/bin/activate

 $ pip install --upgrade pip
 
 $ pip install -r requirements.txt
```

step 3: start the web server

```
 $ cd chat

 $ python run.py
```

