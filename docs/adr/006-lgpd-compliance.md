# ADR-006: Compliance LGPD para Dados Sensíveis

## Status
**Aceito** — 2026-04-19

## Contexto

O sistema cruza **imagens aéreas** (que podem identificar residências) com
**dados do CadÚnico** (CPF, NIS, renda, composição familiar). A LGPD
(Lei 13.709/2018) se aplica integralmente, especialmente:

- **Art. 7, III**: Tratamento para execução de políticas públicas.
- **Art. 11, II, b**: Dados sensíveis para políticas públicas (sem consentimento, mas com transparência).
- **Art. 18**: Direitos do titular (acesso, correção, exclusão).
- **Art. 37**: Registro de operações de tratamento.
- **Art. 41**: Encarregado de dados (DPO).
- **Art. 46**: Medidas de segurança.

## Decisão

### 1. Base legal

O tratamento se fundamenta no **Art. 7, inciso III** — execução de políticas
públicas pela administração pública. Isso **dispensa consentimento** mas
**não dispensa transparência, segurança e direitos do titular**.

### 2. Anonimização (Art. 12)

Todos os identificadores pessoais são anonimizados antes de aparecer em
qualquer output da API:

| Dado | Técnica | Exemplo |
|---|---|---|
| CPF | HMAC-SHA256 + truncate | `11122233344` → `a1b2c3d4e5f6` |
| Nome | Preserva iniciais | `Maria Silva` → `M. S.` |
| Endereço | Remove número | `Rua A, 123, Centro` → `Rua A, ***, Centro` |
| NIS | HMAC-SHA256 + truncate | `12345678901` → `f7e8d9c0b1a2` |

- **Salt rotativo**: HMAC usa salt configurável (rotacionar periodicamente).
- **Irreversível**: não é possível recuperar o CPF a partir do hash.
- **Determinístico**: mesmo CPF sempre gera mesmo hash (permite join anonimizado).

### 3. Audit Trail (Art. 37)

**Todo** acesso a dados pessoais é registrado com:

```json
{
  "timestamp": "2026-04-19T12:00:00Z",
  "user_id": "usr_123",
  "user_email": "analista@paulista.pe.gov.br",
  "user_role": "analyst",
  "client_ip": "10.0.0.50",
  "action": "cross_reference",
  "resource": "/api/v1/detect/cross-reference/abc123",
  "purpose": "social_policy",
  "legal_basis": "LGPD Art. 7, III",
  "data_categories": ["cpf", "nis", "income", "geolocation"],
  "data_subject_count": 15
}
