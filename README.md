# Duelo de Termos

Jogo web de adivinhação de palavras de cinco letras para duas pessoas, em tempo real.
O escopo completo, as regras dos modos e as fases estão em [PROJECT_SCOPE.md](PROJECT_SCOPE.md).

## Status

**Fase 0 e Fase 1 concluídas.**

- `apps/api`: FastAPI com `GET /health` → `{"status":"ok"}`, configuração por `.env` e CORS. Em
  produção também serve o build do frontend (ver "Deploy" abaixo).
- `apps/web`: React + TypeScript + Vite + Tailwind. Dá pra jogar uma rodada completa, sozinho e
  localmente, em `/jogo`: teclado virtual + físico, `evaluateGuess()` puro com tratamento de
  letras repetidas, cores no tabuleiro e no teclado, mensagens de erro amigáveis (palpite
  incompleto) e tela de vitória/derrota com "Jogar de novo".

Ainda **não** existem: Socket.IO, banco, salas, identidade, timer e motor de regras no backend —
a palavra secreta é fixa e a avaliação roda no cliente só até a Fase 2 trocar isso pelo servidor
(ver `PROJECT_SCOPE.md`).

## Estrutura

```text
duelo-de-termos/
├── apps/
│   ├── api/                    # FastAPI (Python 3.12+)
│   │   ├── app/
│   │   │   ├── main.py         # create_app(): CORS + rotas
│   │   │   ├── core/config.py  # Settings (pydantic-settings, prefixo API_)
│   │   │   └── api/            # router.py, health.py
│   │   └── tests/
│   └── web/                    # React + TypeScript + Vite
│       └── src/
│           ├── app/            # roteamento, providers, QueryClient
│           ├── pages/          # HomePage, GamePage, NotFoundPage
│           ├── components/     # GameBoard, GuessRow, LetterTile, TileLegend, ServerStatus
│           ├── features/game/  # evaluateGuess() puro, estado do jogo, apresentação do tabuleiro
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
# Terminal 1: API em http://localhost:8000 (docs em /docs)
cd apps/api
.venv/bin/uvicorn app.main:app --reload --port 8000
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

## Deploy

No ar em `https://duelo-de-termos.tail9ff58.ts.net` (Tailscale Funnel), seguindo o mesmo padrão
dos outros projetos pessoais (`ayo-std`, `ayo-sketchbook`): um container Tailscale próprio
(`deploy/tailscale/`, chave e estado locais, nunca versionados) expõe a porta 3500, onde roda o
serviço systemd de usuário `deploy/duelo-de-termos.service` (`uvicorn app.main:app --port 3500`,
com `linger` habilitado — sobrevive a reboot/logout).

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

Fase 2: motor de regras no backend (domínio oficial do jogo, ainda sem Socket.IO) — ver
`PROJECT_SCOPE.md`.
