# Duelo de Termos

## 1. Visão do projeto

**Duelo de Termos** é um jogo web competitivo de adivinhação de palavras para duas pessoas jogarem em tempo real.

O jogo é inspirado em jogos de palavras de cinco letras, mas foi pensado para disputas simultâneas entre dois jogadores. Os dois jogadores recebem a mesma palavra secreta, enviam palpites e acompanham o próprio progresso enquanto veem apenas o status resumido do adversário.

O projeto começará como um jogo privado para duas pessoas. Posteriormente, poderá ser publicado para pessoas na mesma tailnet usando Tailscale Serve e, somente após segurança e validações adequadas, poderá ser exposto publicamente com Tailscale Funnel.

O backend é a fonte oficial de verdade. O navegador não deve receber a palavra secreta antes do término da rodada e não deve decidir vencedores, pontuação ou validação oficial dos palpites.

---

## 2. Objetivos

### Objetivos do MVP

- Permitir que dois jogadores criem e entrem em uma sala privada.
- Usar código de convite para entrar em uma sala.
- Permitir que os dois jogadores joguem a mesma palavra em tempo real.
- Suportar os modos Normal, Competitivo e Hardcore.
- Sincronizar sala, presença, progresso, término de rodada e placar em tempo real.
- Impedir que um jogador veja as palavras, palpites ou cores do tabuleiro do oponente.
- Salvar partidas e pontuações.
- Funcionar bem em navegador mobile e desktop.
- Ser acessível inicialmente por uma rede privada com Tailscale.

### Objetivos futuros

- Login real com conta, senha, OAuth ou magic link.
- Perfil de jogador.
- Histórico detalhado de partidas.
- Ranking geral e ranking entre amigos.
- Sistema de amigos e convites.
- Partidas com mais de duas pessoas.
- Partidas públicas ou matchmaking.
- Modo espectador.
- Chat dentro da sala.
- Seleção de idioma.
- Dicionário maior e categorias de palavras.
- Conquistas, níveis, temporadas e estatísticas.
- Publicação pública via Tailscale Funnel ou uma hospedagem convencional.
- Aplicativo mobile nativo ou PWA instalável.

---

## 3. Fora do escopo inicial

Os itens abaixo não devem ser implementados no primeiro MVP:

- Login com senha.
- OAuth com Google, GitHub ou Discord.
- Recuperação de senha.
- E-mail transacional.
- Ranking global.
- Matchmaking aleatório.
- Chat.
- Notificações push.
- Pagamentos.
- Microserviços.
- Redis.
- Docker Swarm ou Kubernetes.
- Multiplayer com mais de dois jogadores.
- Modo espectador.
- Painel administrativo completo.
- Publicação pública via Funnel.
- IA para gerar palavras.
- Sistema complexo de anti-cheat.

O objetivo é entregar um jogo 1v1 funcional antes de adicionar infraestrutura ou funcionalidades avançadas.

---

## 4. Público inicial

O público inicial é formado por dois jogadores conhecidos que entram na mesma sala por um código ou link de convite.

O jogo precisa funcionar em:

- Celular Android usando navegador moderno.
- Notebook ou desktop usando navegador moderno.
- Redes diferentes, desde que ambos tenham acesso ao servidor do jogo por Tailscale.

---

## 5. Stack tecnológica

| Camada | Tecnologia | Responsabilidade |
|---|---|---|
| Frontend | React + TypeScript + Vite | Interface, navegação, tabuleiro, lobby, placar e estado visual |
| Estilos | Tailwind CSS + CSS Variables | Tema, responsividade, modo claro/escuro e componentes visuais |
| Dados HTTP | TanStack Query | Chamadas REST, cache de dados e sincronização não em tempo real |
| Tempo real | Socket.IO Client | Eventos de sala, presença, palpites, timer e resultado |
| Backend | FastAPI + Python | API HTTP, domínio do jogo, validações e regras |
| WebSocket | python-socketio | Comunicação em tempo real entre jogadores e servidor |
| Validação backend | Pydantic | DTOs, payloads HTTP e eventos validados |
| Banco MVP | SQLite | Persistência local de salas, jogadores, partidas e palpites |
| Banco futuro | PostgreSQL | Produção, concorrência, histórico e ranking |
| ORM | SQLAlchemy | Modelos e acesso a dados |
| Migrações | Alembic | Evolução segura do schema do banco |
| Testes backend | Pytest | Regras do jogo, integração e domínio |
| Testes frontend | Vitest + Testing Library | Componentes, hooks e estado |
| Teste E2E | Playwright | Fluxo de duas pessoas criando e jogando uma partida |
| Ambiente | Docker Compose | Execução reproduzível em desenvolvimento e deploy |
| Rede inicial | Tailscale Serve | Publicação privada para dispositivos da mesma tailnet |

---

## 6. Princípios de arquitetura

O projeto deve começar como um monólito modular.

Não usar microserviços na primeira versão. O sistema terá dois aplicativos no mesmo repositório:

```text
duelo-de-termos/
├── apps/
│   ├── web/                # React + TypeScript + Vite
│   └── api/                # FastAPI + Socket.IO
├── docs/
├── docker-compose.yml
├── README.md
├── PROJECT_SCOPE.md
└── .env.example
```

### Regra de autoridade

O backend é a fonte de verdade para:

- Palavra secreta.
- Dicionário de palavras válidas.
- Validade de um palpite.
- Resultado de cada letra.
- Limite de tentativas.
- Cronômetro.
- Encerramento da rodada.
- Vencedor.
- Pontuação.
- Desempates.
- Estado da sala.
- Reconexões.

O frontend apenas exibe o estado recebido e envia intenções do usuário, como criar sala, entrar na sala, marcar pronto ou enviar palpite.

### Separação em módulos no backend

```text
apps/api/app/
├── main.py
├── core/
│   ├── config.py
│   ├── logging.py
│   └── security.py
├── db/
│   ├── base.py
│   ├── session.py
│   ├── models/
│   └── migrations/
├── users/
│   ├── models.py
│   ├── repository.py
│   └── service.py
├── rooms/
│   ├── models.py
│   ├── repository.py
│   ├── service.py
│   └── schemas.py
├── game/
│   ├── enums.py
│   ├── entities.py
│   ├── rules.py
│   ├── scoring.py
│   ├── service.py
│   └── schemas.py
├── words/
│   ├── repository.py
│   ├── service.py
│   └── words_ptbr.json
├── realtime/
│   ├── socket_server.py
│   ├── events.py
│   ├── handlers.py
│   └── room_gateway.py
└── api/
    ├── health.py
    ├── rooms.py
    └── router.py
```

### Separação em módulos no frontend

```text
apps/web/src/
├── app/
│   ├── routes.tsx
│   ├── providers.tsx
│   └── query-client.ts
├── pages/
│   ├── HomePage.tsx
│   ├── CreateRoomPage.tsx
│   ├── JoinRoomPage.tsx
│   ├── LobbyPage.tsx
│   ├── GamePage.tsx
│   └── ResultsPage.tsx
├── features/
│   ├── identity/
│   ├── room/
│   ├── game/
│   └── realtime/
├── components/
│   ├── ui/
│   ├── GameBoard.tsx
│   ├── VirtualKeyboard.tsx
│   ├── GameTimer.tsx
│   ├── OpponentStatus.tsx
│   └── Scoreboard.tsx
├── services/
│   ├── api.ts
│   └── socket.ts
├── hooks/
├── types/
└── styles/
```

---

## 7. Conceitos do domínio

### Jogador

Um jogador é identificado inicialmente por uma identidade anônima persistida no navegador.

Campos mínimos:

```text
Player
- id: UUID
- nickname: string
- created_at: datetime
```

No MVP:

- O jogador escolhe um apelido.
- O frontend armazena um identificador aleatório em `localStorage`.
- O backend associa a sessão/socket àquela identidade.
- O jogador não pode ocupar os dois slots da mesma sala.

### Sala

Uma sala é o local onde dois jogadores se encontram antes e durante a partida.

```text
Room
- id: UUID
- code: string único
- status: waiting | ready | playing | finished | expired
- mode: normal | competitive | hardcore
- created_at: datetime
- expires_at: datetime
```

```text
RoomPlayer
- room_id: UUID
- player_id: UUID
- slot: 1 | 2
- is_ready: boolean
- joined_at: datetime
- connected_at: datetime
- disconnected_at: datetime | null
```

Regras da sala:

- Uma sala aceita no máximo dois jogadores.
- O primeiro jogador cria a sala e ocupa o slot 1.
- O segundo jogador entra usando um código de convite e ocupa o slot 2.
- A partida só pode começar com dois jogadores conectados e prontos.
- Uma sala abandonada expira automaticamente.
- O código de sala precisa ser aleatório e difícil de adivinhar.
- Não usar códigos incrementais como `1`, `2`, `3`.
- O código inicial pode ter 8 caracteres alfanuméricos, por exemplo: `K7M4P9XZ`.

### Partida

Uma partida é composta por uma ou mais rodadas.

```text
Match
- id: UUID
- room_id: UUID
- status: waiting | active | finished
- mode: normal | competitive | hardcore
- score_player_1: integer
- score_player_2: integer
- current_round_number: integer
- created_at: datetime
- finished_at: datetime | null
```

### Rodada

Uma rodada usa uma palavra secreta compartilhada pelos dois jogadores.

```text
Round
- id: UUID
- match_id: UUID
- word_id: UUID
- mode: normal | competitive | hardcore
- status: waiting | countdown | active | time_expired | final_guess | scoring | finished
- started_at: datetime | null
- expires_at: datetime | null
- ended_at: datetime | null
- winner_player_id: UUID | null
- first_correct_player_id: UUID | null
```

A palavra secreta jamais deve ser enviada ao cliente enquanto a rodada estiver ativa.

