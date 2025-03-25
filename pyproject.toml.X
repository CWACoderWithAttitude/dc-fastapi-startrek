[project]
name = "fastapi_startrek"
version = "0.1.0"
description = "Add your description here"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115.11",
    "httpx>=0.28.1",
    "passlib[bcrypt]>=1.7.4",
    "prometheus-fastapi-instrumentator>=7.1.0",
    "psycopg2>=2.9.10",
    "pydantic[email]>=2.10.6",
    "pyjwt>=2.10.1",
#    "pytest>=8.3.5",
#    "pytest-watch>=4.2.0",
    "python-decouple>=3.8",
    "python-multipart>=0.0.20",
    "sqlalchemy>=2.0.39",
    "sqlmodel>=0.0.24",
 #   "uv>=0.6.9",
    "uvicorn>=0.34.0",
]

[dependency-groups]
dev = [
    "pytest>=8.3.5",
    "pytest-watch>=4.2.0",
]
