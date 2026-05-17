import { InputHTMLAttributes } from 'react'

interface Props extends InputHTMLAttributes<HTMLInputElement> {
  label: string
}

export default function CyberInput({
  label,
  ...props
}: Props) {

  return (
    <div className="cyber-input-wrapper">

      <label>
        {label}
      </label>

      <div className="cyber-input-box">

        <div className="cyber-line"></div>

        <input {...props} />

      </div>

    </div>
  )
}