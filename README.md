# Duelo de Termos

Jogo web de adivinhação de palavras de cinco letras para duas pessoas, em tempo real.
O escopo completo, as regras dos modos e as fases estão em [PROJECT_SCOPE.md](PROJECT_SCOPE.md).

## Status

**Fases 0-4 completas** (com cortes de escopo pontuais, documentados — ver nota abaixo e as
notas dentro de cada fase no `PROJECT_SCOPE.md`).

- `apps/api`: FastAPI com `GET /health`, CORS, e Socket.IO (`python-socketio`, montado via
  `socketio.ASGIApp` — ver "Rodando em desenvolvimento"). Em produção também serve o build do
  frontend (ver "Deploy"). `app/game/`: `rules.py` (motor de regras), `modes.py` (pontuação dos
  3 modos), `rooms.py` (salas em memória, por modo), `sockets.py` (eventos + timers),
  `persistence.py` (histórico em SQLite). `GET /partidas` lista o histórico.
- `apps/web`: React + TypeScript + Vite + Tailwind.
  - **Modo infinito** (`/jogo`): sozinho, local, palavra aleatória a cada rodada (pool de ~90
    palavras em `features/game/words.ts`), sequência de acertos, teclado virtual+físico.
  - **1v1** (`/duelo`): cria ou entra numa sala por código de 4 letras, escolhendo um dos 4 modos:
    - **Competitivo** — 6 tentativas cada, sem timer; pontos = `7 - tentativas` (quem acerta
      acertou continua podendo pontuar enquanto o oponente ainda joga).
    - **Hardcore** — 90s no relógio; o primeiro acerto válido encerra a partida na hora pra todo
      mundo (3 pontos pro vencedor, 0 pro resto; ninguém pontua se o tempo acabar sem acerto).
    - **Normal** — 90s + prorrogação (tentativas extras ilimitadas enquanto o tempo não acaba) +
      exatamente 1 tentativa final pra quem não acertou quando o tempo esgota; pontuação por
      faixa de tentativa (seção 9.1 do `PROJECT_SCOPE.md`), com bônus pra quem acerta primeiro.
    - **Infinito** (fora dos 3 modos da seção 9, pedido à parte — ver seção 9.4) — mesma
      pontuação do Competitivo por rodada, mas a sala nunca finaliza sozinha: ao concluir, sorteia
      outra palavra e soma ao placar acumulado da sessão. Só termina quando alguém sai.
  - Em todos: o oponente só vê a contagem de tentativas, nunca as letras.
  - **Reconexão de sessão** (seção 14 do `PROJECT_SCOPE.md`): um refresh de página ou queda de
    conexão no meio de uma partida não perde a rodada. O cliente guarda um token por jogador no
    `localStorage` e tenta reconectar sozinho ao montar a página; o servidor dá até 30s de janela
    (`app/game/sockets.py`, `TIMER_RECONEXAO_SEGUNDOS`) antes de tratar como abandono definitivo.
  - **Revanche direta** (seção 9.5, fora do escopo original): depois que uma partida termina,
    qualquer um pode pedir pra jogar de novo com o mesmo oponente — quando os dois pedem, a mesma
    sala reinicia (código, jogadores e modo iguais, placar zerado).
  - **Cursor clicável** (pedido à parte): clicar num quadrado da linha em digitação move o cursor
    pra lá — a próxima letra sobrescreve aquela posição em vez de só acrescentar no final. Mesma
    lógica pros dois modos (`features/game/guessCursor.ts`).
  - **Dicionário de validação** (pedido à parte): todo palpite só é aceito se existir — ~18 mil
    palavras de 5 letras geradas do dicionário hunspell `pt_BR` (pacote AUR `hunspell-pt-br`,
    expandido com `unmunch`, sem acento, filtrado pra 5 letras). Palpite que não existe mostra
    "Essa palavra não existe." e NÃO consome a tentativa — nos dois modos (solo valida local,
    1v1 valida no servidor). Arquivo duplicado em `apps/api/app/game/data/` e
    `apps/web/src/features/game/data/` (mesma dívida técnica consciente do pool de respostas).