### Palpite

```text
Guess
- id: UUID
- round_id: UUID
- player_id: UUID
- word: string
- attempt_number: integer
- submitted_at: datetime
- result: JSON
- is_correct: boolean
- phase: regular | overtime | final
```

O campo `result` pode seguir este formato:

```json
[
  { "letter": "C", "state": "correct" },
  { "letter": "A", "state": "present" },
  { "letter": "S", "state": "absent" },
  { "letter": "A", "state": "absent" },
  { "letter": "S", "state": "correct" }
]
```

Os estados possíveis são:

```text
correct = letra existe e está na posição certa
present = letra existe, mas está na posição errada
absent = letra não existe ou excede a quantidade presente na palavra
```

---

## 8. Regras comuns do jogo

### Palavra

- Cada rodada usa uma palavra secreta.
- Os dois jogadores recebem a mesma palavra secreta.
- A palavra terá exatamente cinco letras no MVP.
- Palavras devem ser normalizadas para letras maiúsculas e sem acentos.
- Palavras enviadas pelos jogadores devem ter cinco letras.
- Palavras inválidas não consomem tentativa.
- O backend deve validar se o palpite existe no dicionário permitido.

### Avaliação das letras

A avaliação deve tratar letras repetidas corretamente.

Algoritmo obrigatório:

1. Comparar cada posição e marcar letras verdes (`correct`) primeiro.
2. Remover ou contabilizar as letras já utilizadas da palavra secreta.
3. Para as posições restantes, marcar amarelo (`present`) apenas se ainda existir ocorrência disponível daquela letra.
4. Marcar as demais letras como cinza (`absent`).

Exemplo conceitual:

```text
Palavra secreta: TERRA
Palpite:          RARAS
```

O algoritmo não pode marcar mais letras como `present` do que a quantidade real existente na palavra secreta.

### Privacidade entre jogadores

Cada jogador pode ver:

- Próprio tabuleiro completo.
- Próprias tentativas.
- Resultado visual de cada letra.
- Timer global.
- Placar.
- Estado resumido do adversário.
- Quantidade de tentativas do adversário.
- Se o adversário está digitando, resolveu, ficou sem tentativas ou desconectou.

Cada jogador não pode ver:

- Palavra secreta enquanto a rodada estiver ativa.
- Palpites do adversário enquanto a rodada estiver ativa.
- Cores das letras do tabuleiro do adversário enquanto a rodada estiver ativa.
- Dados internos de pontuação antes do cálculo oficial.
- Eventos privados do adversário.

---

## 9. Modos de jogo

O jogo terá três modos no MVP:

```text
normal
competitive
hardcore
```

A sala define o modo antes do início da partida. O modo não pode mudar durante uma partida ativa.

### 9.1 Modo Normal

O modo Normal é o modo casual com cronômetro e possibilidade de tentativas extras.

Configuração inicial:

```text
Palavra: 5 letras
Jogadores: 2
Tentativas regulares: 6
Timer: 90 segundos
Tentativas após a 6ª linha: permitidas enquanto o tempo não acabar
Tentativa final após o tempo: 1 para cada jogador que ainda não acertou
Encerramento por primeiro acerto: não
```

Fluxo:

1. Ambos começam com seis tentativas regulares.
2. O cronômetro inicia em 90 segundos.
3. O jogador pode enviar palpites normalmente.
4. Se consumir as seis tentativas e ainda houver tempo, pode enviar tentativas extras.
5. Tentativas extras devem aparecer em uma seção visual chamada `Prorrogação`.
6. Se um jogador acertar, ele fica bloqueado e marcado como `Resolvido`.
7. O outro jogador continua enquanto houver tempo.
8. Quando o cronômetro chegar a zero, nenhum novo palpite regular ou de prorrogação será aceito.
9. Cada jogador que ainda não acertou recebe exatamente uma tentativa final.
10. Após usar ou perder a tentativa final, o jogador fica bloqueado.
11. A rodada termina quando todos os jogadores estiverem resolvidos, bloqueados ou tiverem concluído a tentativa final.
12. O backend calcula o placar oficial.

Pontuação:

| Condição | Pontos |
|---|---:|
| Acertou na tentativa 1, 2 ou 3 | 3 |
| Acertou na tentativa 4, 5 ou 6 | 2 |
| Acertou em prorrogação | 1 |
| Acertou na tentativa final pós-tempo | 1 |
| Não acertou | 0 |
| Primeiro jogador a acertar a palavra | bônus de 1 |

Regras importantes:

- Não existe limite de tentativas de prorrogação enquanto o timer estiver ativo.
- O servidor deve aplicar rate limit para evitar spam de palpites.
- Uma tentativa final não pode ser enviada antes do timer expirar.
- Quem erra a tentativa final recebe 0 ponto naquela rodada.
- Se ambos acertarem, cada um recebe sua pontuação conforme a própria tentativa.
- Em empate de pontos, usar menor quantidade de tentativas; persistindo empate, usar menor timestamp registrado pelo servidor.

