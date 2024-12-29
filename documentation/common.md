
## !! Before each commit 
```aiignore
    pip freeze > requirements.txt
```

and make sure the port is 8000 

---
## setup venv & requirements
Create Virtual Environment
```aiignore
    python -m venv venv
```
Activate Virtual Environment
- on windows
```aiignore
    venv\Scripts\activate
```
- on macOS/Linux
```aiignore
    source venv/bin/activate
```
---
## Install Requirements
```aiignore
    pip install -r requirements.txt
```
---
## setup env variables
```aiignore
    DB_SERVER=
    DB_NAME=
    DB_USERNAME=
    DB_PASSWORD=
    DB_DRIVER=
    JWT_SECRET_KEY=
```
---
## Run the app 
```aiignore
    python app.py
```
