# Riscos e Próximas Fases - Area 51

## 1. Objetivo

Este documento registra os principais riscos conhecidos do projeto Area 51 e propõe as próximas fases após o encerramento do ciclo de MVP/piloto.

O objetivo é deixar claro o que já está maduro, o que ainda depende de dados reais e quais evoluções são necessárias para transformar o MVP em uma solução operacional mais próxima de produção.

## 2. Estado atual

O projeto já possui:

- APIs operacionais.
- Interface web.
- Login integrado ao fluxo de autenticação existente.
- Experiência de sessão local.
- Busca por matrícula, transformador, alimentador, subestação e coordenadas.
- Upload de imagem aérea.
- Mapa operacional.
- Importadores de dados.
- Camada territorial.
- Integração com IBGE e CRAS.
- Contrato para dados de geração distribuída.
- Cálculo de perda ajustada.
- Testes automatizados.
- Documentação de prontidão para piloto.

## 3. Riscos técnicos

### 3.1 Qualidade dos dados reais

Risco:

Dados reais podem chegar incompletos, duplicados, desatualizados ou com vínculos inconsistentes entre cliente, transformador, alimentador e subestação.

Impacto:

- Busca operacional imprecisa.
- Ranking de perdas distorcido.
- Mapa com pontos incorretos.
- Priorização frágil.

Mitigação:

- Criar validação automática de qualidade dos dados.
- Exigir dicionário de campos.
- Validar amostra com equipe de negócio.
- Comparar resultados com conhecimento de campo.
- Criar relatórios de inconsistências antes da análise.

### 3.2 Associação cliente-transformador

Risco:

Nem todos os clientes podem estar corretamente associados ao transformador real.

Impacto:

- Erro no balanço energético.
- Perda atribuída ao ativo errado.
- Distorção na análise por bolsão.

Mitigação:

- Solicitar base oficial de vínculo cliente-transformador.
- Validar com cadastro técnico.
- Usar coordenadas como camada auxiliar.
- Criar rotina para identificar clientes sem vínculo ou com vínculo suspeito.

### 3.3 Coordenadas imprecisas

Risco:

Coordenadas de clientes, transformadores ou áreas podem estar ausentes ou deslocadas.

Impacto:

- Mapa incorreto.
- Busca por coordenada inconsistente.
- Cruzamento territorial impreciso.

Mitigação:

- Validar latitude e longitude.
- Remover coordenadas inválidas.
- Criar regra de tolerância espacial.
- Comparar coordenadas com área operacional conhecida.

### 3.4 Dados de GD incompletos

Risco:

Dados de geração distribuída podem não ter energia gerada, consumida, injetada ou compensada com a mesma granularidade das perdas.

Impacto:

- Perda ajustada menos confiável.
- Falso positivo de perda.
- Dificuldade para separar fraude de efeito de geração.

Mitigação:

- Definir contrato mínimo de dados de GD.
- Padronizar mês de referência.
- Garantir vínculo com cliente, transformador ou alimentador.
- Registrar quando o ajuste de GD não puder ser aplicado.

### 3.5 Análise por imagem aérea

Risco:

Imagens podem ter baixa resolução, ângulo ruim, data desatualizada ou cobertura incompleta da área.

Impacto:

- Estimativa de telhados imprecisa.
- Baixa confiança na análise visual.
- Resultado pouco útil para validação de campo.

Mitigação:

- Definir padrão mínimo de imagem.
- Exibir score de confiança.
- Permitir revisão humana.
- Usar imagem apenas como apoio, não como decisão final.

### 3.6 Interpretação de perda como fraude

Risco:

Perda elétrica pode ter múltiplas causas e não deve ser automaticamente classificada como fraude.

Impacto:

- Priorização inadequada.
- Risco operacional e reputacional.
- Decisões sem validação de campo.

Mitigação:

- Tratar o sistema como apoio à decisão.
- Usar linguagem de risco, anomalia ou prioridade.
- Confirmar suspeitas com inspeção.
- Cruzar com histórico de campo e medição.

## 4. Riscos de segurança

### 4.1 Autenticação local

Risco:

A autenticação atual é adequada para MVP/piloto, mas ainda não representa um modelo corporativo final.

Impacto:

- Controle limitado de usuários.
- Gestão de senha menos integrada.
- Necessidade de governança adicional em produção.

Mitigação:

- Evoluir para Active Directory, Azure AD ou solução corporativa equivalente.
- Implementar perfis e permissões por papel.
- Implementar expiração e renovação segura de sessão.
- Registrar auditoria de acesso.

### 4.2 Dados sensíveis

Risco:

Bases da concessionária podem conter dados pessoais ou operacionais sensíveis.

Impacto:

- Exposição indevida.
- Não conformidade com políticas internas.
- Risco legal e reputacional.

Mitigação:

- Minimizar dados pessoais.
- Evitar CPF, telefone e endereço completo sempre que possível.
- Usar identificadores técnicos.
- Restringir acesso.
- Documentar finalidade de uso.
- Tratar dados conforme LGPD e política interna.

### 4.3 Ambiente local

Risco:

Rodar o piloto em ambiente local pode não ter os mesmos controles de produção.

Impacto:

- Dependência da máquina do operador.
- Risco de arquivos locais sensíveis.
- Dificuldade de auditoria.

Mitigação:

- Usar ambiente controlado.
- Definir responsáveis pelo ambiente.
- Limpar artefatos após testes.
- Evoluir para deploy em servidor homologado.

## 5. Riscos operacionais

### 5.1 Adoção pelo usuário

Risco:

Usuários não técnicos podem ter dificuldade se a interface ainda exigir interpretação técnica.

Impacto:

- Baixa adesão.
- Necessidade de suporte constante.
- Uso incorreto dos resultados.