### 9.2 Modo Competitivo

O modo Competitivo prioriza precisão e eficiência.

Configuração inicial:

```text
Palavra: 5 letras
Jogadores: 2
Tentativas: exatamente 6 por jogador
Timer: não obrigatório no MVP
Tentativas extras: não
Tentativa final após tempo: não
Encerramento por primeiro acerto: não
```

Fluxo:

1. Ambos recebem a mesma palavra secreta.
2. Cada jogador tem exatamente seis tentativas.
3. Não existem linhas extras.
4. Quando um jogador acerta, ele fica resolvido e não pode enviar mais tentativas.
5. O outro jogador pode usar as tentativas restantes.
6. A rodada termina quando ambos os jogadores acertarem, esgotarem tentativas ou não puderem mais jogar.
7. O backend calcula o resultado.

Pontuação:

\[
pontos = 7 - tentativas\_usadas
\]

| Tentativas usadas | Pontos |
|---:|---:|
| 1 | 6 |
| 2 | 5 |
| 3 | 4 |
| 4 | 3 |
| 5 | 2 |
| 6 | 1 |
| Não acertou | 0 |

Desempate:

1. Maior pontuação.
2. Menor número de tentativas.
3. Menor timestamp de acerto registrado pelo servidor.
4. Empate oficial se todos os critérios forem iguais.

### 9.3 Modo Hardcore

O modo Hardcore valoriza velocidade e encerra imediatamente no primeiro acerto válido.

Configuração inicial:

```text
Palavra: 5 letras
Jogadores: 2
Tentativas: até acertar ou o timer expirar
Timer: 90 segundos
Tentativas extras: não
Tentativa final após tempo: não
Encerramento por primeiro acerto: sim
```

Fluxo:

1. Os dois jogadores recebem a mesma palavra.
2. O cronômetro inicia em 90 segundos.
3. Os dois enviam palpites simultaneamente.
4. Quando o backend recebe e valida um palpite correto, ele encerra a rodada imediatamente.
5. O primeiro jogador cujo acerto foi aceito pelo servidor vence.
6. Todos os palpites que chegarem depois do encerramento devem ser rejeitados.
7. Se o timer terminar sem acerto, a rodada encerra sem vencedor.

Pontuação:

| Condição | Pontos |
|---|---:|
| Primeiro jogador a acertar | 3 |
| Outro jogador | 0 |
| Ninguém acertou antes do tempo | 0 para ambos |

Regra de concorrência:

- O relógio do dispositivo do jogador não deve decidir o vencedor.
- O backend deve usar horário e ordem do próprio servidor.
- A operação de registrar o primeiro acerto precisa ser atômica.
- Se dois palpites corretos chegarem quase juntos, somente o primeiro persistido deve ganhar.
- Depois de definir `winner_player_id`, nenhuma outra tentativa pode mudar o resultado.

---

## 10. Máquina de estados

### Estados gerais da rodada

```text
waiting
  -> countdown
  -> active
  -> time_expired
  -> final_guess
  -> scoring
  -> finished
```

Nem todos os modos usam todos os estados.

### Modo Normal

```text
waiting
  -> countdown
  -> active
  -> time_expired
  -> final_guess
  -> scoring
  -> finished
```

### Modo Competitivo

```text
waiting
  -> countdown
  -> active
  -> scoring
  -> finished
```

### Modo Hardcore

```text
waiting
  -> countdown
  -> active
  -> finished
```

### Estados individuais do jogador

```text
playing
resolved
out_of_attempts
waiting_final_guess
final_guess_used
disconnected
```

---

## 11. Eventos em tempo real

O Socket.IO deve usar uma room interna por sala:

```text
room:<room_id>
```

Não emitir eventos de uma sala para sockets de outras salas.

### Eventos cliente para servidor

| Evento | Payload | Descrição |
|---|---|---|
| `identity:set` | `nickname` | Define ou atualiza apelido do jogador |
| `room:create` | `mode`, `nickname` | Cria sala e coloca jogador no slot 1 |
| `room:join` | `code`, `nickname` | Entra em sala existente |
| `room:ready` | `roomId`, `ready` | Marca jogador como pronto ou não pronto |
| `match:start` | `roomId` | Solicita início quando houver dois jogadores prontos |
| `guess:submit` | `roundId`, `word`, `clientRequestId` | Envia palpite |
| `rematch:vote` | `matchId`, `accept` | Aceita ou recusa próxima rodada |
| `player:typing` | `roomId`, `isTyping` | Atualiza indicador visual opcional |
| `room:leave` | `roomId` | Sai da sala |

### Eventos servidor para cliente

