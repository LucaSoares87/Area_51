
---

## Arquivo 2: `docs/adr/003-auth-jwt-rbac.md`

```markdown
# ADR-003: Autenticação JWT com RBAC

## Status

Aceito — 2026-04-19

## Contexto

A API processa imagens aéreas e cruza detecções com dados do CadUnico contendo
CPF, NIS e informações de renda. A LGPD exige controle de acesso e
rastreabilidade. Os requisitos são:

- Autenticar usuários da prefeitura.
- Diferenciar permissões entre visualização, análise e administração.
- Permitir integração máquina-a-máquina com Power Apps.
- Registrar quem acessou quais dados e quando.

## Decisão

### Autenticação via JWT

Fluxo:

