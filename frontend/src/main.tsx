import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { DroneProvider } from './DroneContext.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <DroneProvider>
      <App />
    </DroneProvider>
  </StrictMode>,
)
