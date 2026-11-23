
# Matriz de requisitos da UC (prévia v0.9)

Um requisito só recebe o status **Atendido** quando existe uma evidência observável de sua conclusão. Todos os demais devem ser classificados como Parcial ou Pendente.

| ID | UC | Requisito | Onde está implementado | Evidência | Status |
|---|---|---|---|---|---|
| IOT-01 | IoT | Placa com pelo menos 2 sensores realizando leituras com unidades físicas | `firmware/previa/previa.ino` | Linhas do monitor serial `[P1]` (DHT22 °C/% e LDR %) | Parcial |
| IOT-02 | IoT | Reconexão R1 + tratamento de sensores inválidos R5 | `previa.ino` (`ensureWifi`, `sample`) | Testes F1 e F3 na demonstração | Parcial |
| IOT-03 | IoT | ThingSpeak recebendo dados reais, com intervalo ≥ 15 s e resposta HTTP verificada | `previa.ino` (`sendThingSpeak`) | Feed do canal | Parcial |
| IOT-04 | IoT | Pelo menos 48 h de dados coletados com estatísticas descritivas | `/stats`, `database/queries.sql` | Exportação + resumo | Pendente |
| CLD-01 | Nuvem | API em HTTPS, com configuração por variáveis de ambiente | `infra/Dockerfile`, `backend/.env.example` | URL pública + log do CI | Pendente |
| CLD-02 | Nuvem | Dockerfile e segredos mantidos fora do código | `infra/Dockerfile`, `.gitignore` | Imagem construída no CI | Parcial |
| SEG-01 | Segurança | Modelo de ameaças STRIDE do fluxo principal | `docs/seguranca/STRIDE.md` | Documento | Atendido |
| SEG-02 | Segurança | Autenticação JWT; cada usuário acessa somente seus próprios dispositivos | `backend/app/security.py` | `test_other_users_device_is_403`, `test_no_token_is_401` | Atendido |
| SEG-03 | Segurança | Uma chave de dispositivo não pode ser usada para se passar por outro dispositivo | `device_from_key`, `ingest` | `test_key_of_one_device_cannot_write_as_another` | Atendido |
| QUA-01 | Qualidade | Plano de testes | `docs/qualidade/TEST_PLAN.md` | Documento | Atendido |
| QUA-02 | Qualidade | Testes automatizados das principais rotas no GitHub Actions | `backend/tests`, `.github/workflows/ci.yml` | Execução bem-sucedida após o envio das alterações | Parcial |
| IA-01 | IA | Problema definido e modelo de referência inicial calculado | `ia/baseline.py`, `ia/README.md` | MAE do modelo de referência com dados reais | Parcial |
| MOB-01 | UE Mobile | Protótipo navegável (Figma) | - | Link do Figma | Pendente |
| MOB-02 | UE Mobile | Aplicativo realiza autenticação e lista leituras reais | `mobile/` (PWA) | Demonstração em um celular | Parcial |
| CON-01 | Consumidor | Persona, jornada e proposta de valor fundamentadas em pesquisa (pelo menos 5 entrevistas ou 20 respostas) | `docs/ux/` | Dispensa por escrito do professor (a ser anexada) | Dispensado (confirmação anexa) |
| ENG-01 | Inglês Técnico | README e documentação da API em inglês | `README.md`, `/docs` | Arquivos | Atendido |
| ENG-02 | Inglês Técnico | Apresentação de 2 minutos em inglês | `docs/slides.md` | Ensaio | Parcial |

Todos os itens com status Parcial/Pendente devem ser incluídos em `PLANO_ACAO.md`.

> CON-01: o requisito de pesquisa foi dispensado pelo professor. A confirmação por escrito deve ser anexada em `docs/ux/` antes que esse status seja considerado válido.
