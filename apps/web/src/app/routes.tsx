import { createBrowserRouter } from 'react-router'

import { GamePage } from '../pages/GamePage'
import { HomePage } from '../pages/HomePage'
import { NotFoundPage } from '../pages/NotFoundPage'

export const router = createBrowserRouter([
  { path: '/', element: <HomePage /> },
  { path: '/jogo', element: <GamePage /> },
  { path: '*', element: <NotFoundPage /> },
])