| Evento | Destino | Payload | Descrição |
|---|---|---|---|
| `room:state` | Sala | sala, jogadores, modo, status | Estado resumido da sala |
| `match:started` | Sala | partida e rodada pública | Partida começou |
| `round:started` | Sala | rodada pública, timer | Rodada começou |
| `guess:result` | Apenas jogador que enviou | palpite avaliado e tabuleiro privado | Resultado oficial do palpite |
| `opponent:progress` | Apenas oponente | tentativa, status, resolvido | Progresso resumido sem vazar letras |
| `round:timer` | Sala | segundos restantes | Atualização do timer |
| `round:time_expired` | Sala | estado da fase final | Timer encerrou |
| `round:final_guess_available` | Jogador elegível | roundId | Libera última tentativa no modo normal |
| `round:finished` | Sala | vencedor, resultado, palavra revelada, placar | Rodada encerrada |
| `match:state` | Sala | placar, rodada atual | Estado da partida |
| `player:presence` | Sala | jogador, online/offline | Presença e reconexão |
| `game:error` | Apenas solicitante | code, message | Erro de validação ou estado |

### Formato de erro recomendado

```json
{
  "code": "ROUND_CLOSED",
  "message": "A rodada já foi encerrada."
}
```

Outros códigos úteis:

```text
INVALID_WORD
INVALID_WORD_LENGTH
PLAYER_NOT_IN_ROOM
ROOM_NOT_FOUND
ROOM_FULL
ROOM_NOT_READY
ROUND_NOT_ACTIVE
NO_GUESSES_REMAINING
FINAL_GUESS_NOT_AVAILABLE
PLAYER_ALREADY_RESOLVED
RATE_LIMITED
UNAUTHORIZED
```

---

## 12. API HTTP inicial

As ações em tempo real devem ser feitas por Socket.IO. A API HTTP deve ser usada para leitura, saúde e operações simples.

```text
GET /health
GET /api/v1/rooms/{code}
GET /api/v1/matches/{match_id}
GET /api/v1/words/validate?word=CASAS
```

Resposta de saúde esperada:

```json
{
  "status": "ok"
}
```

---

## 13. Interface do usuário

### Telas necessárias no MVP

| Tela | Objetivo |
|---|---|
| Home | Mostrar nome do jogo, criar sala e entrar por código |
| Criar sala | Escolher apelido e modo de jogo |
| Entrar na sala | Inserir apelido e código da sala |
| Lobby | Mostrar os dois jogadores, status de conexão e botão de pronto |
| Jogo | Tabuleiro, teclado, timer, status do rival e placar |
| Resultado da rodada | Mostrar palavra, vencedor, pontos e revanche |
| Sala expirada/cheia | Exibir erro amigável e retorno para a home |

### Componentes essenciais

```text
GameBoard
GuessRow
LetterTile
VirtualKeyboard
GameTimer
OpponentStatus
Scoreboard
RoomCodeCard
PlayerPresence
ModeSelector
RematchPanel
ConnectionStatus
Toast / ErrorMessage
```

### Requisitos de responsividade

- Prioridade para mobile.
- Tabuleiro deve caber em telas estreitas.
- Teclado virtual deve ser clicável/tocável.
- Entrada física do teclado deve funcionar em desktop.
- Não depender de hover para ações importantes.
- Usar contraste suficiente para estados das letras.
- Não depender apenas de cor; incluir bordas, animações ou textos acessíveis quando necessário.

### Feedback visual

O jogo deve mostrar:

- Letra correta na posição correta.
- Letra presente em posição errada.
- Letra ausente.
- Erro de palavra inválida.
- Sala cheia.
- Oponente conectado/desconectado.
- Oponente digitando.
- Oponente resolvido.
- Timer chegando ao fim.
- Tentativa final liberada.
- Rodada encerrada.
- Palavra revelada apenas após o fim.

---

## 14. Segurança e integridade

### Regras obrigatórias

- Nunca enviar a palavra secreta ao frontend durante uma rodada ativa.
- Nunca confiar em pontuação enviada pelo cliente.
- Nunca confiar em horário enviado pelo cliente.
- Nunca confiar em resultado de letras calculado no cliente.
- Validar todos os payloads HTTP e Socket.IO.
- Verificar se o socket pertence ao jogador da sala.
- Verificar se o jogador pertence à rodada.
- Limitar sala a dois jogadores.
- Impedir o mesmo jogador de ocupar os dois slots.
- Usar UUIDs e códigos aleatórios.
- Usar variáveis de ambiente para segredos e URLs.
- Não versionar arquivos `.env`.
- Implementar rate limit para `room:create`, `room:join` e `guess:submit`.
- Registrar logs de erro e eventos importantes.
- Rejeitar palpites enviados depois do fim da rodada.
- Não permitir que o frontend altere diretamente estado de rodada ou placar.

### Reconexão

No MVP:

1. O jogador deve poder reconectar à mesma sala usando sua identidade salva no navegador.
2. O backend deve associar o novo socket ao mesmo `player_id`.
3. A sala deve notificar o oponente sobre desconexão.
4. O jogo pode aguardar até 30 segundos pela reconexão.
5. Se o jogador não voltar, a rodada pode ser encerrada como abandono ou anulada. A regra precisa ficar configurável.
6. O jogador reconectado deve receber um snapshot atualizado do estado que ele tem permissão para visualizar.

