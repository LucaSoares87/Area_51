# Guia do Usuario

## Primeiros passos

### 1. Acessar a API

URL base: configurada pelo administrador (ex: https://aerial.paulista.pe.gov.br)

Documentacao interativa: {URL_BASE}/api/v1/docs

### 2. Autenticacao

Fazer login com suas credenciais:

    curl -X POST {URL_BASE}/api/v1/auth/login \
      -H "Content-Type: application/json" \
      -d '{
        "email": "seu.email@paulista.pe.gov.br",
        "password": "sua-senha"
      }'

Resposta:

    {
      "access_token": "eyJ...",
      "refresh_token": "eyJ...",
      "token_type": "bearer",
      "expires_in": 900
    }

Usar o access_token em todas as requisicoes seguintes:

    Authorization: Bearer eyJ...

### 3. Renovar token

O access_token expira em 15 minutos. Para renovar:

    curl -X POST {URL_BASE}/api/v1/auth/refresh \
      -H "Content-Type: application/json" \
      -d '{"refresh_token": "eyJ..."}'

O refresh_token dura 7 dias. Apos esse periodo, e necessario fazer login novamente.

### 4. Consultar seus dados

    curl {URL_BASE}/api/v1/auth/me \
      -H "Authorization: Bearer {TOKEN}"

## Roles e permissoes

| Role | O que pode fazer |
|---|---|
| viewer | Consultar resultados proprios, ver configuracao do pipeline |
| analyst | Tudo de viewer, enviar imagens, executar analises, cruzar CadUnico |
| admin | Tudo de analyst, gerenciar usuarios, ver todos os resultados, administrar LGPD |

Sua role e definida pelo administrador no momento do cadastro.

## Analisar imagem aerea

Requer role analyst ou admin.

### Analise individual

    curl -X POST {URL_BASE}/api/v1/detect/analyze \
      -H "Authorization: Bearer {TOKEN}" \
      -F "file=@imagem_aerea.tif" \
      -F "confidence_threshold=0.5" \
      -F "region=paulista_centro"

Resposta:

    {
      "analysis_id": "ana_abc123",
      "status": "completed",
      "image_metadata": {
        "filename": "imagem_aerea.tif",
        "width": 4000,
        "height": 4000,
        "format": "TIFF"
      },
      "detections": [
        {
          "id": "det_001",
          "bbox": {"x_min": 100, "y_min": 200, "x_max": 250, "y_max": 350},
          "confidence": 0.87,
          "class_name": "habitacao",
          "stage1_confidence": 0.65,
          "stage2_confidence": 0.87
        }
      ],
      "summary": {
        "total_detections": 42,
        "average_confidence": 0.78,
        "processing_time_ms": 3200
      }
    }

Campos relevantes:

| Campo | Significado |
|---|---|
| analysis_id | Identificador unico para consultar depois |
| confidence | Confianca final (Stage 2) de que e uma habitacao |
| stage1_confidence | Confianca do SpaceNet (deteccao de construcao) |
| stage2_confidence | Confianca do Bootstrap (classificacao habitacao) |
| bbox | Coordenadas do retangulo da deteccao na imagem |

### Analise em lote

Ate 10 imagens por requisicao:

    curl -X POST {URL_BASE}/api/v1/detect/analyze/batch \
      -H "Authorization: Bearer {TOKEN}" \
      -F "files=@area1.tif" \
      -F "files=@area2.tif" \
      -F "files=@area3.tif" \
      -F "confidence_threshold=0.5"

Resposta:

    {
      "batch_id": "bat_xyz789",
      "total_images": 3,
      "results": [
        { "analysis_id": "ana_001", "status": "completed", ... },
        { "analysis_id": "ana_002", "status": "completed", ... },
        { "analysis_id": "ana_003", "status": "completed", ... }
      ],
      "total_processing_time_ms": 9600
    }

### Consultar resultado anterior

    curl {URL_BASE}/api/v1/detect/results/{analysis_id} \
      -H "Authorization: Bearer {TOKEN}"

