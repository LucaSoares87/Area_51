# ADR-004: Pipeline CI/CD com GitHub Actions

## Status
**Aceito** — 2026-04-19

## Contexto

O projeto precisa de integração e entrega contínua para:
- Garantir que código novo não quebre o existente.
- Automatizar build e deploy.
- Manter qualidade de código (lint, type check).
- Gerar imagens Docker reprodutíveis.

## Decisão

### CI (Integração Contínua) — `.github/workflows/ci.yml`

Executa em **todo push e pull request**:

