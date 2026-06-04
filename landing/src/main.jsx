import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import './styles/global.css'
import './styles/app.css'
import Landing from './landing/Landing.jsx'
import Dashboard from './dashboard/Dashboard.jsx'
import ScrollToTop from './components/ScrollToTop.jsx'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <ScrollToTop />
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/demo/*" element={<Dashboard />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>,
)
