
# Plano de ação (atualizado em 23/11/2026)

Uma linha para cada lacuna: todos os itens com status *Parcial* / *Pendente* de `REQUISITOS_UC.md`, os testes de resiliência ainda em aberto e os objetivos finais de cada seção.

Os responsáveis são uma primeira proposta da equipe e podem ser alterados durante a aula de laboratório. Cada linha termina com uma evidência que pode ser verificada.

## Concluído desde a prévia v0.9

| Item | Evidência |
|---|---|
| Dashboard web reconstruído sobre a API: login/cadastro, indicadores em tempo real, histórico com filtro por período (40 leituras, 1 h, 6 h, 24 h), alertas de limite, status online/offline, último contato, aviso "sem dados desde HH:MM", painel de rastreabilidade da última leitura e exportação CSV | `frontend/index.html` |

## Lacunas

| Lacuna | UC / Critério | Ação concreta | Responsável | Prazo | Evidência de conclusão |
|---|---|---|---|---|---|
| API ainda não implantada, sem URL pública (CLD-01) | Nuvem / Cloud Computing | Implantar a API + PostgreSQL gerenciado no Render a partir de `infra/`; manter os segredos somente nas variáveis de ambiente do provedor | Hugo Pires | 24/11 | URL HTTPS pública; `/health` retorna `{"status":"ok","db":"ok"}` |
| Placa ainda envia dados apenas para localhost / ThingSpeak | IoT / Integração | Configurar o firmware para utilizar a URL pública da API; manter o ThingSpeak como cópia da telemetria | Alef Rafael | 24/11 | Registro serial `[P1]..[P6]` e o mesmo `seq` + `ts` visíveis no dashboard público |
| Menos de 48 h de dados reais (IOT-04) | IoT / Dados | Iniciar a coleta contínua usando a URL pública logo após a implantação; exportar a tabela, calcular estatísticas descritivas e contabilizar leituras ausentes e inválidas | Isack Otávio | 26/11 | Exportação CSV + resumo em `docs/` (também alimenta a referência inicial da IA) |
| F1 e F3 ainda não foram medidos no hardware (IOT-01/02/03) | IoT / Resiliência | Executar F1 (desligar o hotspot por 60 s) e F3 (desconectar o fio de dados do DHT22) na placa; preencher as tabelas em `RESILIENCIA.md` com números reais | Alef Rafael | 25/11 | Tabelas preenchidas + consulta de lacunas retornando 0 linhas |
| Buffer R2 existe apenas na RAM (perdido em caso de queda de energia) | IoT / Resiliência | Persistir o buffer no LittleFS e reenviar os dados em ordem pelo `seq` | Alef Rafael | 27/11 | F1 repetido após uma queda de energia; nenhuma lacuna no `seq` |
| Watchdog R4 não testado; F2 não executado | IoT / Resiliência | Testar a reinicialização pelo watchdog e executar F2 (desconectar a alimentação) | Alef Rafael | 27/11 | Novos dados no dashboard em até 60 s, sem intervenção manual (vídeo + tabela) |
| Sem TLS entre a placa e a API | Segurança / IoT | Utilizar HTTPS com o certificado CA no firmware; remover HTTP sem criptografia | Alef Rafael | 27/11 | Captura mostrando apenas tráfego TLS; firmware sem `http://` |
| Protótipo Figma ausente (MOB-01) | UE Mobile | Criar 3 telas: login, valores mais recentes e estado offline (+ tela de alerta), mantendo a mesma identidade visual do dashboard | João Victor | 24/11 | Link do Figma em `docs/ux/` |
| PWA mobile com visual antigo e sem funcionamento offline/alertas (MOB-02) | UE Mobile | Aplicar a nova identidade visual; implementar estado offline com último contato; alertas push por limite | João Victor | 28/11 | Demonstração em um celular; notificação push recebida após ultrapassar o limite |
| Evidências de usabilidade do aplicativo | UE Mobile / Consumidor | Testar com 5 usuários (tarefas + SUS); realizar avaliação heurística; registrar os problemas encontrados e o que foi alterado | João Victor | 29/11 | Relatório SUS em `docs/ux/` (meta ≥ 68) |
| Pesquisa com usuários (CON-01) | Consumidor | **Requisito dispensado pelo professor.** Anexar a confirmação por escrito e manter persona/jornada em `docs/ux/` | Zaion | 23/11 | Captura de tela da confirmação do professor em `docs/ux/` |
| CI ainda não possui evidência de execução bem-sucedida (QUA-02) | Qualidade | Corrigir e enviar as alterações até que a execução do Actions fique verde; adicionar relatório de cobertura | Pedro Lucas | 25/11 | Link da execução bem-sucedida + resultado da cobertura |
| Cobertura abaixo da meta final | Qualidade | Aumentar a cobertura do back-end para ≥ 60% (75% desejado), com testes de idempotência (F5), 400/401/403 e `/health`; análise estática sem bloqueios | Pedro Lucas | 28/11 | `pytest --cov` ≥ 60%; relatório de análise estática |
| Imagem Docker não é construída no CI (CLD-02) | Nuvem / Qualidade | Adicionar uma etapa `docker build` ao workflow; adicionar implantação automática por tag | Hugo Pires | 27/11 | Log do CI com construção + implantação |
| Apenas modelo de referência inicial (IA-01) | IA | Executar `ia/baseline.py` com dados reais; treinar um modelo com divisão temporal entre treino/teste que supere a referência inicial; disponibilizar `/predict`; mostrar o resultado no dashboard e no aplicativo; escrever o model card (documento de descrição do modelo) | Israel | 28/11 | MAE/F1 do modelo × referência inicial em `ia/README.md`; `/predict` na documentação OpenAPI; model card |
| Dashboard não apresenta o resultado da IA nem os perfis de usuário | IoT / Dashboard | Mostrar a saída de `/predict` no dashboard; adicionar funções de usuário | [seu nome] | 29/11 | Captura de tela + teste de funções de usuário no CI |
| Sem limitação de requisições; análise ZAP não executada | Segurança | Adicionar limite de requisições; executar o ZAP baseline; corrigir todos os alertas de alta gravidade; verificar as dependências | Pedro Lucas | 28/11 | Relatório ZAP sem alertas de alta gravidade |
| Documentos LGPD e OWASP ausentes | Segurança | Criar uma nota curta sobre a LGPD (dados coletados, finalidade e retenção) e uma lista de verificação OWASP para API/IoT | Zaion | 28/11 | Arquivos em `docs/seguranca/` |
| F4, F5 e F6 ainda não foram demonstrados | IoT / Nuvem / Qualidade | Parar o container da API por 30 s (F4); reenviar um dado duplicado (F5); bloquear/invalidar o ThingSpeak (F6); automatizar F5 como teste | Hugo Pires | 28/11 | Tabela em `RESILIENCIA.md`; teste F5 no CI |
| R7/R8: logs não centralizados; backup não testado | Nuvem / Resiliência | Centralizar os logs no provedor; configurar backup gerenciado com teste de restauração documentado; estimar o custo mensal | Hugo Pires | 28/11 | Registro da restauração; tabela de custos |
| Medições finais ausentes | IoT / Qualidade | Executar por 24 h: taxa de perda (meta ≤ 1%), disponibilidade do dispositivo e tempo de recuperação em F1/F2/F4 | Isack Otávio | 29/11 | Relatório de teste em `docs/` |
| Apresentação em inglês ainda não ensaiada (ENG-02) | Inglês Técnico | Ensaiar a apresentação de 2 minutos; finalizar os slides (máximo de 6) e o vídeo de 5 minutos; realizar commits e PRs em inglês | Zaion | 29/11 | Slides + vídeo em `docs/` |
| README completo e reprodutibilidade | Inglês Técnico / Qualidade | Criar README com usuário de teste e instruções de execução/implantação por módulo; relatório ISO/IEC 25010; uma pessoa de fora deve conseguir seguir apenas o README | Zaion | 29/11 | Execução em uma máquina limpa seguindo o README |

## Regras para a equipe

- Cada item acima deve possuir um commit ou PR vinculado quando for concluído (matriz de responsabilidades).
- A tag `v1.0` deve ser criada antes da aula de 30/11; nada feito depois dessa data será contabilizado.
- Segredos reais nunca devem ser colocados no repositório; revogue e gere novamente qualquer chave que já tenha sido enviada ao repositório.
