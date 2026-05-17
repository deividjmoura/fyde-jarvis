import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import {
  createUserWithEmailAndPassword,
  sendPasswordResetEmail,
  signInWithEmailAndPassword,
} from 'firebase/auth'

import { auth } from '../../services/firebase'

import ParticleBackground from '../../components/background/ParticleBackground'
import GoogleButton from '../../components/ui/GoogleButton'

import './login.css'

type TabType =
  | 'login'
  | 'register'

export default function LoginPage() {

  const navigate =
    useNavigate()

  const [activeTab, setActiveTab] =
    useState<TabType>('login')

  const [email, setEmail] =
    useState('')

  const [password, setPassword] =
    useState('')

  const [message, setMessage] =
    useState('')

  const [errorMessage, setErrorMessage] =
    useState('')
  const [loginAttempts, setLoginAttempts] =
  useState(0)
  const passwordValidation = useMemo(() => {

  if (!password) return null

  const validations = {
    uppercase:
      /[A-Z]/.test(password),

    special:
      /[^A-Za-z0-9]/.test(password),

    number:
      /\d/.test(password),

    minLength:
      password.length >= 8,
  }

  const passed =
    Object.values(validations)
      .filter(Boolean).length

  let strength = 'weak'

  if (passed >= 3)
    strength = 'medium'

  if (passed === 4)
    strength = 'strong'

  return {
    strength,
    validations,
  }

}, [password])

  async function handleAuth(
    event: React.FormEvent
  ) {

    event.preventDefault()

    setMessage('')
    setErrorMessage('')

    try {

      if (activeTab === 'register') {

        await createUserWithEmailAndPassword(
          auth,
          email,
          password
        )

        setMessage(
          'Account created successfully'
        )

      } else {

        await signInWithEmailAndPassword(
          auth,
          email,
          password
        )

        setMessage(
          'Login successful'
        )
      }

      navigate('/home')

    } catch (error: any) {

      console.error(error)

      setErrorMessage(
        error.message
      )
    }
  }

  async function handleResetPassword() {

    try {

      setMessage('')
      setErrorMessage('')

      if (!email) {

        setErrorMessage(
          'Enter your email first'
        )

        return
      }

      await sendPasswordResetEmail(
        auth,
        email
      )

      setMessage(
        'Password reset email sent'
      )

    } catch (error: any) {

      setErrorMessage(
        error.message
      )
      if (activeTab === 'login') {

      setLoginAttempts(
        (prev) => prev + 1
      )
    }
    }
  }

  return (

    <div className="login-screen">

      <ParticleBackground />

      <div className="corner corner-top">
        FYDE
      </div>

      <div className="corner corner-bottom">
        AI SYSTEM INTERFACE
      </div>

      <div className="auth-card">

        <div className="tabs">

          <button
            className={
              activeTab === 'login'
                ? 'tab active'
                : 'tab'
            }
            onClick={() =>
              setActiveTab('login')
            }
          >
            LOGIN
          </button>

          <button
            className={
              activeTab === 'register'
                ? 'tab active'
                : 'tab'
            }
            onClick={() =>
              setActiveTab('register')
            }
          >
            SIGN IN
          </button>

        </div>

        <form
          className="auth-form"
          onSubmit={handleAuth}
        >

          <div className="input-group">

            <input
              type="email"
              placeholder="Enter your Email"
              value={email}
              onChange={(e) =>
                setEmail(
                  e.target.value
                )
              }
            />

          </div>

          <div className="input-group">

            <input
              type="password"
              placeholder="Enter your Password"
              value={password}
              onChange={(e) =>
                setPassword(
                  e.target.value
                )
              }
            />

          </div>

          {activeTab === 'register' && passwordValidation && (

            <div
              className={`password-strength ${passwordValidation.strength}`}
            >

              <span>
                {passwordValidation.strength.toUpperCase()}
              </span>

              <ul>

                {!passwordValidation.validations.minLength && (
                  <li>minimum 8 characters</li>
                )}

                {!passwordValidation.validations.uppercase && (
                  <li>one uppercase letter</li>
                )}

                {!passwordValidation.validations.number && (
                  <li>one number</li>
                )}

                {!passwordValidation.validations.special && (
                  <li>one special character</li>
                )}

              </ul>

            </div>

          )}

          {activeTab === 'login'
            && loginAttempts >= 3 && (

            <div
              className="forgot-password"
              onClick={
                handleResetPassword
              }
            >
              forgot password?
            </div>

          )}

          <button
            className="submit-button"
            type="submit"
          >
            {activeTab === 'login'
              ? 'INITIALIZE'
              : 'CREATE ACCOUNT'}
          </button>

          <div className="auth-divider">
            OR
          </div>

          <GoogleButton />

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

        </form>

      </div>

    </div>
  )
}