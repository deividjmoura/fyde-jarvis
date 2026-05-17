import { useEffect, useRef } from 'react'

export default function ParticleBackground() {

  const canvasRef =
    useRef<HTMLCanvasElement>(null)

  useEffect(() => {

    const canvas =
        canvasRef.current!

    const ctx = 
        canvas.getContext('2d')!

    
    let animationFrame: number

    canvas.width = window.innerWidth
    canvas.height = window.innerHeight

    const mouse = {
      x: canvas.width / 2,
      y: canvas.height / 2,
    }

    const particles: Particle[] = []

    const PARTICLE_COUNT =
      window.innerWidth < 1280
        ? 120
        : 180

    class Particle {

      x: number
      y: number

      vx: number
      vy: number

      radius: number

      constructor() {

        this.x =
          Math.random() * canvas.width

        this.y =
          Math.random() * canvas.height

        this.vx =
          (Math.random() - 0.5) * 0.6

        this.vy =
          (Math.random() - 0.5) * 0.6

        this.radius =
          Math.random() * 1.8
      }

      draw() {

        ctx.beginPath()

        ctx.fillStyle =
            'rgba(108,99,255,0.45)'
        ctx.arc(
          this.x,
          this.y,
          this.radius,
          0,
          Math.PI * 2
        )

        ctx.fill()
      }

      update() {

        if (
          this.x < 0 ||
          this.x > canvas.width
        ) {
          this.vx *= -1
        }

        if (
          this.y < 0 ||
          this.y > canvas.height
        ) {
          this.vy *= -1
        }

        this.x += this.vx
        this.y += this.vy
      }
    }

    for (
      let i = 0;
      i < PARTICLE_COUNT;
      i++
    ) {
      particles.push(new Particle())
    }

    function connectParticles() {

      for (
        let a = 0;
        a < particles.length;
        a++
      ) {

        for (
          let b = a;
          b < particles.length;
          b++
        ) {

          const dx =
            particles[a].x -
            particles[b].x

          const dy =
            particles[a].y -
            particles[b].y

          const distance =
            Math.sqrt(dx * dx + dy * dy)

          if (distance < 100) {

            const mouseDistance =
              Math.sqrt(
                (particles[a].x - mouse.x) ** 2 +
                (particles[a].y - mouse.y) ** 2
              )

            if (mouseDistance < 260) {

            ctx.beginPath()

            ctx.strokeStyle =
                `rgba(108,99,255,${
                0.28 - distance / 850
                })`

            ctx.lineWidth = 1

              ctx.moveTo(
                particles[a].x,
                particles[a].y
              )

              ctx.lineTo(
                particles[b].x,
                particles[b].y
              )

              ctx.stroke()
            }
          }
        }
      }
    }

    function animate() {

      ctx.clearRect(
        0,
        0,
        canvas.width,
        canvas.height
      )

      particles.forEach((particle) => {
        particle.update()
        particle.draw()
      })

      connectParticles()

      animationFrame =
        requestAnimationFrame(animate)
    }

    animate()

    window.addEventListener(
      'mousemove',
      (event) => {

        mouse.x = event.clientX
        mouse.y = event.clientY
      }
    )

    return () => {

      cancelAnimationFrame(
        animationFrame
      )
    }

  }, [])

  return (
    <canvas
      id="login-background"
      ref={canvasRef}
      className="particle-background"
    />
  )
}