- Rate limit no `enviar_palpite` (0.3s) e no `criar_sala` (2s) — `app/game/rate_limit.py`.
- **Testado de verdade**, não só por inspeção: 88 testes Pytest (unit + 17 de integração com 2
  clientes Socket.IO reais, incluindo timers reais de 1s via monkeypatch — não mocka o
  `asyncio.sleep`, cobrindo inclusive desconexão/reconexão de verdade com 2 conexões Socket.IO
  diferentes) + 40 testes Vitest + verificação manual com 2 navegadores reais (Playwright)
  cobrindo os 4 modos, persistência via `GET /partidas`, reconexão depois de um reload de página
  de verdade, o fluxo completo de revanche (pedido → aviso ao oponente → aceite → rodada nova), o
  cursor clicável sobrescrevendo uma posição específica, e a rejeição de palavra inexistente sem
  consumir tentativa.

> **Nota sobre cortes de escopo (2026-10-03):** ficou de fora (ver `PROJECT_SCOPE.md`, Fase 5):
> expiração de salas abandonadas (ficam em memória indefinidamente), logs estruturados, handshake
> explícito de "pronto" (a partida começa sozinha quando o 2º jogador entra), e uma suíte
> Playwright commitada (foi usado ad hoc durante o desenvolvimento, não ficou como teste
> permanente no repo). Sessões do modo Infinito ainda não entram no histórico de `GET /partidas`
> (ver seção 9.4) — só terminam por desconexão, e desconexão hoje não persiste nada.

## Estrutura

```text
duelo-de-termos/
├── apps/
│   ├── api/                    # FastAPI (Python 3.12+)
│   │   ├── alembic/             # migrações (tabela `partida`)
│   │   ├── dados/                # duelo.db (SQLite local, nunca vai pro git)
│   │   ├── app/
│   │   │   ├── main.py         # create_app() + socket_app (uvicorn serve este)
│   │   │   ├── core/            # config.py (Settings), db.py (engine/session SQLAlchemy)
│   │   │   ├── api/            # router.py, health.py, partidas.py (histórico, GET /partidas)
│   │   │   └── game/           # rules.py, modes.py, words.py, rooms.py, schemas.py, sockets.py,
│   │   │                        # persistence.py
│   │   └── tests/               # unit (rules/modes/rooms) + integração (2 clientes Socket.IO
│   │                             # reais, com timers reais) + persistência + REST
│   └── web/                    # React + TypeScript + Vite
│       └── src/
│           ├── app/            # roteamento, providers, QueryClient
│           ├── pages/          # HomePage, GamePage (infinito), DuelPage (1v1), NotFoundPage
│           ├── components/     # GameBoard, Keyboard, GameStatusBanner, OpponentProgress...
│           ├── features/game/  # evaluateGuess(), words.ts, useGameState, apresentação do tabuleiro
│           ├── features/duel/  # useDuel, useCountdown, socket.ts (cliente Socket.IO), types.ts
│           ├── services/       # cliente HTTP (api.ts)
│           ├── hooks/          # useApiHealth
│           ├── types/          # tipos do jogo
│           └── styles/         # Tailwind + tokens de tema (CSS variables)
├── .env.example
├── PROJECT_SCOPE.md
└── README.md
```

## Pré-requisitos (Arch Linux)

```bash
sudo pacman -S --needed git nodejs npm python
```

Testado com Node 26, npm 12 e Python 3.14. O backend exige Python 3.12 ou superior.

## Instalação

Na raiz do projeto:

```bash
cp .env.example .env

# Backend
cd apps/api
python -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/alembic upgrade head   # cria apps/api/dados/duelo.db
cd ../..

# Frontend
cd apps/web
npm install
cd ../..
```

## Executar em desenvolvimento

Use dois terminais.

```bash
# Terminal 1: API + Socket.IO em http://localhost:8000 (docs em /docs)
cd apps/api
.venv/bin/uvicorn app.main:socket_app --reload --port 8000
```

```bash
# Terminal 2: web em http://localhost:5173
cd apps/web
npm run dev
```

Verificação rápida: `curl http://localhost:8000/health` deve responder `{"status":"ok"}`, e a
home deve mostrar "Servidor online".

## Qualidade

```bash
# Backend (em apps/api)
.venv/bin/pytest              # testes
.venv/bin/ruff check .        # lint
.venv/bin/ruff format .       # formatação
.venv/bin/mypy app tests      # tipagem estrita

# Frontend (em apps/web)
npm test                      # Vitest + Testing Library
npm run typecheck             # tsc estrito
npm run lint                  # ESLint (typescript-eslint strict, type-checked)
npm run format                # Prettier
npm run build                 # build de produção em dist/
```

## Variáveis de ambiente

Há um único `.env` na raiz, lido pelos dois apps:

