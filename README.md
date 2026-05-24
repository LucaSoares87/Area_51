# Area 51 - Aerial Housing Detection

Sistema backend em Python para estimar a quantidade de residências em áreas de risco a partir de imagens aéreas.

O projeto foi estruturado para apoiar concessionárias de energia em análises territoriais onde a medição presencial é difícil, insegura ou operacionalmente limitada.

## Objetivo

Receber uma imagem aérea, processar candidatos a telhado, estimar a quantidade de residências e gerar evidências operacionais em formato CSV e HTML.

O sistema atual entrega o core funcional do pipeline. A detecção visual ainda utiliza uma abordagem determinística inicial, preparada para evolução futura com modelos de visão computacional, como YOLO, classificadores auxiliares e filtros de validação.

## Funcionalidades atuais

- API FastAPI com endpoints principais
- Pipeline de detecção de telhados
- Pré-processamento e validação de imagem
- Contagem estimada de residências
- Geração de relatório CSV
- Geração de mapa HTML simples
- Scripts operacionais para execução local
- Tratamento controlado de erros
- Testes automatizados
- Validação com Ruff
- Build Docker via CI

## Stack principal

| Camada | Tecnologia |
|---|---|
| Linguagem | Python 3.12+ |
| API | FastAPI |
| Validação | Pydantic |
| Logs | Structlog |
| Imagem | Pillow |
| Testes | Pytest |
| Qualidade | Ruff |
| Container | Docker |
| CI/CD | GitHub Actions |

## Estrutura principal

```text
Area_51/
|
|-- config/
|   |-- settings.py
|   |-- logging_config.py
|
|-- src/
|   |-- aerial_housing_detection/
|       |-- api/
|       |   |-- main.py
|       |   |-- routes/
|       |   |   |-- detection.py
|       |   |   |-- health.py
|       |   |   |-- report.py
|       |   |-- schemas/
|       |       |-- requests.py
|       |       |-- responses.py
|       |
|       |-- detection/
|       |   |-- image_preprocessor.py
|       |   |-- model_manager.py
|       |   |-- post_processor.py
|       |   |-- roof_detector.py
|       |
|       |-- domain/
|       |   |-- detection.py
|       |   |-- exceptions.py
|       |   |-- geometry.py
|       |   |-- report.py
|       |
|       |-- pipeline/
|       |   |-- orchestrator.py
|       |   |-- pipeline_state.py
|       |   |-- step_registry.py
|       |
|       |-- reports/
|           |-- map_renderer.py
|           |-- report_generator.py
|
|-- scripts/
|   |-- run_inference.py
|   |-- generate_report.py
|
|-- tests/
|   |-- test_api/
|   |-- test_pipeline/
|   |-- test_reports/
|   |-- test_scripts/
|
|-- data/
|-- reports/
|-- models/