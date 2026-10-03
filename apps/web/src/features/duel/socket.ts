import { io, type Socket } from 'socket.io-client'

// Em produção VITE_API_URL fica vazio de propósito (mesma origem, ver
// .env.production na raiz) — io() sem argumento já conecta na origem atual.
// (truthy-check de propósito: string vazia também deve cair no fallback,
// por isso não dá pra usar só `??` aqui.)
const SOCKET_URL = import.meta.env.VITE_API_URL ?? ''

let socket: Socket | null = null

export function getSocket(): Socket {
  socket ??= SOCKET_URL ? io(SOCKET_URL, { autoConnect: false }) : io({ autoConnect: false })
  return socket
}
