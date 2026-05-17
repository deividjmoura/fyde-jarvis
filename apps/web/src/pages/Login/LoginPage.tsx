import CyberInput from '../../components/ui/CyberInput'
import GoogleButton from '../../components/ui/GoogleButton'

import './login.css'

export default function LoginPage() {
  return (
    <div className="login-screen">

      <div className="bg-grid"></div>
      <div className="bg-glow"></div>

      <div className="login-panel">

        <div className="login-header">

          <h1>FYDE</h1>

          <p>
            ARTIFICIAL INTELLIGENCE SYSTEM
          </p>

        </div>

        <form className="login-form">

          <CyberInput
            label="EMAIL"
            type="email"
            placeholder="user@fyde.ai"
          />

          <CyberInput
            label="PASSWORD"
            type="password"
            placeholder="••••••••"
          />

          <button
            className="login-button"
            type="submit"
          >
            INITIALIZE
          </button>

          <div className="divider">
            EXTERNAL AUTH
          </div>

          <GoogleButton />

        </form>

      </div>

    </div>
  )
}