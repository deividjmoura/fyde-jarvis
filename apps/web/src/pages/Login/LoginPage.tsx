import CyberInput from '../../components/ui/CyberInput'
import GoogleButton from '../../components/ui/GoogleButton'
import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import {
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
} from 'firebase/auth'

import { auth } from '../../services/firebase'

import './login.css'

export default function LoginPage() {
  const [isRegistering, setIsRegistering] =
  useState(false)

const [email, setEmail] =
  useState('')

const [password, setPassword] =
  useState('')

const [message, setMessage] =
  useState('')

const [errorMessage, setErrorMessage] =
  useState('')
  const navigate = useNavigate()
  const passwordStrength = useMemo(() => {

  if (password.length < 6)
    return 'weak'

  if (password.length < 10)
    return 'medium'

  return 'strong'

}, [password])
  async function handleAuth(
  event: React.FormEvent
) {


  event.preventDefault()

  setMessage('')
  setErrorMessage('')
  try {

    if (isRegistering) {

      const result =
        await createUserWithEmailAndPassword(
          auth,
          email,
          password
        )

          setMessage(
      'Account created successfully'
)
      navigate('/home')
      console.log(result.user)

    } else {

      const result =
        await signInWithEmailAndPassword(
          auth,
          email,
          password
        )

      setMessage(
      'Login successful'
      )
      navigate('/home')
      console.log(result.user)

    }

    } catch (error: any) {

      console.error(error)

      setErrorMessage(
        error.message
      )
    }
}
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

        <form
        className="login-form"
        onSubmit={handleAuth}
>

          <CyberInput
          label="EMAIL"
          type="email"
          placeholder="user@fyde.ai"
          value={email}
          onChange={(e) =>
            setEmail(e.target.value)
          }
        />

                  <CyberInput
          label="PASSWORD"
          type="password"
          placeholder="••••••••"
          value={password}
          onChange={(e) =>
            setPassword(e.target.value)
          }
/>
          {password && (

          <div
            className={`password-strength ${passwordStrength}`}
          >
            {passwordStrength}
          </div>

          )}
          <button
            className="login-button"
            type="submit"
          >
            {isRegistering
            ? 'CREATE ACCOUNT'
            : 'INITIALIZE'}
          </button>
          {message && (
          <div className="success-message">
            {message}
          </div>
        )}

          {errorMessage && (
          <div className="error-message">
            {errorMessage}
          </div>
        )}
          <button
          className="register-button"
          type="button"
          onClick={() =>
            setIsRegistering(
              !isRegistering
            )
          }
        >
          {isRegistering
            ? 'BACK TO LOGIN'
            : 'CREATE ACCOUNT'}
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