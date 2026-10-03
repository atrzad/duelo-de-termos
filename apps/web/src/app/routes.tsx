import { createBrowserRouter } from 'react-router'

import { DuelPage } from '../pages/DuelPage'
import { GamePage } from '../pages/GamePage'
import { HomePage } from '../pages/HomePage'
import { NotFoundPage } from '../pages/NotFoundPage'

export const router = createBrowserRouter([
  { path: '/', element: <HomePage /> },
  { path: '/jogo', element: <GamePage /> },
  { path: '/duelo', element: <DuelPage /> },
  { path: '*', element: <NotFoundPage /> },
])