---

## 15. Persistência e banco de dados

### SQLite no MVP

Usar SQLite para desenvolvimento e primeira versão privada.

Persistir:

- Jogadores.
- Salas.
- Participantes da sala.
- Partidas.
- Rodadas.
- Tentativas.
- Pontuação.
- Resultado de cada rodada.

### PostgreSQL no futuro

Migrar para PostgreSQL quando houver:

- Mais jogadores.
- Hospedagem pública.
- Ranking.
- Necessidade de maior concorrência.
- Mais de uma instância do backend.
- Relatórios e consultas mais complexas.

### Regra para segredo da rodada

A palavra secreta pode ser salva no banco, mas nunca deve aparecer em serializadores, DTOs ou eventos enviados durante uma rodada ativa.

Após `round:finished`, a palavra pode ser revelada para os dois jogadores.

---

## 16. Testes obrigatórios

### Testes unitários do domínio

Criar testes para:

- Palavra com tamanho inválido.
- Palavra com caracteres inválidos.
- Palavra fora do dicionário.
- Acerto completo.
- Letra correta na posição correta.
- Letra presente em posição errada.
- Letra ausente.
- Letras repetidas na palavra secreta.
- Palpite com mais letras repetidas do que a palavra secreta.
- Palpite repetido.
- Tentativa após a rodada terminar.
- Tentativa de jogador fora da sala.
- Tentativa de jogador já resolvido.

### Testes por modo

#### Normal

- Jogador pode enviar até seis tentativas regulares.
- Jogador pode continuar após a sexta tentativa enquanto houver tempo.
- Jogador resolvido não pode continuar enviando palpites.
- Ao fim do tempo, jogador não resolvido recebe uma tentativa final.
- Apenas uma tentativa final é aceita.
- Erro na tentativa final resulta em zero ponto.
- Acerto na prorrogação recebe um ponto.
- Primeiro acerto recebe bônus.

#### Competitivo

- Jogador possui no máximo seis tentativas.
- Sétima tentativa é rejeitada.
- Não existe prorrogação.
- Pontuação segue `7 - tentativas_usadas`.
- Sem acerto resulta em zero ponto.
- Desempate usa tentativas e depois timestamp do servidor.

#### Hardcore

- Primeiro acerto encerra a rodada.
- Segundo palpite correto após o primeiro acerto é rejeitado.
- Dois acertos quase simultâneos geram apenas um vencedor.
- Timer encerrado sem acerto gera zero para ambos.
- O vencedor é definido por ordem atômica registrada no backend.

### Testes de integração

Criar testes para:

- Criar sala.
- Entrar na sala.
- Impedir terceiro jogador.
- Marcar jogadores como prontos.
- Iniciar partida.
- Enviar palpite via Socket.IO.
- Receber resultado privado.
- Oponente receber apenas progresso público.
- Encerrar rodada.
- Reconectar com a mesma identidade.

### Testes E2E

Usar Playwright quando o MVP estiver funcional:

1. Jogador A cria sala.
2. Jogador B entra com código.
3. Ambos marcam pronto.
4. A rodada inicia.
5. Jogador A envia palpite.
6. Jogador B vê apenas o progresso de A.
7. Um jogador vence.
8. Ambos veem resultado e placar.
9. Ambos aceitam revanche.
10. Nova rodada inicia.

---

## 17. Fases de implementação

### Fase 0 — Preparação

Objetivo: definir repositório, documentação e estrutura mínima.

Tarefas:

```text
[ ] Criar repositório Git.
[ ] Adicionar README.md.
[ ] Adicionar PROJECT_SCOPE.md.
[ ] Criar .gitignore.
[ ] Criar .env.example.
[ ] Criar estrutura apps/web e apps/api.
[ ] Configurar formatação, lint e testes.
[ ] Criar documentação de comandos de desenvolvimento.
```

Critério de aceite:

```text
O projeto inicia localmente e possui documentação clara.
```

### Fase 1 — Jogo local no frontend

Objetivo: validar UI e regras básicas sem rede.

Tarefas:

```text
[x] Criar React + TypeScript + Vite.
[x] Configurar Tailwind.
[x] Criar tela inicial.
[x] Criar tabuleiro de seis linhas por cinco colunas.
[x] Criar teclado virtual.
[x] Aceitar teclado físico.
[x] Criar palavra secreta temporária fixa.
[x] Implementar evaluateGuess() como função pura.
[x] Implementar cores das letras.
[x] Tratar letras repetidas.
[x] Criar testes Vitest do algoritmo.
[x] Criar tela de vitória e derrota local.
```

Critério de aceite:

```text
Uma pessoa consegue jogar localmente no navegador, com avaliação correta de letras repetidas.
```

### Fase 2 — Backend e motor de regras

