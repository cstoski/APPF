import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App.jsx'
import { AuthProvider } from './hooks/useAuth.jsx'
import { LicencaProvider } from './hooks/useLicenca.jsx'
import './styles/global.css'
import './styles/operacional.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <LicencaProvider>
          <App />
        </LicencaProvider>
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>,
)
