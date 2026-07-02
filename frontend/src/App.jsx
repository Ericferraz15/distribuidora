import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './auth/AuthContext.jsx'
import Layout from './components/Layout.jsx'
import ProtectedRoute from './components/ProtectedRoute.jsx'
import Login from './pages/Login.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Operacao from './pages/Operacao.jsx'
import Estoque from './pages/Estoque.jsx'
import Usuarios from './pages/Usuarios.jsx'

export default function App() {
  const { autenticado, isAdmin } = useAuth()
  const inicio = isAdmin ? '/dashboard' : '/operacao'

  return (
    <Routes>
      <Route
        path="/login"
        element={autenticado ? <Navigate to={inicio} replace /> : <Login />}
      />

      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route path="/operacao" element={<Operacao />} />
        <Route path="/estoque" element={<Estoque />} />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute adminOnly>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/usuarios"
          element={
            <ProtectedRoute adminOnly>
              <Usuarios />
            </ProtectedRoute>
          }
        />
      </Route>

      <Route path="/" element={<Navigate to={autenticado ? inicio : '/login'} replace />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