| Variável           | App | Padrão                                       | Uso                                    |
| ------------------ | --- | --------------------------------------------- | --------------------------------------- |
| `API_CORS_ORIGINS` | api | `http://localhost:5173`                       | Origens da API REST, separadas por `,` (o Socket.IO usa `"*"` — ver "Decisões técnicas") |
| `API_DATABASE_URL` | api | `sqlite+aiosqlite:///apps/api/dados/duelo.db` | Banco do histórico de partidas         |
| `VITE_API_URL`     | web | `http://localhost:8000`                       | URL base da API usada pelo navegador   |

Tudo o que começa com `VITE_` vai para o bundle do navegador. Nunca coloque segredos nessas
variáveis.

## Decisões técnicas

- **Monorepo sem workspaces.** `apps/api` e `apps/web` têm dependências independentes (venv e
  `node_modules`). Um orquestrador só entra se surgir necessidade real.
- **Backend como autoridade (a partir da Fase 2).** Na Fase 1, sem rede, `evaluateGuess()` roda
  no cliente contra uma palavra fixa temporária (`TERMO`, em `useGameState.ts`) só pra validar a
  mecânica. A partir da Fase 2 o servidor passa a decidir a palavra e avaliar os palpites; o
  frontend volta a só exibir os estados (`correct`, `present`, `absent`) recebidos por rede.
- **Acessibilidade das letras.** Cada célula tem `aria-label` com letra e estado. O estado
  `present` também tem uma borda tracejada interna, para não depender só da cor.
- **Tema.** As cores ficam como CSS variables em `styles/index.css` e são expostas ao Tailwind
  via `@theme`. O modo claro/escuro segue `prefers-color-scheme`.
- **TypeScript estrito.** Ativados `strict`, `noUncheckedIndexedAccess`,
  `exactOptionalPropertyTypes` e lint type-checked. `any` é proibido pelo ESLint.
- **Python tipado.** `mypy --strict` com o plugin do Pydantic. Os testes usam o `TestClient` do
  FastAPI com `httpx2`, que o Starlette atual recomenda no lugar do `httpx`.
- **React Router 8 + TanStack Query.** O Query já está configurado (hoje só consulta
  `/health`) para servir de base às leituras HTTP das próximas fases.
- **Socket.IO, não WebSocket puro.** Escolha já estava no `PROJECT_SCOPE.md` (salas prontas,
  fallback automático pra polling). `python-socketio` não tem stubs de tipo — ver
  `[[tool.mypy.overrides]]` pro módulo em `pyproject.toml`, e `# type: ignore[untyped-decorator]`
  nos handlers de `app/game/sockets.py` (o erro aparece na linha do `@sio.event`, não na da
  função — se mover o ignore pra linha errada, o mypy acusa "unused ignore").
- **CORS do Socket.IO é `"*"`, não a lista de origens da API.** Achado testando com navegador de
  verdade (Playwright): em produção front+API dividem a origem (`127.0.0.1:3500`), mas o handshake
  do WebSocket ainda manda `Origin`, e isso não batia com `API_CORS_ORIGINS` (pensado pro Vite dev
  em `:5173`). Sem cookies/sessão no handshake (identidade = nome + código de sala), `"*"` aqui não
  abre superfície de ataque nova — mas é o tipo de bug que só aparece testando num browser real,
  não só com cliente Python ou Testing Library.
- **Salas do 1v1 em memória, não banco.** Dict Python num singleton (`app/game/rooms.py`); morre
  se o servidor reiniciar no meio de uma partida. Decisão consciente pelo prazo, não esquecimento.
- **Código de sala com `secrets`, não `random`.** É o único controle de acesso à sala — precisa
  ser imprevisível.
- **React 19 deprecou `FormEvent`/`FormEventHandler` genéricos.** Use `SubmitEvent<T>` (de
  `'react'`) pra `onSubmit`; `FormEvent` ainda existe mas o lint (`@typescript-eslint/no-deprecated`)
  acusa.
- **`react-hooks/refs` proíbe mutar `ref.current` durante a renderização** (mesmo fora de JSX,
  tipo `meuRef.current = valor` solto no corpo do componente/hook). Precisa estar dentro de
  `useEffect` — ver `useDuel.ts`.
- **`react-hooks/purity` proíbe chamar função impura (`Date.now()`, etc.) durante a renderização**,
  e `react-hooks/set-state-in-effect` proíbe `setState` síncrono no corpo do efeito (só dentro de
  callback de evento/timer). Resultado: `useCountdown.ts` guarda o "tempo restante" inteiro em
  estado, atualizado só de dentro do callback do `setInterval` — o valor pode ficar vazio por até
  250ms no início de cada partida (até o primeiro tick), compromisso consciente.
