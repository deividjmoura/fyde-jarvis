import {
  GoogleAuthProvider,
  signInWithPopup,
} from 'firebase/auth'

import { auth } from '../../services/firebase'

import './google-button.css'

export default function GoogleButton() {

  async function handleGoogleLogin() {

    try {

      const provider =
        new GoogleAuthProvider()

      await signInWithPopup(
        auth,
        provider
      )

      window.location.href =
        '/home'

    } catch (error) {

      console.error(error)
    }
  }

  return (

    <button
      className="google-button"
      type="button"
      onClick={handleGoogleLogin}
    >

      <span className="google-icon">
        G
      </span>

      <span>
        CONTINUE WITH GOOGLE
      </span>

    </button>
  )
}