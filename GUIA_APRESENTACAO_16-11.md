# Guia da prévia (16/11) - leia isto primeiro

Este arquivo é só pra você e sua equipe. Não precisa ir pro repositório (pode ir, não tem problema).

## O que já está pronto e o que só vocês podem fazer

| Pronto no repositório | Só vocês conseguem (e a banca confere) |
|---|---|
| API com JWT, 401/403/400, idempotência, /health (21 testes passando) | Colocar a API no ar com URL pública HTTPS (passo 2 abaixo) |
| Firmware ESP32 (R1, R2, R3, R4, R5), escrito mas **nunca rodou numa placa** | Gravar na placa com o sensor e corrigir o que aparecer (pinos, bibliotecas) |
| Dashboard web + app PWA (último contato, offline, "sensor com falha") | Pesquisa com usuários: **>= 20 respostas ou 5 entrevistas**. Não dá pra inventar |
| Banco, Dockerfile, CI, STRIDE, plano de testes, README em inglês | Protótipo no Figma (3 telas: login, valores atuais, estado offline) |
| Baseline de IA (script pronto) | Rodar o baseline em dados reais (>= 48 h de coleta) |

**Sobre os números:** nada nas tabelas de `RESILIENCIA.md` (F1, F3) foi medido. Preencham com o que acontecer de verdade amanhã.
Se algo falhar na frente da banca, o que conta é vocês explicarem o porquê. Dado inventado é pior que dado ausente.

## Hoje à noite (a tag vence 15/11 às 23h59)

1. Criar o repositório no GitHub e subir esta pasta (o `.gitignore` já protege `.env` e `config.h`).
2. Rodar `git tag v0.9-previa && git push --tags` e enviar o link pelo ambiente virtual.
3. Conferir na aba **Actions** do GitHub se o CI ficou verde (é uma evidência pra apresentar).
4. **Deploy (30-40 min):**
   - render.com -> New PostgreSQL (free) -> copiar a *Internal Database URL*.
   - New Web Service -> o repositório -> Runtime **Docker**, Dockerfile path `infra/Dockerfile`.
   - Variáveis: `DATABASE_URL` = URL do Postgres, `JWT_SECRET` = texto longo aleatório.
   - Esperar subir e abrir `https://SEU-APP.onrender.com/health`. Tem que responder `{"status":"ok"...}`.
   - Plano free "dorme" depois de inatividade: abram `/health` uns 2 min antes de apresentar.
5. Abrir `https://SEU-APP.onrender.com/docs`, criar usuário (`/auth/register`) e um dispositivo (`POST /api/v1/devices`). **Anote a `api_key`: só aparece uma vez.**
6. Criar o canal no ThingSpeak (field1 temperatura, field2 umidade, field3 luz) e anotar a Write API Key.
7. Pesquisa: mandar o formulário (perguntas em `docs/ux/RESEARCH_PLAN.md`) pra turma, família, amigos. 20 respostas é viável numa noite.
8. Sem a placa, dá pra testar a nuvem inteira: `python tools/simulate.py --base https://SEU-APP.onrender.com --email ... --password ... --device-id esp32-sim-01`. Use outro `device_id` do real e **nunca na demonstração**.

## Amanhã, antes de apresentar (seu amigo traz o sensor)

1. Montar conforme `firmware/CIRCUIT.md`. Tirar foto da montagem.
2. Arduino IDE: instalar placa ESP32 e as bibliotecas (DHT sensor library, Adafruit Unified Sensor, ArduinoJson v7).
3. Copiar `config.h.example` para `config.h` e preencher (Wi-Fi do **hotspot do celular**, URL, device id, chave).
4. Gravar e abrir o monitor serial (115200). Esperado: linhas `[P1] seq=...` e `[P2] API seq=... -> http=201`.
5. Abrir o dashboard no notebook e o `/app/` no celular. Os valores têm que bater com o monitor serial.
6. **Ensaiar F1 e F3 pelo menos uma vez** (tempos e passos em `RESILIENCIA.md`). Se a primeira falhar, ainda dá tempo de ajustar.
7. Chegar até 18h30 com tudo ligado e conectado.

Se a compilação reclamar: erro de biblioteca costuma ser versão do ArduinoJson (precisa ser a 7) ou placa errada selecionada. Me mande a mensagem de erro que eu ajusto.

## Roteiro dos 15 minutos

| Min | Bloco | Quem / o que mostrar |
|---|---|---|
| 0-2 | Pitch em inglês | Texto em `docs/slides.md` (leiam em voz alta 3 vezes antes) |
| 2-8 | Rastreabilidade | Valor atual no dashboard e no app -> banca aquece/ilumina/aproxima -> monitor serial `[P1]` -> `[P2]` ThingSpeak e API -> consulta SQL (`database/queries.sql`, 1ª) -> dashboard e app -> indicadores (/stats). Depois: chamada sem token = 401, token de outro usuário = 403, valor absurdo = 400 (use `/docs`) |
| 8-11 | Falhas | F1: desligar hotspot 60 s. F3: soltar o fio de dados do DHT22 |
| 11-15 | Evidências + arguição | CI verde e cobertura, STRIDE (maior risco), baseline de IA, pesquisa. Tudo que não estiver pronto: dizer "pendente, está no plano de ação" |

## Perguntas que podem cair (todos precisam saber responder)

- **Wi-Fi caiu 2 minutos, o que acontece?** `ensureWifi()` tenta reconectar com espera crescente (1 s até 30 s). A cada 20 s o sensor continua lendo e cada leitura entra num buffer na RAM. Quando a rede volta, `flushBuffer()` reenvia na ordem e só remove a leitura do buffer depois que a API responde 200/201.
- **Como sabe se uma mensagem foi perdida ou duplicada?** Cada leitura tem `device_id` + `seq`. Lacuna no `seq` = perdida (query de lacunas). O banco tem `UNIQUE(device_id, seq)`: duplicada vira 1 linha só e a API responde `duplicate`.
- **E se o sensor soltar?** Leitura NaN ou fora da faixa vai como `null`, o banco guarda `valid = false`, o dashboard e o app mostram "Sensor fault". Nunca entra como valor válido.
- **O que impede alguém de mandar leituras falsas?** A chave do dispositivo (`X-Device-Key`, guardada como hash). Uma chave só escreve no seu próprio device_id (senão 403). Limitação honesta: a placa ainda não valida o certificado TLS (está no STRIDE).
- **Maior ameaça do STRIDE?** Adulteração em trânsito (placa sem validar certificado). Mitigação: configurar `API_ROOT_CA`.
- **Cobertura atual?** 95% no backend, 21 testes. Parte crítica não coberta: o firmware (testado só manualmente).
- **Por que treino/teste temporal?** Porque embaralhar deixa o modelo "ver o futuro" e infla a métrica.
- **O que o app mostra sem internet?** Os últimos valores recebidos, marcados como "não são atuais", e "App offline".
- **Em inglês:** *"What happens when the reading crosses the alert threshold?"* (alertas por limiar entram na entrega final.) / *"Hardest trade-off?"* Boa resposta: buffer em RAM é simples mas perde dados se faltar energia; cartão SD resolveria, com mais complexidade.

## Limitações honestas (digam antes que a banca descubra)

Buffer só em RAM (perde se faltar energia) · placa sem validação de certificado · sem limite de requisições · sem backup do banco · IA só com baseline · app sem push · sem pesquisa concluída (se não der tempo).
