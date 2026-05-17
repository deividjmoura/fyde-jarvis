import {
  BrowserRouter,
  Routes,
  Route,
} from 'react-router-dom'

import LoginPage from '../pages/Login/LoginPage'
import HomePage from '../pages/Home/HomePage'

export default function AppRoutes() {

  return (
    <BrowserRouter>

      <Routes>

        <Route
          path="/"
          element={<LoginPage />}
        />

        <Route
          path="/home"
          element={<HomePage />}
        />

      </Routes>

    </BrowserRouter>
  )
}