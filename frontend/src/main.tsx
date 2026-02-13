import React from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import './utils/consoleSuppression'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <App />
)
