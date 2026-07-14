/** Win / lose modal shown over the board when a round ends. */
export default function Overlay({ status, level, onNext, onRestart }) {
  if (status !== 'won' && status !== 'lost') return null

  const won = status === 'won'
  return (
    <div className="overlay" role="dialog" aria-modal="true">
      <div className="overlay__card">
        <div className="overlay__emoji" aria-hidden="true">
          {won ? '🎉' : '💥'}
        </div>
        <h2 className="overlay__title">
          {won ? 'Level Cleared!' : 'Out of Lives'}
        </h2>
        <p className="overlay__text">
          {won
            ? `You cleared level ${level}.`
            : `Level ${level} beat you this time.`}
        </p>
        {won ? (
          <button className="btn btn--primary" onClick={onNext}>
            Next Level →
          </button>
        ) : (
          <button className="btn btn--primary" onClick={onRestart}>
            Try Again
          </button>
        )}
      </div>
    </div>
  )
}
