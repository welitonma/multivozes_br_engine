<!-- ESTRUTURA:MANAGED:START (gerado por .estrutura/scripts/link.mjs - nao editar a mao, editar docs/AGENTS.template.md no submodule e rerodar link.mjs) -->
# AGENTS.md

## O que é o `.estrutura`

É um submodule git com protocolo de coordenação `.ai/` + guarda de segurança + playbook. Use ao trabalhar com tasks/handoff entre agentes e antes de comandos destrutivos. Leitura: `.estrutura/README.md` (versão em `.estrutura/VERSION`, histórico em `.estrutura/CHANGELOG.md`). NUNCA edite nem commite dentro de `.estrutura/` — mude no repositório do estrutura e atualize o ponteiro com `git submodule update --remote .estrutura` + `node .estrutura/scripts/link.mjs`. Para saber se o projeto está desatualizado: `node .estrutura/scripts/link.mjs --check`.

Ordem de leitura para qualquer agente neste projeto: este arquivo →
`.ai/MEMORY.md` → `.ai/README.md`; se o projeto tiver `CLAUDE.md` (opcional)
ou outro arquivo de convenções — se existir, leia também; se não existir,
siga sem ele.

## Convenções de código

As convenções de código/stack deste projeto ficam neste `AGENTS.md` (fora do
bloco gerenciado) ou no arquivo que o projeto indicar, se houver — por exemplo
`CLAUDE.md`, se existir (opcional) — sem tratar nenhum deles como obrigatório
neste bloco.

## Coordenação entre agentes (protocolo `.ai/`)

Artefatos versionados em `.ai/` coordenam papéis (arquiteto, worker, revisor, QA)
e agentes que não compartilham contexto. Antes de agir numa task, leia
`.ai/README.md` e a skill do seu papel em `.estrutura/ai-protocol/skills/`. Sem
hook nativo de eventos, rode no início da sessão:
`node .estrutura/scripts/check-events.mjs --tool=<nome>`. Se ele imprimir `[estrutura] há versão nova`, avise o humano e só atualize o submodule com a autorização dele.

Trabalho com orquestrador + worktrees em paralelo: `.estrutura/ai-protocol/playbook/PLAYBOOK.md`.

## Agente e modelo padrão por papel

O padrão de cada papel (orquestrador, worker, revisor) vem do próprio estrutura
(`scripts/agents-padrao.json`); o projeto só declara `agents` no `.estrutura.config.json` para
sobrescrever um papel. Leia o valor efetivo com `node .estrutura/scripts/resolve-agent.mjs <papel>`
(`--fallback` = reserva). `enviar-brief.sh` já o usa (`PAPEL=revisor`; padrão
worker). **O padrão vale sempre**: só troque de agente ou modelo se o humano pedir;
única exceção é o `fallback`, quando o primário falha ao subir (avise o humano).

## Quem escreve o quê: orquestrador x worker

- **Orquestrador** (a sessão principal quando o projeto opera o protocolo `.ai/`, ou quando o humano lhe deu
  esse papel) **não escreve código de produto, testes nem docs de produto**: lê, decide, despacha, concilia
  e relata. Pode escrever só artefatos administrativos do protocolo: briefs, contract e estado da task,
  eventos, spec curta (PLAYBOOK §3) e commit com confirmação do humano.
- **Antes de começar um pedido que muda arquivos, pergunte-se: "isso é trabalho de worker?"** Se sim,
  abra ou atualize a task e despache com `enviar-brief.sh` (agente padrão: `resolve-agent.mjs worker`).
  Se não houver task nem como despachar, **pare e pergunte ao humano**; não execute em silêncio.
- **Pedido só de leitura** (ler, buscar, explicar, conferir): o orquestrador responde direto. Subagente
  nativo só para consulta de leitura (ver abaixo).
- **"Faça você mesmo"** dito pelo humano vale como exceção: faça e registre que foi a pedido dele.
- Esta regra vale para quem opera o protocolo. Um projeto sem tasks `.ai/` e sem orquestrador nomeado segue
  as instruções do humano diretamente, mas o padrão de agente acima continua valendo se despachar.

## Despacho, conferência e fechamento de revisores e workers

- **Nunca em segundo plano.** Revisor, worker, QA e qualquer papel que escreva
  arquivos, rode comandos ou possa pedir aprovação **não** vão em segundo plano
  nem como subagente nativo do seu CLI (o humano não vê o terminal e as aprovações
  ficam presas). Use card/terminal visível (Elyra: `elyra canvas create terminal`);
  sem como, rode em primeiro plano ou peça ao humano. Subagente nativo só para
  consulta de leitura.
- **Confira que começou.** `accepted:true` do Elyra só prova que o texto chegou ao
  terminal. Despache com `.estrutura/ai-protocol/playbook/scripts/enviar-brief.sh`
  (envia por `--text-file` e roda `conferir-card.mjs`); só vale com exit 0
  (3 = parou em permissão, 4 = ocioso, 5 = card ausente). PLAYBOOK §5.
- **Feche o card depois de coletar.** Depois de ler a entrega
  (`worker_done`/relatório), `elyra canvas close "<título>"`; nova revisão ou
  correção abre card novo. Se o filho travou, leia a tela antes de fechar.

## Tasks de documentação/pesquisa

Tasks `type: "doc" | "research"`: limite de chamadas do subagente é **pausa
retomável (`PAUSED`), nunca falha**. Decomponha em `units` (1 fonte = 1 unidade;
`.ai/tasks/TEMPLATE-DOC.json`), no máximo 2-3 unidades por despacho; o worker grava
cada unidade ao terminá-la e loga `UNIT_DONE`; 3-4 chamadas sem conteúdo útil
= unidade `failed` com `last_error`. Retomada:
`node .estrutura/ai-protocol/gates/check-manifest.mjs DOC-XXX --checkpoint`
(`BLOCKED` só após `max_resumes_without_progress` redespachos sem progresso).

## Guarda de segurança (3 camadas)

Comandos destrutivos (commit, push, `rm -rf`, `git add -A`, arquivos sensíveis)
exigem confirmação humana explícita naquele turno:

1. `.estrutura/security-guard/guard.mjs` — política central. Antes de comando
   destrutivo: `node .estrutura/security-guard/guard.mjs "<comando>"` (exit 2 =
   pedir confirmação).
2. Hook nativo (só o Claude Code, ver `.claude/settings.json`): chama o mesmo
   `guard.mjs`; se não consegue avaliar, pergunta (falha fechada).
3. Git hooks (`pre-commit`, `pre-push`): bloqueiam com `ESTRUTURA_AGENT=1` ou
   `CLAUDECODE=1`; só passam com `IA_CONFIRMA=1` dado pelo humano naquele turno
   (nunca hardcoded em script).

Regras fixas: sem merge/push/deploy/migration de produção sem aprovação humana;
revisor nunca corrige, só reporta; "parece funcionar" não é evidência (exige saída
real de comando com exit code).

## Vigia de permissões (serviço da máquina)

Um único serviço do usuário vigia os workers de todos os projetos. **Não instale, não
reinstale e não crie automação para isso**, nem após atualizar o submodule: só confira com
`bash .estrutura/ai-protocol/playbook/scripts/instalar-vigia-global.sh verificar`
(0 = ativo; 1/3 = avise o humano, que instala uma vez). PLAYBOOK §6.

## Avisos no Elyra (opcional)

Para ser avisado quando um agente parar esperando resposta: `.estrutura/docs/elyra-automacoes.md`
("Para o agente do projeto"); confira com `elyra automations list` e crie só com aprovação do humano.
<!-- ESTRUTURA:MANAGED:END -->
