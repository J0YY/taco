import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'

// Reset scroll on route change (but preserve in-page anchor scrolling on landing).
export default function ScrollToTop() {
  const { pathname, hash } = useLocation()
  useEffect(() => {
    if (!hash) window.scrollTo(0, 0)
  }, [pathname, hash])
  return null
}
