# Guia de Deploy

## Pre-requisitos

- Docker 24+ e Docker Compose v2
- 4 GB RAM minimo (8 GB recomendado para inferencia com GPU)
- 20 GB disco
- Dominio configurado (para HTTPS em producao)

## Deploy local (desenvolvimento)

Clonar o repositorio:

    git clone https://github.com/prefeitura-paulista/aerial-housing-detection.git
    cd aerial-housing-detection

Configurar variaveis:

    cp .env.example .env

Subir com hot-reload:

    make dev

A aplicacao estara disponivel em http://localhost:8000.
Documentacao interativa em http://localhost:8000/api/v1/docs.

## Deploy com Docker Compose (producao)

### 1. Configurar variaveis de ambiente

    cp .env.example .env

Editar .env com valores de producao:

    AUTH_SECRET_KEY=<chave-segura-gerada-com-openssl>
    ADMIN_EMAIL=admin@paulista.pe.gov.br
    ADMIN_PASSWORD=<senha-forte>
    DETECTION_MOCK_INFERENCE=false

Gerar chave segura:

    openssl rand -hex 32

### 2. Subir a stack

    docker-compose up -d

### 3. Verificar saude

    curl http://localhost:8000/health

Resposta esperada:

    {
      "status": "healthy",
      "version": "1.0.0",
      "uptime_seconds": 12.5
    }

### 4. Popular dados iniciais

    make seed

### 5. Configurar HTTPS (Nginx reverse proxy)

Criar arquivo /etc/nginx/sites-available/aerial:

    server {
        listen 443 ssl;
        server_name aerial.paulista.pe.gov.br;

        ssl_certificate /etc/letsencrypt/live/aerial.paulista.pe.gov.br/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/aerial.paulista.pe.gov.br/privkey.pem;

        client_max_body_size 50M;

        location / {
            proxy_pass http://127.0.0.1:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }

    server {
        listen 80;
        server_name aerial.paulista.pe.gov.br;
        return 301 https://$server_name$request_uri;
    }

Ativar e reiniciar:

    sudo ln -s /etc/nginx/sites-available/aerial /etc/nginx/sites-enabled/
    sudo nginx -t
    sudo systemctl reload nginx

Gerar certificado com Let's Encrypt:

    sudo certbot --nginx -d aerial.paulista.pe.gov.br

## Deploy via CI/CD

O pipeline CD e acionado automaticamente:

- Push na branch main: deploy em staging
- Tag v*.*.*: deploy em staging e depois producao

### Secrets necessarios no GitHub

| Secret | Descricao |
|---|---|
| STAGING_HOST | IP do servidor staging |
| STAGING_USER | Usuario SSH |
| STAGING_SSH_KEY | Chave privada SSH |
| STAGING_ADMIN_PASSWORD | Senha admin staging |
| PRODUCTION_HOST | IP do servidor producao |
| PRODUCTION_USER | Usuario SSH |
| PRODUCTION_SSH_KEY | Chave privada SSH |

### Variables necessarias no GitHub

| Variable | Descricao |
|---|---|
| STAGING_URL | URL do staging para smoke test |
| PRODUCTION_URL | URL de producao para smoke test |

### Fluxo do pipeline

    push main -> CI (lint, test, coverage)
                    |
                    v
                 Build imagem Docker
                    |
                    v
                 Push para GHCR
                    |
                    v
                 Deploy staging via SSH
                    |
                    v
                 Smoke test staging
                    |
                    v (apenas tags v*.*.*)
                 Aprovacao manual
                    |
                    v
                 Deploy producao via SSH
                    |
                    v
                 Smoke test producao
                    |
                    v (se falhar)
                 Rollback automatico

## Rollback

### Automatico

O pipeline CD executa rollback automatico se o health check falhar apos
deploy em producao. O backup de .env e docker-compose.yml e restaurado
a partir do diretorio /opt/backups/aerial/.

### Manual

    ssh deploy@servidor
    cd /opt/aerial-housing-detection

Listar backups disponiveis:

    ls /opt/backups/aerial/

Restaurar backup especifico:

    BACKUP=/opt/backups/aerial/20260419_120000
    cp $BACKUP/.env .env
    cp $BACKUP/docker-compose.yml docker-compose.yml
    docker-compose up -d

Verificar saude apos rollback:

    curl http://localhost:8000/health

## Monitoramento pos-deploy

Logs da aplicacao:

    docker-compose logs -f app

Metricas do modelo:

    curl http://localhost:8000/api/v1/monitoring/metrics

Drift do modelo:

    curl http://localhost:8000/api/v1/monitoring/drift

Alertas ativos:

    curl -H "Authorization: Bearer <token>" \
      http://localhost:8000/api/v1/monitoring/alerts

Exportar metricas para dashboard:

    curl -H "Authorization: Bearer <token>" \
      http://localhost:8000/api/v1/monitoring/export

## Estrutura de diretorios no servidor

    /opt/aerial-housing-detection/
        .env
        docker-compose.yml
        models/
            spacenet/model.pth
            bootstrap/model.pth
        data/
            uploads/
            results/
            metrics/

    /opt/backups/aerial/
        20260419_120000/
            .env
            docker-compose.yml

## Checklist de deploy

Antes de deployar em producao, verificar:

| Item | Verificacao |
|---|---|
| .env configurado | AUTH_SECRET_KEY gerado com openssl |
| Mock desativado | DETECTION_MOCK_INFERENCE=false |
| Modelos presentes | models/spacenet/model.pth e models/bootstrap/model.pth |
| HTTPS ativo | Certificado SSL valido |
| DNS configurado | Dominio apontando para IP do servidor |
| Backup configurado | Diretorio /opt/backups/aerial/ criado |
| Nginx configurado | client_max_body_size 50M |
| Firewall | Portas 80 e 443 abertas, 8000 bloqueada externamente |
| Admin criado | Seed executado ou usuario admin criado manualmente |
| Health check | GET /health retorna status healthy |