Objetivo: criar o domínio oficial do jogo sem Socket.IO.

> **Nota (2026-10-03):** cortado rápido a pedido do usuário, comprimido com as
> Fases 3 e 4 — ver nota no início da Fase 4. Entregue: motor de regras single-mode
> (sem GameMode/Normal/Competitivo/Hardcore, sem classes Round/PlayerRoundState
> formais — ver `Sala`/`Jogador`/`Tentativa` em `app/game/rooms.py`).

Tarefas:

```text
[x] Criar FastAPI.
[x] Criar GET /health.
[x] Configurar Pydantic.
[x] Criar catálogo inicial de palavras em português.
[ ] Implementar normalização de palavras. (só .upper(); sem tratar acento)
[x] Implementar validação de palpite.
[x] Implementar avaliação de letras.
[ ] Criar GameMode.
[ ] Criar Round, PlayerRoundState e GuessResult.
[ ] Implementar regras de Normal, Competitivo e Hardcore.
[x] Criar testes Pytest completos do domínio. (do modo único que existe)
```

Critério de aceite:

```text
O backend consegue executar regras dos três modos sem interface, com testes automatizados.
```

**Não atingido como escrito** — só 1 modo existe, não 3.

### Fase 3 — Salas e identidade simples

Objetivo: permitir que dois jogadores entrem na mesma sala.

> **Nota (2026-10-03):** sem persistência (tudo em memória, um processo só —
> cai se o servidor reiniciar no meio de uma partida). Eventos Socket.IO em
> português (`criar_sala`/`entrar_sala`/`enviar_palpite`), não no namespace
> `room:*`/`guess:*` descrito abaixo — mesma ideia, nomes diferentes.

Tarefas:

```text
[ ] Configurar SQLite e SQLAlchemy.
[ ] Criar migrações Alembic.
[ ] Criar Player.
[ ] Criar Room e RoomPlayer. (equivalente em memória: Sala/Jogador)
[x] Criar geração segura de código de sala. (secrets, não random)
[ ] Criar identidade anônima persistida. (nome é só da conexão, não persiste)
[ ] Criar endpoints HTTP de leitura.
[x] Configurar Socket.IO.
[x] Implementar room:create. (criar_sala)
[x] Implementar room:join. (entrar_sala)
[x] Impedir terceiro jogador.
[ ] Implementar room:ready. (a partida começa sozinha quando o 2º entra)
[ ] Sincronizar room:state. (eventos pontuais, não um estado sincronizado)
```

Critério de aceite:

```text
Duas abas de navegador conseguem entrar na mesma sala e marcar-se como prontas.
```

**Parcialmente atingido**: as duas abas entram na mesma sala de verdade (testado com 2 browsers reais via Playwright) e a partida começa sozinha — só não existe o passo explícito de "pronto".

### Fase 4 — Partida em tempo real

Objetivo: criar uma partida 1v1 funcional.

> **Nota (2026-10-03):** o critério de aceite desta fase — "dois dispositivos
> disputam uma partida completa em tempo real" — **foi atingido e testado de
> verdade** (2 contextos de navegador reais via Playwright, não só simulação
> Python): sala por código, corrida simultânea, resultado só pra quem jogou,
> progresso do oponente sem vazar letra nenhuma (testado explicitamente nos
> dois níveis), fim por vitória/derrota/empate, palavra revelada só no fim.
> Sem timer, sem placar/múltiplas rodadas, sem os 3 modos, sem revanche —
> cortado deliberadamente pelo prazo.

Tarefas:

```text
[ ] Criar Match e Round no banco.
[ ] Implementar início de rodada. (não há "rodada" separada da partida)
[ ] Implementar timer no backend.
[x] Implementar guess:submit. (enviar_palpite)
[x] Emitir guess:result apenas para quem enviou.
[x] Emitir opponent:progress sem vazar letras.
[ ] Implementar placar.
[x] Implementar fim de rodada.
[x] Revelar palavra somente ao final.
[ ] Implementar os três modos.
[x] Implementar tela de resultado.
[ ] Implementar revanche. ("voltar pro lobby" existe; revanche direta não)
```

Critério de aceite:

```text
Dois dispositivos conseguem disputar uma partida completa em tempo real.
```

**Atingido e testado de verdade** (ver nota acima).

### Fase 5 — Qualidade, persistência e reconexão

Objetivo: tornar a experiência robusta.

Tarefas:

```text
[ ] Salvar histórico de rodadas e palpites.
[ ] Implementar reconexão.
[ ] Implementar expiração de sala.
[ ] Implementar tratamento de abandono.
[ ] Adicionar logs estruturados.
[ ] Adicionar rate limiting.
[ ] Adicionar testes de integração.
[ ] Adicionar testes E2E Playwright.
[ ] Melhorar acessibilidade.
[ ] Revisar UI mobile.
```

Critério de aceite:

```text
O jogo resiste a atualização de página, reconexão e erros comuns sem corromper a partida.
```

