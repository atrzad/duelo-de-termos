# Duelo de Termos

Jogo web de adivinhação de palavras de cinco letras para duas pessoas, em tempo real.
O escopo completo, as regras dos modos e as fases estão em [PROJECT_SCOPE.md](PROJECT_SCOPE.md).

## Status

**Fase 0 concluída + base da Fase 1.**

- `apps/api`: FastAPI com `GET /health` → `{"status":"ok"}`, configuração por `.env` e CORS.
- `apps/web`: React + TypeScript + Vite + Tailwind, com tela inicial e tabuleiro 6×5 estático
  (`/jogo`) mais um indicador do status da API.

Ainda **não** existem: Socket.IO, banco, salas, identidade, timer, teclado virtual e regras de
avaliação de palpites.

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
│           ├── features/game/  # helpers de apresentação do tabuleiro
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
- **Backend como autoridade.** O frontend só exibe estados (`correct`, `present`, `absent`)
  recebidos do servidor. As linhas coloridas em `/jogo` são dados fixos de demonstração, sem
  avaliação no cliente.
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

## Próximo passo

Concluir a Fase 1: teclado virtual e físico, palavra temporária fixa, `evaluateGuess()` puro
com testes de letras repetidas e tela de vitória/derrota local.