- **Pontuação e fim de partida são por modo** (`app/game/modes.py` tem as fórmulas puras;
  `app/game/rooms.py` decide quando aceitar um palpite e quando a sala termina, por modo):
  Competitivo deixa o oponente continuar jogando depois que alguém acerta (quem importa é o placar
  no fim); Hardcore encerra tudo no primeiro acerto; Normal libera prorrogação e depois exatamente
  1 tentativa final por jogador quando o tempo acaba.
- **Timer de verdade no servidor, não só no cliente.** `asyncio.create_task` por sala
  (`app/game/sockets.py`), nunca o relógio do navegador — o cliente só roda uma contagem regressiva
  aproximada (`useCountdown`) pra UX; quem decide é sempre o evento `tempo_esgotado` do servidor.
  Achado só com teste de timer real (não com os testes unitários da Fase 2): `_finalizar_e_notificar`
  cancelava a própria task quando chamada de dentro do timer que acabou de disparar — corrigido com
  uma guarda contra auto-cancelamento (`task is not asyncio.current_task()`).
- **Histórico de partidas em SQLite, não o estado ao vivo.** `app/game/persistence.py` grava um
  registro só quando a sala termina (resultado, não cada palpite) — o estado em andamento continua
  em memória (ver ponto acima sobre salas). `python-socketio` sem stubs de tipo já forçava um
  `[[tool.mypy.overrides]]`; `greenlet` é dependência transitiva obrigatória do
  `sqlalchemy[asyncio]` (sem ela, erro só aparece ao importar `sqlalchemy.ext.asyncio`, não na
  instalação).
- **Dicionário de palpites gerado uma vez, versionado — não regenerado em runtime.**
  `apps/api/app/game/data/palavras_validas.txt` (e a cópia em `apps/web/.../data/`) vieram de
  `unmunch pt_BR.dic pt_BR.aff` (pacote AUR `hunspell-pt-br`) expandindo todas as conjugações,
  removendo acento e filtrando pra 5 letras (10M+ formas → 18212 palavras únicas). O repo não
  depende de `hunspell` instalado pra RODAR — só pra regenerar o arquivo, se um dia precisar de
  mais cobertura. Cursor clicável (`guessCursor.ts`) guarda o palpite em digitação como array de
  posições fixas (não string), porque o cursor pode pular pra qualquer quadrado e abrir buracos
  no meio da palavra.

## Deploy

No ar em `https://duelo-de-termos.tail9ff58.ts.net` (Tailscale Funnel), seguindo o mesmo padrão
dos outros projetos pessoais (`ayo-std`, `ayo-sketchbook`): um container Tailscale próprio
(`deploy/tailscale/`, chave e estado locais, nunca versionados) expõe a porta 3500, onde roda o
serviço systemd de usuário `deploy/duelo-de-termos.service` (`uvicorn app.main:socket_app --port
3500`, com `linger` habilitado — sobrevive a reboot/logout).

Em produção a própria API serve o frontend: `apps/api/app/main.py` monta `apps/web/dist/` como
estático (com fallback pra `index.html` em qualquer rota, pra o React Router funcionar) quando
essa pasta existe. `.env.production` (versionado, sem segredo) zera `VITE_API_URL` no build pra
ficar relativo, já que front e API dividem a mesma origem.

Pra atualizar o jogo no ar depois de mudar código:

```bash
cd apps/web && npm run build
systemctl --user restart duelo-de-termos.service
```

O container Tailscale não precisa ser tocado de novo — ele só aponta pra porta 3500.

## Próximo passo

Fases 0-4 completas (3 modos, timers reais, histórico persistido — ver "Status"). O que falta,
em ordem razoável de prioridade (tudo listado como Fase 5 no `PROJECT_SCOPE.md`):

1. Reconexão de sessão — hoje um crash/refresh no meio de uma partida perde aquela rodada.
2. Revanche direta (hoje só existe "voltar pro lobby", que perde o código da sala).
3. Suíte Playwright commitada no repo (foi usado ad hoc durante o desenvolvimento, não ficou).
4. Rate limiting nos eventos Socket.IO.

Ver as notas dentro de cada fase no `PROJECT_SCOPE.md` pra detalhes exatos do que ficou de fora.
