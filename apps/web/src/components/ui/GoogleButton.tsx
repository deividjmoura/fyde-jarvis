import {
  signInWithPopup,
} from 'firebase/auth'

import {
  auth,
  googleProvider,
} from '../../services/firebase'

import { useNavigate } from 'react-router-dom'

export default function GoogleButton() {

  const navigate = useNavigate()

  async function handleGoogleLogin() {

    try {

      const result = await signInWithPopup(
        auth,
        googleProvider
      )

      const token = await result.user.getIdToken()

      console.log(token)

      navigate('/home')

    } catch (error) {

      console.error(error)

    }
  }

  return (
    <button
      className="google-button"
      onClick={handleGoogleLogin}
      type="button"
    >
      Continue with Google
    </button>
  )
}