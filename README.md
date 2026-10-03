# Duelo de Termos

Jogo web de adivinhação de palavras de cinco letras para duas pessoas, em tempo real.
O escopo completo, as regras dos modos e as fases estão em [PROJECT_SCOPE.md](PROJECT_SCOPE.md).

## Status

**Fase 0 e Fase 1 completas; Fases 2-4 cortadas rápido (ver nota abaixo e PROJECT_SCOPE.md).**

- `apps/api`: FastAPI com `GET /health`, CORS, e Socket.IO (`python-socketio`, montado via
  `socketio.ASGIApp` — ver "Rodando em desenvolvimento"). Em produção também serve o build do
  frontend (ver "Deploy"). Motor de regras (`app/game/rules.py`) e salas 1v1 em memória
  (`app/game/rooms.py`) com testes Pytest, incluindo 4 testes de integração que sobem o servidor
  de verdade e conectam dois clientes Socket.IO reais.
- `apps/web`: React + TypeScript + Vite + Tailwind.
  - **Modo infinito** (`/jogo`): sozinho, local, palavra aleatória a cada rodada (pool de ~90
    palavras em `features/game/words.ts`), sequência de acertos, teclado virtual+físico.
  - **1v1** (`/duelo`): cria ou entra numa sala por código de 4 letras, corrida simultânea contra
    outra pessoa em tempo real — quem acerta primeiro vence. O oponente só vê quantas tentativas
    você já usou, nunca as letras.

> **Nota sobre o corte de escopo (2026-10-03):** a pedido do usuário ("1v1 pronto rápido"), as
> Fases 2, 3 e 4 do `PROJECT_SCOPE.md` foram comprimidas numa entrega mínima e **testada de
> verdade** (dois navegadores reais via Playwright, não só simulação), mas deliberadamente sem:
> persistência (tudo cai se o processo reiniciar no meio de uma partida), os 3 modos
> (Normal/Competitivo/Hardcore — só existe um modo), timer, placar/múltiplas rodadas, revanche
> direta, e handshake explícito de "pronto" (a partida começa sozinha quando o 2º jogador entra).
> Ver as notas dentro de cada fase no `PROJECT_SCOPE.md` pra saber exatamente o que falta.

## Estrutura

```text
duelo-de-termos/
├── apps/
│   ├── api/                    # FastAPI (Python 3.12+)
│   │   ├── app/
│   │   │   ├── main.py         # create_app() + socket_app (uvicorn serve este)
│   │   │   ├── core/config.py  # Settings (pydantic-settings, prefixo API_)
│   │   │   ├── api/            # router.py, health.py
│   │   │   └── game/           # rules.py, words.py, rooms.py, schemas.py, sockets.py (1v1)
│   │   └── tests/               # unit (rules/rooms) + integração (2 clientes Socket.IO reais)
│   └── web/                    # React + TypeScript + Vite
│       └── src/
│           ├── app/            # roteamento, providers, QueryClient
│           ├── pages/          # HomePage, GamePage (infinito), DuelPage (1v1), NotFoundPage
│           ├── components/     # GameBoard, Keyboard, GameStatusBanner, OpponentProgress...
│           ├── features/game/  # evaluateGuess(), words.ts, useGameState, apresentação do tabuleiro
│           ├── features/duel/  # useDuel (hook), socket.ts (cliente Socket.IO), types.ts
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

| Variável           | App | Padrão                  | Uso                                     |
| ------------------ | --- | ----------------------- | --------------------------------------- |
| `API_CORS_ORIGINS` | api | `http://localhost:5173` | Origens permitidas, separadas por `,`   |
| `VITE_API_URL`     | web | `http://localhost:8000` | URL base da API usada pelo navegador    |

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

O essencial das Fases 2-4 está no ar e testado (ver "Status"). O que falta, em ordem razoável de
prioridade caso o usuário queira continuar depois do corte rápido:

1. Persistência mínima (SQLite) pra salas sobreviverem a um restart do servidor.
2. Revanche direta (hoje só existe "voltar pro lobby", que perde o código da sala).
3. Timer por rodada e placar (hoje é melhor-de-uma-rodada, sem cronômetro).
4. Os três modos (Normal/Competitivo/Hardcore) — hoje só existe um conjunto de regras.

Ver as notas dentro de cada fase no `PROJECT_SCOPE.md` pra detalhes exatos do que ficou de fora.