### Fase 6 — Deploy privado

Objetivo: permitir acesso por Tailscale.

Tarefas:

```text
[ ] Criar Dockerfile do backend.
[ ] Criar Dockerfile do frontend.
[ ] Criar docker-compose.yml.
[ ] Configurar reverse proxy se necessário.
[ ] Configurar variáveis de produção.
[ ] Expor o serviço local pelo Tailscale Serve.
[ ] Testar em dois dispositivos conectados à mesma tailnet.
[ ] Documentar deploy privado.
```

Critério de aceite:

```text
Duas pessoas conectadas à mesma tailnet conseguem jogar usando HTTPS fornecido pelo Tailscale.
```

---

## 18. Deploy e Tailscale

### Desenvolvimento local

```text
Frontend: http://localhost:5173
Backend HTTP: http://localhost:8000
Socket.IO: mesmo host/porta do backend
```

### Publicação privada

O primeiro deploy deve usar Tailscale Serve.

Objetivo:

- Permitir que dispositivos autenticados na mesma tailnet acessem o jogo.
- Não expor o jogo para a internet pública.
- Não abrir portas no roteador.

### Publicação pública futura

Tailscale Funnel só deve ser considerado depois que o projeto tiver:

```text
[ ] Validação completa de payloads.
[ ] Rate limiting.
[ ] Logs.
[ ] Tratamento de erros.
[ ] Código de convite seguro.
[ ] Configuração de CORS restritiva.
[ ] Revisão de segredos.
[ ] Persistência confiável.
[ ] Política clara para salas públicas e privadas.
```

---

## 19. Critérios de aceite do MVP

O MVP está pronto quando:

```text
[ ] Um usuário consegue escolher apelido.
[ ] Um usuário consegue criar uma sala em um dos três modos.
[ ] A sala gera um código compartilhável.
[ ] Um segundo usuário consegue entrar usando o código.
[ ] A sala não aceita terceiro usuário.
[ ] Ambos conseguem marcar-se como prontos.
[ ] A partida inicia somente com os dois jogadores.
[ ] Ambos recebem a mesma palavra.
[ ] A palavra secreta não vaza antes do fim.
[ ] Os palpites são validados pelo backend.
[ ] Letras repetidas são avaliadas corretamente.
[ ] Cada modo aplica suas regras específicas.
[ ] Um jogador não vê o tabuleiro do adversário durante a rodada.
[ ] Oponente vê apenas progresso resumido.
[ ] O placar é calculado pelo servidor.
[ ] O jogo encerra corretamente.
[ ] A palavra é revelada no resultado.
[ ] Existe opção de revanche.
[ ] O jogo funciona em celular e desktop.
[ ] O jogo pode ser acessado por dois dispositivos via Tailscale.
[ ] Os principais fluxos possuem testes automatizados.
```

---

## 20. Regras para geração de código

Ao implementar este projeto:

1. Implementar somente a fase solicitada.
2. Não antecipar microserviços, Redis, filas, autenticação complexa ou deploy público.
3. Não colocar regra de negócio em componentes React.
4. Não colocar a palavra secreta em estado do frontend durante rodada ativa.
5. Não confiar em dados enviados pelo cliente para decisão de jogo.
6. Não criar endpoints ou eventos sem validação de schema.
7. Não usar `any` em TypeScript, exceto em caso extremamente justificado.
8. Não usar estado global desnecessário.
9. Criar testes antes ou junto com regras de domínio.
10. Manter funções de regras puras sempre que possível.
11. Manter eventos Socket.IO pequenos, explícitos e tipados.
12. Não vazar dados privados do oponente.
13. Tratar erros de maneira amigável no frontend.
14. Documentar decisões técnicas relevantes no README.
15. Antes de criar código, explicar brevemente a estrutura proposta e listar os arquivos que serão criados ou alterados.

---

## 21. Primeiro prompt de implementação

Use este prompt para iniciar a primeira tarefa:

```text
Você está implementando o projeto "Duelo de Termos".
Leia PROJECT_SCOPE.md e respeite todas as restrições dele.

Implemente somente a Fase 0 e a base da Fase 1.

Objetivo:
- Criar um monorepo simples com apps/web e apps/api.
- Configurar React + TypeScript + Vite no frontend.
- Configurar FastAPI no backend.
- Criar endpoint GET /health retornando {"status":"ok"}.
- Criar a estrutura inicial de componentes e páginas no frontend.
- Criar apenas um tabuleiro visual estático 6x5.
- Não implementar Socket.IO, banco, autenticação, salas, timer ou regras completas ainda.

Requisitos:
- TypeScript estrito.
- Python com tipagem.
- Código organizado.
- Adicionar README com comandos para rodar frontend e backend.
- Adicionar .env.example e .gitignore.
- Antes de gerar código, explique a estrutura e liste os arquivos que serão criados.
- Ao final, liste comandos exatos para instalar dependências e iniciar os dois serviços no Arch Linux.
```
