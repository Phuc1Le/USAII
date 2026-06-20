import { useMemo, type CSSProperties } from "react"

type Star = {
  id: number
  left: string
  top: string
  size: number
  delay: string
  duration: string
  driftX: number
  driftY: number
}

export default function Starfield() {
  const stars = useMemo<Star[]>(
    () =>
      Array.from({ length: 48 }, (_, i) => ({
        id: i,
        left: `${(i * 17 + 5) % 96 + 2}%`,
        top: `${(i * 29 + 13) % 94 + 3}%`,
        size: 10 + (i % 6) * 4,
        delay: `${(i % 9) * 0.55}s`,
        duration: `${10 + (i % 7) * 2.5}s`,
        driftX: -60 - (i % 5) * 28,
        driftY: -90 - (i % 6) * 32,
      })),
    [],
  )

  return (
    <div className="starfield" aria-hidden="true">
      {stars.map((star) => (
        <span
          key={star.id}
          className={`starfield-star${star.size >= 22 ? " starfield-star-lg" : ""}`}
          style={
            {
              left: star.left,
              top: star.top,
              width: star.size,
              height: star.size,
              animationDelay: star.delay,
              animationDuration: star.duration,
              "--drift-x": `${star.driftX}px`,
              "--drift-y": `${star.driftY}px`,
            } as CSSProperties
          }
        />
      ))}
    </div>
  )
}
