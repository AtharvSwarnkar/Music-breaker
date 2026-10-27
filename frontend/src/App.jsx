
import React, { useEffect, useRef, useState } from 'react'
import {
  Activity,
  AudioLines,
  ChevronDown,
  CircleHelp,
  Disc3,
  Download,
  FileAudio,
  Headphones,
  Layers3,
  Music2,
  Pause,
  Play,
  Radio,
  RefreshCw,
  Settings2,
  Sparkles,
  Upload,
  Volume2,
  Waves,
  X,
} from 'lucide-react'

import { analyzeAudio, apiBase } from './lib/api'
import {
  formatTime,
  makeWaveform,
  normalizeAnalysis,
} from './lib/audio'

const COLORS = ['#D65336', '#E8E1D2', '#252823']

const demoPoints = Array.from({ length: 44 }, (_, i) => ({
  second: i,
  Drums:
    i % 7 === 0
      ? 0.08
      : Math.max(
          0,
          Math.sin(i * 0.72) * 0.42 +
            Math.sin(i * 0.19) * 0.2
        ),
  Bass: Math.max(0, Math.sin(i * 0.29 + 1) * 0.36),
  Guitar: Math.max(0, Math.sin(i * 0.15 + 2) * 0.24),
  Vocals: Math.max(0, Math.sin(i * 0.2 + 3) * 0.45),
  Piano: Math.max(0, Math.sin(i * 0.37 + 4) * 0.19),
}))

const demoAnalysis = {
  points: demoPoints,
  instruments: ['Drums', 'Bass', 'Guitar', 'Vocals', 'Piano'],
  summary: {
    Drums: 28,
    Bass: 24,
    Guitar: 18,
    Vocals: 17,
    Piano: 13,
  },
  duration: 214,
  metadata: {
    title: 'Midnight City',
    artist: 'Demo track',
  },
}

function prettyName(value = '') {
  return value
    .replace(/[_-]/g, ' ')
    .replace(/\b\w/g, (character) => character.toUpperCase())
}

function formatIndex(value) {
  const score = Number(value)

  if (!Number.isFinite(score)) {
    return '—'
  }

  return `${score.toFixed(1)}/100`
}

function Waveform({ values, progress, onSeek }) {
  const bars = values?.length
    ? values
    : Array.from(
        { length: 160 },
        (_, i) =>
          0.12 +
          Math.abs(Math.sin(i * 0.41) * Math.cos(i * 0.07)) *
            0.55
      )

  return (
    <div
      className="waveform"
      onClick={(event) => {
        const rect = event.currentTarget.getBoundingClientRect()
        const fraction = (event.clientX - rect.left) / rect.width

        onSeek?.(Math.max(0, Math.min(1, fraction)))
      }}
      role="slider"
      aria-label="Audio timeline"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={Math.round(progress * 100)}
      tabIndex={0}
    >
      {bars.map((value, index) => (
        <span
          key={index}
          style={{
            height: `${Math.max(7, value * 100)}%`,
            background:
              index / bars.length <= progress
                ? '#D65336'
                : 'rgba(37,40,35,.24)',
          }}
        />
      ))}

      <i
        className="playhead"
        style={{ left: `${progress * 100}%` }}
      />
    </div>
  )
}

function Stat({ label, value, sub, icon: Icon }) {
  return (
    <div className="stat glass">
      <div className="stat-icon">
        <Icon size={17} />
      </div>

      <div>
        <div className="stat-label">{label}</div>
        <div className="stat-value">{value}</div>
        <div className="stat-sub">{sub}</div>
      </div>
    </div>
  )
}

