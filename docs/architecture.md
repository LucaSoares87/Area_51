# Arquitetura — Aerial Housing Detection

## Visao geral

O sistema detecta habitacoes em imagens aereas usando um pipeline de dois
estagios e cruza as deteccoes com dados do CadUnico para subsidiar politicas
habitacionais no municipio de Paulista-PE.

## Diagrama de componentes

```text
                    +-------------------+
                    |   Cliente         |
                    |   (Power Apps,    |
                    |    curl, browser) |
                    +--------+----------+
                             |
                             | HTTPS
                             v
                    +--------+----------+
                    |   FastAPI App     |
                    |                   |
                    |  +-------------+  |
                    |  | Auth Module |  |
                    |  | JWT + RBAC  |  |
                    |  +------+------+  |
                    |         |         |
                    |  +------v------+  |
                    |  | Routers     |  |
                    |  | auth detect |  |
                    |  | monitor lgpd|  |
                    |  +------+------+  |
                    +--------+---------+
                             |
              +--------------+--------------+
              |              |              |
    +---------v--+   +------v------+  +----v--------+
    | Detection  |   | Monitoring  |  | LGPD        |
    | Pipeline   |   | Pipeline    |  | Pipeline    |
    +-----+------+   +-------------+  +-------------+
          |
    +-----v------+
    | Stage 1    |
    | SpaceNet   |
    | (ResNet-34)|
    +-----+------+
          |
    +-----v------+
    | Stage 2    |
    | Bootstrap  |
    | (ResNet-18)|
    +-----+------+
          |
    +-----v------+
    | Cross-Ref  |
    | CadUnico   |
    +------------+
```text

## Modulos

### src/api

Factory FastAPI com create_app. Registra routers, middleware de seguranca,
CORS e lifecycle events.

### src/auth

Autenticacao JWT com access token de 15 minutos e refresh token de 7 dias.
RBAC com tres roles: viewer, analyst, admin. Suporta API Keys para integracao
maquina-a-maquina. Rate limiting por sliding window. Middleware de security
headers e audit log.

### src/detect

Pipeline de deteccao em dois estagios. O image_processor valida imagens,
gera tiles com overlap e extrai metadados. O inference engine executa SpaceNet
(Stage 1) para gerar candidatos e Bootstrap Classifier (Stage 2) para filtrar
falsos positivos. O analysis_service orquestra o fluxo completo. O
cross_reference cruza deteccoes com CadUnico usando dados anonimizados.

### src/monitoring

Prediction logger registra toda inferencia com timestamps, confidence scores
e latencias. Drift detector calcula PSI comparando distribuicoes de referencia
e atual. Alert manager gera alertas automaticos por threshold. Health checker
consolida status do sistema. Metrics exporter gera JSON para dashboards.

### src/lgpd

Anonymizer aplica HMAC-SHA256 em CPF e NIS, mascara nomes e enderecos.
Audit logger registra todo acesso a dados pessoais. Consent manager gerencia
consentimentos por titular e proposito. Data deletion processa solicitacoes
de exclusao conforme Art. 18 da LGPD.

## Pipeline de deteccao

```text
Imagem aerea (ex: 4000x4000 px)
    |
    +-- Validacao (formato, tamanho, dimensoes)
    |
    +-- Tiling (512x512, overlap 64px)
    |
    +-- SpaceNet por tile (threshold 0.3)
    |       Gera candidatos (bounding boxes)
    |
    +-- NMS global (IoU 0.4)
    |       Remove duplicatas entre tiles
    |
    +-- Crop de cada candidato (resize 224x224)
    |
    +-- Bootstrap Classifier (threshold 0.7)
    |       Filtra falsos positivos
    |
    +-- Resultado final: deteccoes confirmadas
```text

## Fluxo de dados

```text
Upload -> Validacao -> Tiling -> SpaceNet -> NMS -> Bootstrap -> Resultado
                                                        |
                                                        v
                                                  Cross-reference
                                                  com CadUnico
                                                        |
                                                        v
                                                  Dados anonimizados
                                                  (HMAC-SHA256)
```text

## Decisoes arquiteturais

Documentadas em docs/adr/:

| ADR | Tema |
|---|---|
| 001-bootstrap-architecture | Arquitetura de dois estagios com bootstrap iterativo |
| 002-spacenet-backbone | SpaceNet como backbone de deteccao |
| 003-auth-jwt-rbac | Autenticacao JWT com RBAC |
| 004-ci-cd-pipeline | Pipeline CI/CD com GitHub Actions |
| 005-model-monitoring | Monitoramento de modelo em producao |
| 006-lgpd-compliance | Compliance LGPD para dados sensiveis |

## Stack tecnologica

| Camada | Tecnologia |
|---|---|
| Framework web | FastAPI |
| Linguagem | Python 3.11 |
| ML backbone | SpaceNet (ResNet-34 FPN) |
| ML classifier | ResNet-18 (transfer learning ImageNet) |
| Autenticacao | PyJWT + bcrypt |
| Container | Docker + docker-compose |
| CI/CD | GitHub Actions + GHCR |
| Monitoramento | Built-in (PSI drift, alertas automaticos) |
| Compliance | LGPD (anonimizacao, audit trail, consentimento) |

## Comunicacao entre modulos

| Origem | Destino | Mecanismo |
|---|---|---|
| Router auth | Auth store, tokens, password | Chamada direta |
| Router detect | Analysis service | Chamada direta |
| Analysis service | Inference engine | Chamada direta |
| Analysis service | Cross-reference | Chamada direta |
| Cross-reference | Anonymizer (LGPD) | Chamada direta |
| Cross-reference | Audit logger (LGPD) | Chamada direta |
| Router monitoring | Prediction logger, drift, alerts | Chamada direta |
| Middleware | Rate limiter, security headers | Interceptacao de request |

Nao ha comunicacao assincrona entre modulos. Todos os fluxos sao sincronos
dentro do mesmo processo. Isso simplifica o deploy e debug, sendo adequado
para o volume atual (~100 analises/dia).

## Persistencia

O MVP utiliza armazenamento in-memory para todas as stores (usuarios, tokens,
analises, metricas, audit trail). Dados sao perdidos em reinicio.

Evolucao prevista:

| Dado | Atual | Futuro |
|---|---|---|
| Usuarios | In-memory dict | PostgreSQL |
| Resultados | In-memory dict | PostgreSQL + S3 |
| Metricas | In-memory list | TimescaleDB |
| Audit trail | In-memory list | PostgreSQL append-only |
| Imagens | Filesystem local | S3/MinIO |

## Seguranca

| Camada | Protecao |
|---|---|
| Transporte | HTTPS obrigatorio (TLS 1.2+) |
| Autenticacao | JWT (HS256) com expiracao curta |
| Autorizacao | RBAC com tres niveis |
| Dados pessoais | Anonimizacao HMAC-SHA256 |
| Rate limiting | Sliding window por IP |
| Headers | X-Content-Type-Options, X-Frame-Options, CSP |
| Auditoria | Log de todo acesso a dados sensiveis |

## Limites conhecidos

- In-memory: perda de dados em reinicio.
- Single process: sem escala horizontal.
- Mock inference no dev: resultados sinteticos, nao reais.
- SpaceNet treinado em cidades americanas: possivel vies em construcoes informais brasileiras.
- Sem suporte a GPU no Docker por padrao (requer nvidia-docker).
