# Checklist do Piloto - Area 51

## 1. Objetivo do checklist

Este checklist deve ser usado antes da execução do piloto operacional do Area 51.

A finalidade é garantir que ambiente, dados, responsáveis, critérios de validação e roteiro de execução estejam minimamente preparados antes da demonstração ou uso controlado com dados reais.

## 2. Situação esperada antes do piloto

Antes de iniciar o piloto, o projeto deve estar com:

- Branch principal atualizada.
- Testes automatizados aprovados.
- Interface operacional acessível.
- Login funcional.
- Rotas principais respondendo.
- Dados mínimos importados.
- Mapa operacional gerado.
- Área piloto definida.
- Responsáveis técnicos identificados.
- Critérios de sucesso acordados.

## 3. Checklist técnico

### 3.1 Ambiente local

- [ ] Python instalado e compatível com o projeto.
- [ ] Dependências instaladas.
- [ ] Projeto clonado ou atualizado.
- [ ] Branch `main` limpa.
- [ ] Arquivo de configuração local validado.
- [ ] Banco local ou base de dados de teste disponível.
- [ ] Pasta `data/` criada.
- [ ] Pasta `reports/` criada.
- [ ] Porta da API disponível.

### 3.2 Testes automatizados

Executar:

```powershell
python -m pytest tests\test_api tests\test_pipeline tests\test_reports tests\test_scripts tests\test_detection tests\test_bootstrap tests\test_losses tests\test_imports tests\test_territory tests\test_services tests\test_integrations -v