export function AnimatedBackground() {
  return (
    <div className="animated-background" aria-hidden="true">
      <video
        className="animated-background-video"
        autoPlay
        muted
        loop
        playsInline
        preload="auto"
      >
        <source
          src="/media/portfolio-background.mp4"
          type="video/mp4"
        />
      </video>

      <div className="animated-background-tint" />
      <div className="animated-background-vignette" />
    </div>
  )
}
