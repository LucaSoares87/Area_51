# Roteiro de Demonstração - Area 51

## 1. Objetivo da demonstração

Este roteiro orienta a apresentação do Area 51 para uma demonstração técnica ou executiva.

A demonstração deve mostrar como o sistema apoia a análise de perdas, priorização territorial, geração distribuída, mapa operacional, busca de ativos e análise por imagem aérea.

## 2. Público recomendado

A demonstração pode ser realizada para:

- Equipe de perdas.
- Equipe de medição.
- Equipe de operação.
- Equipe de planejamento.
- Equipe de tecnologia.
- Gestão técnica.
- Gestão executiva.
- Representantes de campo.

## 3. Mensagem central

O Area 51 não substitui a decisão técnica da concessionária.

Ele organiza dados dispersos e gera uma visão operacional integrada para apoiar:

- Priorização de áreas.
- Identificação de perdas.
- Análise de transformadores críticos.
- Ajuste de perda por geração distribuída.
- Cruzamento com indicadores socioenergéticos.
- Planejamento de inspeção.
- Apoio à validação de campo.

## 4. Preparação antes da apresentação

Antes de iniciar, validar:

- API local ligada.
- Usuário de teste criado.
- Login funcionando.
- Interface `/app` abrindo após login.
- Dados simulados ou reais importados.
- Mapa operacional gerado.
- Navegador aberto em `/login`.
- Terminal preparado para demonstrar logs, se necessário.

## 5. Sequência sugerida da demonstração

### 5.1 Abertura

Explicar o problema:

- Dados de perdas ficam distribuídos em diferentes bases.
- A relação cliente, transformador, alimentador e território nem sempre é simples.
- Geração distribuída pode distorcer a leitura inicial de perdas.
- Áreas vulneráveis exigem cuidado na priorização.
- Campo precisa de evidências melhores para orientar ação.

Mensagem sugerida:

> O objetivo do Area 51 é transformar dados elétricos, territoriais e operacionais em uma visão priorizada de apoio à decisão.

## 6. Etapa 1 - Login

Abrir:

