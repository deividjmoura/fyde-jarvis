import {
  signInWithPopup,
} from 'firebase/auth'

import {
  auth,
  googleProvider,
} from '../../services/firebase'

export default function GoogleButton() {

  async function handleGoogleLogin() {

    try {

      const result =
        await signInWithPopup(
          auth,
          googleProvider
        )

      console.log(result.user)

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