### Configuracao do pipeline

Consultar parametros atuais do detector:

    curl {URL_BASE}/api/v1/detect/config \
      -H "Authorization: Bearer {TOKEN}"

Resposta:

    {
      "spacenet_confidence_threshold": 0.3,
      "spacenet_nms_threshold": 0.4,
      "bootstrap_confidence_threshold": 0.7,
      "tile_size": 512,
      "tile_overlap": 64,
      "max_image_size_mb": 50,
      "supported_formats": ["TIFF", "JPEG", "PNG"]
    }

## Cruzamento com CadUnico

Requer role analyst ou admin. Apos uma analise, cruzar deteccoes com dados
do CadUnico:

    curl -X POST {URL_BASE}/api/v1/detect/cross-reference/{analysis_id} \
      -H "Authorization: Bearer {TOKEN}"

Resposta:

    {
      "analysis_id": "ana_abc123",
      "matches": [
        {
          "detection_id": "det_001",
          "cadunico_match": true,
          "anonymized_data": {
            "cpf_hash": "a1b2c3d4e5f6",
            "name_initials": "M. S.",
            "address_masked": "Rua A, ***, Centro",
            "income_range": "0-1 SM"
          }
        }
      ],
      "total_matches": 35,
      "match_rate": 0.83
    }

Dados pessoais nunca aparecem em texto claro:

| Campo original | Dado retornado | Metodo |
|---|---|---|
| CPF | Hash irreversivel | HMAC-SHA256 |
| NIS | Hash irreversivel | HMAC-SHA256 |
| Nome | Apenas iniciais | Truncamento |
| Endereco | Numero mascarado | Substituicao por *** |
| Renda | Faixa em salarios minimos | Generalizacao |

## API Keys (integracao Power Apps)

API Keys permitem integracao maquina-a-maquina sem login interativo.

### Criar API key

    curl -X POST {URL_BASE}/api/v1/auth/api-keys \
      -H "Authorization: Bearer {TOKEN}" \
      -H "Content-Type: application/json" \
      -d '{"name": "power-apps-producao", "expires_in_days": 90}'

Resposta:

    {
      "id": "key_abc123",
      "name": "power-apps-producao",
      "key": "ak_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
      "created_at": "2026-04-19T12:00:00Z",
      "expires_at": "2026-07-18T12:00:00Z"
    }

A chave completa e retornada apenas na criacao. Armazene em local seguro.

### Usar API key

Enviar no header X-API-Key em vez de Authorization:

    curl {URL_BASE}/api/v1/detect/results/ana_abc123 \
      -H "X-API-Key: ak_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

### Listar API keys

    curl {URL_BASE}/api/v1/auth/api-keys \
      -H "Authorization: Bearer {TOKEN}"

A listagem mostra apenas o prefixo da chave, nunca a chave completa.

### Revogar API key

    curl -X DELETE {URL_BASE}/api/v1/auth/api-keys/{key_id} \
      -H "Authorization: Bearer {TOKEN}"

Apos revogacao, a chave para de funcionar imediatamente.

## Monitoramento

### Health check

Endpoint publico, sem autenticacao:

    curl {URL_BASE}/health

### Metricas do modelo

    curl {URL_BASE}/api/v1/monitoring/metrics?period=24h \
      -H "Authorization: Bearer {TOKEN}"

Periodos disponiveis: 1h, 6h, 24h, 7d, 30d.

### Drift do modelo

    curl {URL_BASE}/api/v1/monitoring/drift \
      -H "Authorization: Bearer {TOKEN}"

Status possiveis:

| Status | PSI | Significado |
|---|---|---|
| stable | menor que 0.1 | Modelo funcionando normalmente |
| moderate_drift | 0.1 a 0.2 | Mudanca detectada, monitorar |
| severe_drift | acima de 0.2 | Retreino recomendado |

### Alertas