```text
http://127.0.0.1:8000/login

Demonstrar:

Identidade visual.
Matrícula funcional.
Campo de senha.
Botão de mostrar/ocultar senha.
Entrada no ambiente operacional.

Exemplo:

Matrícula: B626278
Senha: teste123

Pontos a destacar:

O login está integrado ao fluxo de autenticação existente.
A matrícula é usada como identificador do colaborador.
A interface já prepara a experiência de sessão.
7. Etapa 2 - Interface operacional

Após login, abrir a tela principal.

Destacar:

Usuário logado.
Botão Sair.
Busca operacional.
Upload de imagem aérea.
Mapa operacional.
Resultado amigável.
Resultado técnico em JSON.

Mensagem sugerida:

A proposta é permitir que um usuário operacional consiga consultar dados sem depender diretamente de terminal ou scripts.

8. Etapa 3 - Busca por transformador

Usar exemplo:

Transformador: TR-001

Demonstrar:

Retorno da API.
Área associada.
Alimentador.
Subestação.
Localidade.
Resultado técnico.

Explicar:

O transformador é o ponto central para consolidar clientes, perdas, GD e território.
A análise por transformador ajuda a sair de uma visão ampla para uma ação direcionada.
9. Etapa 4 - Busca por alimentador

Usar exemplo:

Alimentador: AL-01

Demonstrar:

Lista de ativos vinculados.
Quantidade de registros.
Relação com transformadores.
Resultado agregado.

Explicar:

O alimentador permite uma análise em escala maior.
É útil para identificar bolsões de perda ou áreas concentradas.
10. Etapa 5 - Busca por coordenadas

Usar coordenadas compatíveis com a base carregada.

Demonstrar:

Busca do ativo mais próximo.
Distância estimada.
Relação com área operacional.

Explicar:

Essa função ajuda quando a equipe tem uma localização de campo, mas não sabe exatamente o ativo associado.
Pode apoiar análise por imagem, inspeção ou ocorrência.
11. Etapa 6 - Upload de imagem aérea

Selecionar uma imagem de teste.

Demonstrar:

Seleção de arquivo.
Pré-visualização.
Envio.
Retorno com telhados estimados.
Confiança média.
Identificador da análise.

Explicar:

A análise de imagem é uma camada auxiliar.
O objetivo é apoiar a estimativa de telhados, áreas ocupadas e potencial de cruzamento com consumo, GD e perdas.
12. Etapa 7 - Mapa operacional

Clicar em:

Abrir mapa

A rota esperada:

http://127.0.0.1:8000/app/map

Demonstrar:

Transformadores no mapa.
Perdas estimadas.
Geração solar estimada.
Perda ajustada.
Prioridade.
Risco.

Explicar:

O mapa transforma a análise em visão territorial.
Ajuda a visualizar concentração de risco.
Apoia priorização para operação e campo.
13. Etapa 8 - Análise socioenergética

Apresentar a proposta da visão socioenergética:

Perdas.
Telhados.
Clientes.
IBGE.
CRAS.
Vulnerabilidade.
Priorização.

Explicar:

A priorização não deve considerar apenas perda elétrica.
Território e vulnerabilidade ajudam a orientar abordagem, comunicação e estratégia de campo.
A atuação pode ser técnica, social ou combinada.
14. Etapa 9 - Geração distribuída

Explicar o papel da GD:

Exemplo:

Cliente gerou 100 kWh
Cliente consumiu 80 kWh
Cliente injetou 20 kWh

Mensagem sugerida:

Se a geração distribuída não for considerada corretamente, parte do balanço pode ser interpretada como perda. O sistema prepara uma camada para ajustar essa análise e reduzir falso positivo.

Demonstrar, se disponível:

Dados de GD.
Energia gerada.
Energia consumida.
Energia injetada.
Perda ajustada.
15. Etapa 10 - Encerramento técnico

Mostrar que o projeto possui:

Testes automatizados.
APIs.
Interface web.
Login.
Mapa.
Upload de imagem.
Importadores.
Documentação de piloto.
Estrutura para dados reais.

Mensagem sugerida:

O projeto está preparado para um piloto controlado. A próxima decisão é selecionar uma área, conectar dados reais e comparar os resultados com conhecimento de campo.

16. Perguntas esperadas
O sistema já decide onde há fraude?

Não. O sistema apoia priorização de perdas e anomalias. A decisão final exige validação técnica e de campo.

O sistema usa dados reais?

Ele está preparado para dados reais. No piloto, os dados simulados devem ser substituídos por bases autorizadas da concessionária.

O sistema considera geração distribuída?

Sim. A arquitetura já possui contrato para integrar dados de GD e ajustar a leitura de perdas.

O mapa é obrigatório?

Não, mas é uma das principais formas de visualização operacional e facilita a compreensão territorial.

A interface é para usuário não técnico?

Sim, a interface foi criada para reduzir dependência de terminal. Ainda assim, a operação do piloto deve ter acompanhamento técnico.

A autenticação está pronta para produção?

Ela está integrada ao fluxo existente do projeto, mas para produção recomenda-se evoluir para autenticação corporativa, como Active Directory, Azure AD ou solução equivalente.

17. Critérios de boa demonstração

A demonstração será bem-sucedida se o público entender:

Qual problema o sistema resolve.
Como o dado entra.
Como o dado é cruzado.
Como o resultado é apresentado.
Como o mapa apoia a decisão.
Como a GD afeta o balanço.
Como a priorização pode orientar campo.
Quais dados reais serão necessários para o piloto.
18. Encerramento sugerido

Finalizar com a seguinte proposta:

O próximo passo recomendado é selecionar uma área piloto, importar dados reais controlados e comparar os rankings gerados com histórico de perdas, inspeções e conhecimento das equipes de campo.