# Guia de Operação Local - Area 51

## 1. Objetivo

Este guia descreve como executar localmente o projeto Area 51 para demonstração, validação técnica e piloto controlado.

O objetivo é permitir que um usuário técnico consiga subir a aplicação, validar os testes, acessar a interface, realizar login, consultar ativos, enviar imagem aérea e abrir o mapa operacional.

## 2. Pré-requisitos

Antes de executar o projeto, validar:

- Python instalado.
- Dependências do projeto instaladas.
- Repositório atualizado.
- Terminal PowerShell disponível.
- Navegador instalado.
- Porta `8000` disponível.
- Ambiente local com permissão de escrita nas pastas `data/` e `reports/`.

## 3. Entrar na pasta do projeto

Executar:

```powershell
cd "C:\Users\Lucas Soares\Downloads\Area_51\Area_51"

4. Atualizar a branch principal

Antes de iniciar qualquer validação, usar:

git checkout main
git pull origin main
git status

Resultado esperado:

On branch main
Your branch is up to date with 'origin/main'.

nothing to commit, working tree clean
5. Rodar testes automatizados

Executar:

python -m pytest tests\test_api tests\test_pipeline tests\test_reports tests\test_scripts tests\test_detection tests\test_bootstrap tests\test_losses tests\test_imports tests\test_territory tests\test_services tests\test_integrations -v

Resultado esperado:

passed

Se houver falha, não seguir para demonstração antes de corrigir.

6. Subir a API local

Executar:

python -m uvicorn src.aerial_housing_detection.api.main:app --reload

Resultado esperado:

Uvicorn running on http://127.0.0.1:8000
Application startup complete.

Manter esse terminal aberto enquanto estiver usando o sistema.

7. Acessar a aplicação

No navegador, abrir:

http://127.0.0.1:8000/

A aplicação deve redirecionar para:

http://127.0.0.1:8000/login
8. Login

A tela de login usa matrícula funcional e senha.

Exemplo para ambiente local:

Matrícula: B626278
Senha: teste123

Após login bem-sucedido, a aplicação deve abrir:

http://127.0.0.1:8000/app
9. Criar usuário local de teste

Se o usuário ainda não existir, criar pelo endpoint de registro existente.

Com a API ligada, em outro PowerShell, executar:

Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/api/v1/auth/register" `
  -ContentType "application/json" `
  -Body '{
    "username": "B626278",
    "email": "b626278@neoenergia.local",
    "full_name": "Lucas Soares",
    "password": "teste123"
  }'

Se o usuário já existir, fazer login diretamente.

10. Interface operacional

Após o login, validar:

Usuário logado aparece no topo.
Botão Sair está visível.
Card Mapa de calor e transformadores está visível.
Formulários de busca estão visíveis.
Upload de imagem aérea está visível.
Resumo da análise está visível.
Resultado técnico está visível.
11. Busca operacional

A interface permite buscar por:

Matrícula.
Transformador.
Alimentador.
Subestação.
Coordenadas.

Exemplos de valores simulados podem variar conforme a base local carregada.

Sugestões:

Transformador: TR-001
Alimentador: AL-01
Subestação: SE-01

Para coordenadas, usar valores compatíveis com a área simulada ou real importada.

12. Upload de imagem aérea

Na seção Imagem aérea:

Selecionar imagem local.
Conferir a pré-visualização.
Clicar em Enviar imagem.
Verificar o resumo da análise.
Verificar o JSON técnico retornado.

Formatos esperados:

PNG.
JPG.
JPEG.
WEBP, se suportado pela aplicação.
13. Mapa operacional

A interface possui o botão:

Abrir mapa

Esse botão abre:

http://127.0.0.1:8000/app/map

Se o mapa ainda não tiver sido gerado, o sistema retornará:

Mapa operacional ainda não foi gerado. Execute a geração do mapa antes de acessar esta página.

Nesse caso, gerar o mapa antes de acessar.

14. Gerar mapa operacional

Executar o script de geração de mapa conforme a estrutura do projeto:

python -m scripts.generate_transformer_operational_map --reference-month 2026-05

Após a execução, validar se foi criado:

reports/transformer_operational_map.html

Depois acessar novamente:

http://127.0.0.1:8000/app/map
15. Importar dados simulados

Se a base local estiver vazia, importar os dados simulados disponíveis na pasta data/samples.

Exemplo:

python -m scripts.import_monthly_losses --input data\samples\monthly_losses_real_simulado.csv
python -m scripts.import_ibge_sectors --input data\samples\ibge_sectors_real_simulado.csv
python -m scripts.import_cras_territories --input data\samples\cras_territories_real_simulado.csv
python -m scripts.import_territory_links --input data\samples\territory_links_real_simulado.csv
python -m scripts.import_solar_estimates --input data\samples\solar_estimates_real_simulado.csv

Depois gerar novamente o mapa operacional.

16. Encerrar execução

No terminal onde o Uvicorn está rodando, pressionar:

CTRL + C
17. Limpeza de artefatos locais

Antes de qualquer commit, limpar arquivos gerados:

git restore data\auth\users.json

Remove-Item data\area51.db -ErrorAction SilentlyContinue
Remove-Item reports\*.csv -ErrorAction SilentlyContinue
Remove-Item reports\*.html -ErrorAction SilentlyContinue
Remove-Item reports\*.json -ErrorAction SilentlyContinue
Remove-Item reports\uploads\* -ErrorAction SilentlyContinue

git status
18. Arquivos que não devem entrar no commit

Não versionar:

Banco local gerado.
Relatórios HTML gerados.
Relatórios CSV gerados.
Evidências JSON geradas.
Uploads de imagens.
Usuários locais de teste.

Exemplos:

data/area51.db
data/auth/users.json
reports/*.html
reports/*.csv
reports/*.json
reports/uploads/
19. Problemas comuns
19.1 Porta 8000 já está em uso

Encerrar outro processo usando a porta ou alterar a porta do Uvicorn.

19.2 Login não funciona

Verificar:

Se a API está ligada.
Se o usuário foi criado.
Se a matrícula está correta.
Se a senha está correta.
Se o endpoint /api/v1/auth/login está respondendo.
19.3 /app volta para /login

Isso indica que não há token salvo no sessionStorage.

Solução:

Fazer login novamente.
Verificar se o login retornou access_token.
Verificar se o navegador não bloqueou armazenamento local.
19.4 Mapa retorna 404

Isso indica que o arquivo do mapa ainda não foi gerado.

Solução:

python -m scripts.generate_transformer_operational_map --reference-month 2026-05
19.5 Testes geram arquivos em reports/

Isso é esperado. Limpar antes de commit.

20. Resultado esperado da operação local

Ao final da operação local, deve ser possível:

Acessar a tela de login.
Entrar com matrícula e senha.
Visualizar a interface operacional.
Consultar ativos.
Enviar imagem aérea.
Visualizar resultado técnico.
Abrir o mapa operacional.
Encerrar a sessão com o botão Sair.