Listar alertas ativos:

    curl {URL_BASE}/api/v1/monitoring/alerts?status=active \
      -H "Authorization: Bearer {TOKEN}"

Reconhecer um alerta:

    curl -X POST {URL_BASE}/api/v1/monitoring/alerts/{alert_id}/acknowledge \
      -H "Authorization: Bearer {TOKEN}"

### Exportar metricas

    curl {URL_BASE}/api/v1/monitoring/export?format=json \
      -H "Authorization: Bearer {TOKEN}"

## LGPD

### Consultar audit trail

Requer role admin:

    curl "{URL_BASE}/api/v1/lgpd/audit-log?page=1&page_size=50" \
      -H "Authorization: Bearer {TOKEN}"

### Registrar consentimento

    curl -X POST {URL_BASE}/api/v1/lgpd/consent \
      -H "Authorization: Bearer {TOKEN}" \
      -H "Content-Type: application/json" \
      -d '{
        "subject_id": "titular-001",
        "purpose": "social_policy",
        "legal_basis": "LGPD Art. 7, III"
      }'

### Consultar consentimentos de um titular

    curl {URL_BASE}/api/v1/lgpd/consent/{subject_id} \
      -H "Authorization: Bearer {TOKEN}"

### Solicitar exclusao de dados (Art. 18)

    curl -X POST {URL_BASE}/api/v1/lgpd/deletion-request \
      -H "Authorization: Bearer {TOKEN}" \
      -H "Content-Type: application/json" \
      -d '{
        "subject_id": "titular-001",
        "reason": "Solicitacao do titular via ouvidoria"
      }'

### Consultar status da exclusao

    curl {URL_BASE}/api/v1/lgpd/deletion-request/{request_id} \
      -H "Authorization: Bearer {TOKEN}"

### Relatorio de compliance

    curl {URL_BASE}/api/v1/lgpd/report \
      -H "Authorization: Bearer {TOKEN}"

### Dados do Encarregado (DPO)

Endpoint publico, sem autenticacao:

    curl {URL_BASE}/api/v1/lgpd/dpo

## Formatos de imagem suportados

| Formato | Extensoes | Observacao |
|---|---|---|
| TIFF/GeoTIFF | .tif, .tiff | Recomendado para imagens aereas |
| JPEG | .jpg, .jpeg | Menor qualidade, compressao com perda |
| PNG | .png | Boa qualidade, arquivos grandes |

Tamanho maximo: 50 MB por imagem.
Dimensoes recomendadas: 2000x2000 a 8000x8000 pixels.

## Codigos de erro comuns

| Codigo | Significado | Acao |
|---|---|---|
| 400 | Requisicao mal formada | Verificar corpo da requisicao |
| 401 | Token expirado ou invalido | Renovar com /auth/refresh |
| 403 | Sem permissao para esta acao | Verificar role do usuario |
| 404 | Recurso nao encontrado | Verificar ID na URL |
| 409 | Conflito (ex: email duplicado) | Usar outro email |
| 413 | Imagem excede 50 MB | Reduzir resolucao ou recortar |
| 422 | Dados invalidos (formato, tipo) | Verificar formatos suportados |
| 429 | Muitas requisicoes | Aguardar e tentar novamente |
| 500 | Erro interno do servidor | Contactar administrador |

## Fluxo tipico de uso

1. Login com email e senha (POST /auth/login)
2. Enviar imagem aerea para analise (POST /detect/analyze)
3. Verificar deteccoes no resultado
4. Cruzar com CadUnico se necessario (POST /detect/cross-reference/{id})
5. Consultar resultados anteriores (GET /detect/results/{id})
6. Monitorar saude do modelo periodicamente (GET /monitoring/metrics)

## Suporte

Em caso de problemas:

- Verificar se o token esta valido (GET /auth/me)
- Consultar health do sistema (GET /health)
- Contactar o administrador do sistema
- Para questoes sobre dados pessoais, contactar o DPO (GET /lgpd/dpo)
