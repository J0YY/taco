import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import './styles/global.css'
import './styles/app.css'
import Landing from './landing/Landing.jsx'
import Research from './research/Research.jsx'
import Dashboard from './dashboard/Dashboard.jsx'
import ScrollToTop from './components/ScrollToTop.jsx'

// basename must match the Vite base / GitHub Pages project path (e.g. /taco)
const basename = import.meta.env.BASE_URL.replace(/\/$/, '')

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter basename={basename}>
      <ScrollToTop />
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/research" element={<Research />} />
        <Route path="/demo/*" element={<Dashboard />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>,
)