export default function App() {
  const [file, setFile] = useState(null)
  const [audioUrl, setAudioUrl] = useState('')
  const [wave, setWave] = useState([])
  const [duration, setDuration] = useState(0)

  const [analysis, setAnalysis] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [status, setStatus] = useState('')

  const [playing, setPlaying] = useState(false)
  const [current, setCurrent] = useState(0)
  const [apiOpen, setApiOpen] = useState(false)

  const audioRef = useRef(null)
  const inputRef = useRef(null)

  const view = analysis || demoAnalysis;
  const instruments = view.instruments || [];
  const summary = view.summary || {};
  const points = Array.isArray(view.points) ? view.points : [];
  
  // Read the song-level aggregate only.
  // Never substitute a single frame's score for a missing song score.
  const progress = duration > 0 ? current / duration : 0

  const ranked = instruments
    .map((name, index) => {
      const normalizeName = (value) =>
        String(value).toLowerCase().replace(/[_-]/g, ' ').trim()

      const matchingKey = Object.keys(summary).find(
        (key) => normalizeName(key) === normalizeName(name)
      )

      if (matchingKey === undefined) {
        return null
      }

      const value = Number(summary[matchingKey])

      if (!Number.isFinite(value)) {
        return null
      }

      return {
        name,
        value,
        color: COLORS[index % COLORS.length],
      }
    })
    .filter(Boolean)
    .sort((a, b) => b.value - a.value)

  const handleFile = async (selectedFile) => {
    if (!selectedFile) return

    const validAudio =
      /^audio\//i.test(selectedFile.type) ||
      /\.(mp3|wav|flac|m4a|ogg)$/i.test(selectedFile.name)

    if (!validAudio) {
      setError('Choose an audio file (MP3, WAV, FLAC, M4A or OGG).')
      return
    }

    setError('')
    setFile(selectedFile)
    setAnalysis(null)
    setCurrent(0)
    setPlaying(false)
    setStatus('')

    const url = URL.createObjectURL(selectedFile)
    setAudioUrl(url)

    try {
      const waveform = await makeWaveform(selectedFile)
      setWave(waveform.values)
      setDuration(waveform.duration)
    } catch {
      setWave([])
      setDuration(0)
    }
  }

  const runAnalysis = async () => {
    if (!file) {
      inputRef.current?.click()
      return
    }

    setBusy(true)
    setError('')
    setStatus('Starting analysis...')

    try {
      const raw = await analyzeAudio(file, setStatus)
      const normalized = normalizeAnalysis(raw, duration)

      if (!normalized.instruments?.length) {
        throw new Error(
          'No instrument scores were found in the backend response. ' +
          'Check normalizeAnalysis() in src/lib/audio.js.'
        )
      }

      if (
        !normalized.summary ||
        Object.keys(normalized.summary).length === 0
      ) {
        throw new Error(
          'No song-level scores were returned. ' +
          'The backend must provide song_level_scores or an equivalent aggregate.'
        )
      }

      setAnalysis(normalized)
      setStatus('Analysis complete')
    } catch (exception) {
      setError(
        `${exception.message || 'Analysis failed'}. Backend: ${apiBase()}`
      )
      setStatus('Analysis failed')
    } finally {
      setBusy(false)
    }
  }

  const togglePlay = async () => {
    if (!audioRef.current) {
      setError('Upload an audio file to play it.')
      return
    }

    if (audioRef.current.paused) {
      try {
        await audioRef.current.play()
      } catch {
        setError('The audio could not be played by your browser.')
      }
    } else {
      audioRef.current.pause()
    }
  }

  const seek = (fraction) => {
    const audio = audioRef.current

    if (audio && Number.isFinite(audio.duration)) {
      audio.currentTime = fraction * audio.duration
    }
  }

  const downloadJSON = () => {
    const data = analysis?.raw || {
      demo: true,
      points,
      summary,
    }

    const blob = new Blob(
      [JSON.stringify(data, null, 2)],
      { type: 'application/json' }
    )

    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')

    anchor.href = url
    anchor.download = 'sonora-analysis.json'
    anchor.click()

    URL.revokeObjectURL(url)
  }

  useEffect(() => {
    const audio = audioRef.current

    if (!audio) return

    const updateTime = () => setCurrent(audio.currentTime || 0)
    const handlePlay = () => setPlaying(true)
    const handlePause = () => setPlaying(false)

    audio.addEventListener('timeupdate', updateTime)
    audio.addEventListener('play', handlePlay)
    audio.addEventListener('pause', handlePause)
    audio.addEventListener('ended', handlePause)

    return () => {
      audio.removeEventListener('timeupdate', updateTime)
      audio.removeEventListener('play', handlePlay)
      audio.removeEventListener('pause', handlePause)
      audio.removeEventListener('ended', handlePause)
    }
  }, [audioUrl])

  useEffect(() => {
    return () => {
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl)
      }
    }
  }, [audioUrl])

  return (
    <div className="app-shell">
      <aside className="sidebar glass">
        <div className="brand">
          <div className="brand-mark">
            <AudioLines size={22} />
          </div>

          <div>
            <strong>SONORA</strong>
            <small>MUSIC INTELLIGENCE</small>
          </div>
        </div>

        <div className="side-label">WORKSPACE</div>

        <button className="nav-item active">
          <Activity size={17} />
          Analysis studio
          <span className="nav-dot" />
        </button>

        <button
          className="nav-item"
          onClick={() => inputRef.current?.click()}
        >
          <Layers3 size={17} />
          Import audio
        </button>

        <div className="side-label side-label-gap">YOUR LIBRARY</div>

        <div className="library-empty">
          <div className="tiny-disc">
            <Disc3 size={20} />
          </div>
          <span>Your tracks appear here</span>
          <small>Upload a song to get started</small>
        </div>

        <div className="sidebar-bottom">
          <div className="connection">
            <span className="connection-dot" />

            <div>
              <strong>API connection</strong>
              <small>{apiBase().replace(/^https?:\/\//, '')}</small>
            </div>

            <button
              title="API details"
              onClick={() => setApiOpen(!apiOpen)}
            >
              <Settings2 size={16} />
            </button>
          </div>

          {apiOpen && (
            <div className="api-hint">
              Set <code>VITE_API_BASE_URL</code> and{' '}
              <code>VITE_ANALYZE_ENDPOINT</code> in <code>.env</code>.
              See README.
            </div>
          )}

          <div className="profile">
            <div className="avatar">S</div>
            <div>
              <strong>Studio workspace</strong>
              <small>Local analysis</small>
            </div>
            <ChevronDown size={16} />
          </div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div className="crumb">
            Workspace <span>/</span> <b>Analysis studio</b>
          </div>

          <div className="top-actions">
            <span className={`live-pill ${analysis ? 'connected' : ''}`}>
              <i />
              {analysis ? 'Analysis ready' : 'Interactive preview'}
            </span>

            <button
              className="icon-button"
              title="Help"
              onClick={() => setApiOpen(!apiOpen)}
            >
              <CircleHelp size={18} />
            </button>

            <button className="avatar mini">AS</button>
          </div>
        </header>

        <section className="welcome">
          <div>
            <div className="eyebrow">
              <Sparkles size={13} />
              SONIC FIELDNOTES / 001
            </div>

            <h1>
              Listen beneath
              <br />
              <span>the surface.</span>
            </h1>

            <p>
              Explore the instruments detected throughout an entire song
              and compare their overall model-match scores.
            </p>
          </div>

          <div className="welcome-orb">
            <div className="orb-ring ring-a" />
            <div className="orb-ring ring-b" />
            <AudioLines size={48} />
            <div className="orb-caption">
              SOUND
              <br />
              STUDY
            </div>
          </div>
        </section>

        <section className="upload-card glass">
          <div className="upload-copy">
            <div className="upload-icon">
              <Upload size={20} />
            </div>

            <div>
              <h3>{file ? file.name : 'Bring a track into focus'}</h3>
              <p>
                {file
                  ? `${(file.size / 1024 / 1024).toFixed(2)} MB · ${
                      duration ? formatTime(duration) : 'Audio loaded'
                    }`
                  : 'Drop an audio file here, or browse your device.'}
              </p>
            </div>
          </div>

          <div className="upload-actions">
            <input
              ref={inputRef}
              type="file"
              accept="audio/*,.mp3,.wav,.flac,.m4a,.ogg"
              hidden
              onChange={(event) => handleFile(event.target.files?.[0])}
            />

            <button
              className="button-secondary"
              onClick={() => inputRef.current?.click()}
            >
              <FileAudio size={16} />
              Browse files
            </button>

            <button
              className="button-primary"
              disabled={busy || !file}
              onClick={runAnalysis}
            >
              {busy ? (
                <RefreshCw size={16} className="spin" />
              ) : (
                <Sparkles size={16} />
              )}
              {busy ? 'Analyzing…' : 'Analyze track'}
            </button>
          </div>

          <div className="supported">
            MP3 <span /> WAV <span /> FLAC <span /> M4A <span /> OGG
          </div>
        </section>

        {error && (
          <div className="error-banner">
            <X size={17} />

            <div>
              <strong>Couldn’t finish analysis</strong>
              <p>{error}</p>
            </div>

            <button onClick={() => setError('')}>
              <X size={16} />
            </button>
          </div>
        )}

        {busy && (
          <div className="status-banner">
            <RefreshCw className="spin" size={16} />
            {status || 'Working on your track…'}
          </div>
        )}

        <div className="section-heading">
          <div>
            <div className="section-kicker">01 / OVERVIEW</div>
            <h2>Track at a glance</h2>
          </div>

          <button className="subtle-button" onClick={downloadJSON}>
            <Download size={15} />
            Export data
          </button>
        </div>

        <section className="stats-grid">
          <Stat
            label="TRACK LENGTH"
            value={formatTime(duration || view.duration)}
            sub={file ? 'Uploaded audio' : 'Illustrative preview'}
            icon={Headphones}
          />

          <Stat
            label="INSTRUMENTS ANALYZED"
            value={instruments.length.toString().padStart(2, '0')}
            sub="Instrument categories"
            icon={Music2}
          />

          <Stat
            label="ANALYSIS SCOPE"
            value="Full song"
            sub="Aggregated audio evidence"
            icon={Activity}
          />

          <Stat
            label="ANALYSIS STATUS"
            value={analysis ? 'Ready' : file ? 'Pending' : 'Preview'}
            sub={
              analysis
                ? 'Backend response received'
                : file
                  ? 'Ready to analyze'
                  : 'Sample data shown'
            }
            icon={Radio}
          />
        </section>

        <section className="glass timeline-card">
          <div className="card-heading">
            <div>
              <div className="section-kicker">02 / PLAYBACK</div>
              <h2>Song timeline</h2>
            </div>

            <div className="timeline-right">
              <span className="timecode">
                {formatTime(current)}
                {' '}
                <i>/</i>
                {' '}
                {formatTime(duration || view.duration)}
              </span>

              <button
                className="play-button"
                onClick={togglePlay}
                title={playing ? 'Pause' : 'Play'}
              >
                {playing ? (
                  <Pause size={18} fill="currentColor" />
                ) : (
                  <Play size={18} fill="currentColor" />
                )}
              </button>
            </div>
          </div>

          <div className="track-meta">
            <div className="cover-art">
              <Waves size={25} />
            </div>

            <div className="track-title">
              <strong>
                {file?.name?.replace(/\.[^/.]+$/, '') ||
                  view.metadata?.title ||
                  'Midnight City'}
              </strong>

              <small>
                {file
                  ? 'Local audio file'
                  : view.metadata?.artist ||
                    'Sample track · interactive preview'}
              </small>
            </div>

            <div className="wave-label">
              <span className="wave-led" />
              {analysis ? 'ANALYZED TRACK' : 'PREVIEW TRACK'}
            </div>
          </div>

          <Waveform
            values={wave}
            progress={progress}
            onSeek={seek}
          />

          <div className="timeline-axis">
            <span>0:00</span>
            <span>{formatTime((duration || view.duration) * 0.25)}</span>
            <span>{formatTime((duration || view.duration) * 0.5)}</span>
            <span>{formatTime((duration || view.duration) * 0.75)}</span>
            <span>{formatTime(duration || view.duration)}</span>
          </div>

          <div className="player-controls">
            <button
              onClick={togglePlay}
              className="play-inline"
            >
              {playing ? <Pause size={14} /> : <Play size={14} />}
              {playing ? 'Pause' : 'Play track'}
            </button>

            <div className="player-note">
              <Volume2 size={14} />
              Audio preview uses the uploaded file
            </div>

            <span className="volume-dots">
              <i />
              <i />
              <i />
              <i />
              <i />
            </span>
          </div>

          {audioUrl && (
            <audio
              ref={audioRef}
              src={audioUrl}
              preload="metadata"
            />
          )}
        </section>

        <div className="section-heading">
          <div>
            <div className="section-kicker">03 / WHOLE SONG</div>
            <h2>Overall instrument analysis</h2>
            <p>
              One aggregated score per instrument across the entire song.
            </p>
          </div>

          <span className="small-chip">SONG SUMMARY</span>
        </div>

        <section className="glass contribution-card">
          <div className="card-heading compact">
            <div>
              <div className="section-kicker">SONG-LEVEL RESULTS</div>
              <h2>Instrument Match Index</h2>
            </div>

            <span className="small-chip">0–100 SCALE</span>
          </div>

          <p className="insight-intro">
            This index summarizes the average adjusted CLAP similarity
            score across the analyzed song, scaled to 0–100. Higher
            scores indicate stronger overall model matches. These values
            are not probabilities, calibrated confidence levels, or
            physical instrument contribution percentages.
          </p>

          {ranked.length > 0 ? (
            <div className="contribution-list">
              {ranked.map((item) => (
                <div
                  className="contribution-row"
                  key={item.name}
                >
                  <div className="contribution-name">
                    <i style={{ background: item.color }} />
                    {prettyName(item.name)}
                  </div>

                  <div className="contribution-track">
                    <span
                      style={{
                        width: `${Math.max(
                          0,
                          Math.min(100, item.value)
                        )}%`,
                        background: item.color,
                      }}
                    />
                  </div>

                  <strong>{formatIndex(item.value)}</strong>
                </div>
              ))}
            </div>
          ) : (
            <p className="insight-intro">
              No song-level scores were returned. Check that the backend
              returns the song_level_scores field and that
              normalizeAnalysis() in src/lib/audio.js maps it to summary.
            </p>
          )}

          <small className="footnote">
            Scores are independent and do not need to add up to 100.
            They should not be interpreted as probabilities or percentages
            of the song's total sound.
          </small>
        </section>

        <footer>
          <div className="footer-brand">
            <AudioLines size={15} />
            SONORA <span>·</span> Music intelligence workspace
          </div>

          <span>Built for listening closer.</span>
        </footer>
      </main>
    </div>
  )
}
