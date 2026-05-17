import CyberInput from '../../components/ui/CyberInput'
import GoogleButton from '../../components/ui/GoogleButton'
import { useState } from 'react'

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
  async function handleAuth(
  event: React.FormEvent
) {

  event.preventDefault()

  try {

    if (isRegistering) {

      const result =
        await createUserWithEmailAndPassword(
          auth,
          email,
          password
        )

      console.log('user created')

      console.log(result.user)

    } else {

      const result =
        await signInWithEmailAndPassword(
          auth,
          email,
          password
        )

      console.log('login success')

      console.log(result.user)

    }

  } catch (error) {

    console.error(error)

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

          <button
            className="login-button"
            type="submit"
          >
            {isRegistering
            ? 'CREATE ACCOUNT'
            : 'INITIALIZE'}
          </button>
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