# Identificacao Aerea

Sistema de deteccao, classificacao e rastreamento de objetos aereos em tempo real, com conformidade total com a LGPD.

## Visao Geral

O sistema captura feeds de video e imagens de multiplas fontes (cameras, radar, infravermelho, ADS-B), processa via modelos de deep learning (YOLOv8) e classifica objetos aereos como aeronaves, helicopteros, drones, baloes, passaros, satelites e misseis. Todo o pipeline respeita a Lei Geral de Protecao de Dados, com anonimizacao automatica de dados pessoais capturados (rostos, placas).

## Stack

| Camada          | Tecnologia                  |
|-----------------|-----------------------------|
| Linguagem       | Python 3.12+                |
| API             | FastAPI + Uvicorn           |
| Deteccao        | YOLOv8 (Ultralytics)       |
| Visao           | OpenCV + Pillow             |
| ML Runtime      | PyTorch + TorchVision       |
| Banco de Dados  | PostgreSQL 16               |
| Cache           | Redis 7                     |
| Fila            | Celery                      |
| ORM             | SQLAlchemy 2.0 + Alembic    |
| Containers      | Docker + Docker Compose     |
| Metricas        | Prometheus Client           |
| Storage         | Local / S3 (boto3)          |

## Estrutura do Projeto

identificacao-aerea/
|
|-- src/
|   |-- api/
|   |   |-- app.py
|   |   |-- models.py
|   |   |-- routes.py
|   |   |-- schemas.py
|   |
|   |-- auth/
|   |   |-- models.py
|   |   |-- manager.py
|   |
|   |-- config/
|   |   |-- models.py
|   |   |-- settings.py
|   |
|   |-- detect/
|   |   |-- models.py
|   |
|   |-- lgpd/
|   |   |-- models.py
|   |
|   |-- monitoring/
|   |   |-- models.py
|   |
|-- tests/
|-- data/
|-- models/
|
|-- .env
|-- .env.example
|-- .gitignore
|-- docker-compose.yml
|-- docker-compose.dev.yml
|-- Dockerfile
|-- Makefile
|-- pyproject.toml
|-- requirements.txt
|-- requirements-dev.txt
|-- README.md

## Modulos

### src/detect

Nucleo de deteccao. Define os modelos de dados para o pipeline de inferencia.

- **ObjectClass**: classificacao do objeto (aircraft, helicopter, drone, bird, balloon, satellite, missile, unknown)
- **Detection**: deteccao individual com bounding box, geoposicao, confianca e source
- **TrackedObject**: objeto rastreado ao longo do tempo com multiplas deteccoes
- **InferenceResult**: resultado completo de uma execucao de inferencia
- **BoundingBox**: coordenadas e metodos utilitarios (IoU, area, centro)
- **GeoPosition**: latitude, longitude, altitude, heading e velocidade

### src/auth

Autenticacao e controle de acesso via API keys.

- **AuthProvider**: provedor de autenticacao (internal, ldap, oauth2, api_key)
- **Permission / Role**: controle granular de permissoes e papeis
- **ApiKeyRecord**: registro de chave com escopos, rate limit e expiracao
- **AuthEvent**: log de eventos de autenticacao
- **RateLimitEntry**: controle de taxa de requisicoes por chave

### src/lgpd

Conformidade com a Lei Geral de Protecao de Dados.

- **DataSubject**: titular dos dados
- **PersonalDataRecord**: registro de dado pessoal com base legal, retencao e anonimizacao
- **ConsentRecord**: consentimento do titular com controle de validade
- **SubjectRequest**: solicitacao do titular (acesso, exclusao, portabilidade, retificacao)
- **TreatmentRecord**: log de operacoes de tratamento de dados
- **AnonymizationRecord**: registro de anonimizacao aplicada (blur, masking, hashing, etc.)
- **LegalBasis**: bases legais previstas na LGPD

### src/monitoring

Observabilidade do sistema.

- **HealthStatus / HealthCheck**: verificacao de saude dos componentes
- **MetricEntry / MetricSnapshot**: coleta de metricas do sistema
- **AlertRecord**: registro de alertas com severidade e cooldown
- **PredictionLog**: log de predicoes para auditoria
- **SystemResources / SystemInfo**: informacoes de hardware e sistema operacional

### src/config

Configuracao centralizada.

- Carregamento de variaveis do .env
- Settings tipados com Pydantic
- Separacao por contexto (database, redis, auth, detect, lgpd, monitoring, storage, video, cors)

### src/api

Camada HTTP.

- Endpoints REST via FastAPI
- Schemas de request/response
- Middleware de autenticacao
- Documentacao automatica (Swagger + ReDoc)

## Setup

### Pre-requisitos

- Python 3.12+
- Docker e Docker Compose
- Make (opcional)

### Instalacao local

git clone <repo-url>
cd identificacao-aerea

cp .env.example .env

python -m venv .venv
source .venv/bin/activate

make dev

### Subir com Docker (desenvolvimento)

cp .env.example .env
make docker-dev

### Subir com Docker (producao)

cp .env.example .env
make docker-build
make docker-up

## Comandos

make help         lista todos os comandos disponiveis
make install      instala dependencias de producao
make dev          instala dependencias de desenvolvimento
make run          sobe a API com hot reload
make test         executa os testes
make test-cov     executa testes com relatorio de cobertura
make lint         verifica estilo do codigo (ruff)
make format       formata o codigo automaticamente
make type-check   verificacao estatica de tipos (mypy)
make clean        remove artefatos temporarios
make docker-build builda a imagem docker
make docker-up    sobe containers de producao
make docker-down  derruba containers
make docker-dev   sobe containers de desenvolvimento
make docker-logs  exibe logs em tempo real

## Variaveis de Ambiente

Todas as variaveis estao documentadas no .env.example. As principais:

| Variavel                     | Descricao                           | Default                    |
|------------------------------|-------------------------------------|----------------------------|
| APP_ENV                      | Ambiente da aplicacao               | development                |
| APP_SECRET_KEY               | Chave secreta da aplicacao          | CHANGE_ME                  |
| APP_PORT                     | Porta da API                        | 8000                       |
| DB_HOST                      | Host do PostgreSQL                  | localhost                  |
| DB_NAME                      | Nome do banco                       | identificacao_aerea        |
| REDIS_HOST                   | Host do Redis                       | localhost                  |
| DETECT_MODEL_PATH            | Caminho do modelo YOLOv8            | models/yolov8_aerial.pt    |
| DETECT_CONFIDENCE_THRESHOLD  | Confianca minima para deteccao      | 0.5                        |
| DETECT_DEVICE                | Dispositivo de inferencia           | cpu                        |
| LGPD_ENABLED                 | Ativa modulo LGPD                   | true                       |
| LGPD_AUTO_ANONYMIZE_FACES    | Anonimiza rostos automaticamente    | true                       |
| LGPD_DATA_RETENTION_DAYS     | Dias de retencao de dados pessoais  | 30                         |

## API

Com o servidor rodando, a documentacao interativa fica disponivel em:

| Recurso  | URL                           |
|----------|-------------------------------|
| Swagger  | http://localhost:8000/docs    |
| ReDoc    | http://localhost:8000/redoc   |
| Health   | http://localhost:8000/health  |

## Testes

make test

make test-cov

pytest tests/test_detect_models.py -v

Cobertura minima exigida: 80% (configurado no pyproject.toml).

## Licenca

MIT