Mitigação:

- Melhorar mensagens da interface.
- Criar roteiro de uso.
- Criar treinamento curto.
- Reduzir exposição de JSON técnico para usuários finais.
- Criar dashboards executivos.

### 5.2 Expectativa excessiva

Risco:

O projeto pode ser interpretado como solução definitiva de detecção de fraude.

Impacto:

- Frustração com limitações do MVP.
- Uso indevido dos resultados.
- Pressão por decisões automáticas.

Mitigação:

- Comunicar que é uma ferramenta de apoio.
- Explicar limitações.
- Validar com dados reais.
- Criar métricas de acurácia, precisão e falso positivo.

### 5.3 Dependência de dados externos

Risco:

IBGE, CRAS, imagens e bases de GD podem depender de disponibilidade externa.

Impacto:

- Análises incompletas.
- Atraso no piloto.
- Necessidade de ajustes manuais.

Mitigação:

- Definir dados mínimos obrigatórios.
- Permitir execução parcial.
- Registrar ausência de dados no resultado.
- Criar rotina de atualização.

## 6. Limitações conhecidas

- A interface ainda é um piloto operacional, não um produto final.
- A autenticação ainda deve evoluir para padrão corporativo.
- A proteção total de rotas no backend ainda pode ser aprimorada.
- O mapa depende da geração prévia do arquivo HTML.
- A análise de imagem ainda depende da qualidade do arquivo enviado.
- A classificação de risco depende diretamente da qualidade dos dados importados.
- Dados simulados não substituem validação com dados reais.
- A decisão final de campo depende de análise humana.

## 7. Próximas fases recomendadas

### Fase 39 - Execução guiada fim a fim

Objetivo:

Criar uma tela ou fluxo único para executar uma análise completa a partir de uma matrícula, transformador, alimentador, subestação ou coordenada.

Entregas:

- Botão `Executar análise completa`.
- Consolidação de perdas, GD, território, IBGE, CRAS e mapa.
- Resultado final em cards.
- Exportação de evidência operacional.

### Fase 40 - Relatório executivo

Objetivo:

Gerar relatório consolidado para gestores e áreas técnicas.

Entregas:

- Relatório PDF ou HTML.
- Sumário executivo.
- Ranking de prioridade.
- Tabela de ativos críticos.
- Observações de GD.
- Indicadores socioenergéticos.
- Evidências e limitações.

### Fase 41 - Autenticação corporativa

Objetivo:

Substituir ou complementar a autenticação local por integração corporativa.

Entregas:

- Integração com Active Directory ou Azure AD.
- Perfis de acesso.
- Política de expiração.
- Auditoria de login.
- Controle por grupo ou área.

### Fase 42 - Banco corporativo e ETL

Objetivo:

Integrar dados reais por banco, API ou rotina ETL.

Entregas:

- Conectores para bases reais.
- Validação de qualidade.
- Dicionário de dados.
- Agendamento de atualização.
- Logs de importação.

### Fase 43 - Observabilidade

Objetivo:

Melhorar monitoramento e rastreabilidade.

Entregas:

- Logs estruturados.
- Métricas de API.
- Métricas de inferência.
- Monitoramento de jobs.
- Preparação para Prometheus e Grafana.
- Tracing, se necessário.

### Fase 44 - Mapa interativo avançado

Objetivo:

Evoluir o mapa operacional para uma experiência mais rica.

Entregas:

- Filtros por mês.
- Filtros por alimentador.
- Filtros por subestação.
- Camadas de IBGE e CRAS.
- Camada de GD.
- Heatmap dinâmico.
- Seleção de transformador no mapa.

### Fase 45 - Validação de campo

Objetivo:

Comparar recomendações do sistema com inspeções reais.

Entregas:

- Lista de áreas priorizadas.
- Registro de inspeções.
- Resultado confirmado ou não confirmado.
- Medição de precisão.
- Medição de falso positivo.
- Ajuste de pesos do modelo.

## 8. Métricas recomendadas para o piloto

Durante o piloto, acompanhar:

- Quantidade de transformadores analisados.
- Quantidade de clientes analisados.
- Percentual de clientes com vínculo elétrico completo.
- Percentual de transformadores com coordenadas válidas.
- Percentual de áreas com dados de GD.
- Percentual de áreas com dados IBGE/CRAS.
- Quantidade de áreas priorizadas.
- Quantidade de inconsistências de dados.
- Tempo médio para gerar análise.
- Tempo médio para abrir mapa.
- Aderência com percepção da equipe de campo.
- Falso positivo observado.
- Falso negativo observado, se houver validação.

## 9. Decisão recomendada após o piloto

Após executar o piloto com dados reais, recomenda-se decidir entre:

### 9.1 Evoluir para homologação

Quando:

- Dados forem consistentes.
- Resultados forem compreensíveis.
- Equipe reconhecer valor operacional.
- Indicadores forem coerentes com campo.

### 9.2 Reforçar dados antes de evoluir

Quando:

- Faltarem vínculos críticos.
- Coordenadas estiverem ruins.
- Dados de GD não forem confiáveis.
- Perdas não tiverem granularidade suficiente.

### 9.3 Reduzir escopo

Quando:

- A área piloto for complexa demais.
- A base real estiver incompleta.
- O objetivo inicial estiver amplo demais.

## 10. Conclusão

O Area 51 está tecnicamente preparado para um piloto controlado.

A prioridade agora é validar o sistema com dados reais, medir a aderência dos resultados ao conhecimento operacional e documentar limitações.

O projeto não deve ser tratado como solução final de produção antes de:

- Integrar dados reais.
- Validar qualidade das bases.
- Confirmar resultados com campo.
- Evoluir autenticação corporativa.
- Definir governança de uso.
- Estabelecer rotina de atualização.