import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext.jsx'

// Protege rotas autenticadas e, opcionalmente, exige perfil admin (RNF03).
export default function ProtectedRoute({ children, adminOnly = false }) {
  const { autenticado, isAdmin } = useAuth()
  const location = useLocation()

  if (!autenticado) {
    return <Navigate to="/login" replace state={{ from: location }} />
  }
  if (adminOnly && !isAdmin) {
    return <Navigate to="/operacao" replace />
  }
  return children
}
