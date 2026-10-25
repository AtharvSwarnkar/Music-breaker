import React, { useEffect, useMemo, useRef, useState } from 'react'
import { Activity, AudioLines, Check, ChevronDown, CircleHelp, Disc3, Download, FileAudio, Headphones, Layers3, Music2, Pause, Play, Radio, RefreshCw, Search, Settings2, Sparkles, Upload, Volume2, Waves, X } from 'lucide-react'
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis, CartesianGrid } from 'recharts'
import { analyzeAudio, apiBase } from './lib/api'
import { formatTime, makeWaveform, normalizeAnalysis } from './lib/audio'

const COLORS = ['#D65336','#E8E1D2','#252823']
const demoPoints = Array.from({length: 44}, (_,i) => ({second:i, Drums: i%7===0?.08:Math.max(0,Math.sin(i*.72)*.42+Math.sin(i*.19)*.2), Bass:Math.max(0,Math.sin(i*.29+1)*.36), Guitar:Math.max(0,Math.sin(i*.15+2)*.24), Vocals:Math.max(0,Math.sin(i*.2+3)*.45), Piano:Math.max(0,Math.sin(i*.37+4)*.19)}))
const demoAnalysis = {points:demoPoints,instruments:['Drums','Bass','Guitar','Vocals','Piano'],summary:{Drums:28,Bass:24,Guitar:18,Vocals:17,Piano:13},duration:214,metadata:{title:'Midnight City',artist:'Demo track'}}
function prettyName(s='') { return s.replace(/[_-]/g,' ').replace(/\b\w/g,c=>c.toUpperCase()) }
function pct(v) { const n=Number(v||0); return `${(n<=1?n*100:n).toFixed(0)}%` }

function Waveform({values, progress, onSeek}) {
  const bars = values?.length ? values : Array.from({length:160},(_,i)=>.12+Math.abs(Math.sin(i*.41)*Math.cos(i*.07))*.55)
  return <div className="waveform" onClick={e=>{const r=e.currentTarget.getBoundingClientRect();onSeek?.(Math.max(0,Math.min(1,(e.clientX-r.left)/r.width)))}} role="slider" aria-label="Audio timeline" tabIndex="0">
    {bars.map((v,i)=><span key={i} style={{height:`${Math.max(7,v*100)}%`,background:(i/bars.length)<=progress?'#D65336':'rgba(37,40,35,.24)'}} />)}
    <i className="playhead" style={{left:`${progress*100}%`}}/>
  </div>
}
function Stat({label,value,sub,icon:Icon}) { return <div className="stat glass"><div className="stat-icon"><Icon size={17}/></div><div><div className="stat-label">{label}</div><div className="stat-value">{value}</div><div className="stat-sub">{sub}</div></div></div> }

export default function App() {
  const [file,setFile]=useState(null), [audioUrl,setAudioUrl]=useState(''), [wave,setWave]=useState([]), [duration,setDuration]=useState(0)
  const [analysis,setAnalysis]=useState(null), [busy,setBusy]=useState(false), [error,setError]=useState(''), [status,setStatus]=useState('')
  const [playing,setPlaying]=useState(false), [current,setCurrent]=useState(0), [active,setActive]=useState('All instruments'), [threshold,setThreshold]=useState(0.5)
  const [demo,setDemo]=useState(true)
  const [apiOpen,setApiOpen]=useState(false)
  const audioRef=useRef(null), inputRef=useRef(null)
  const view = analysis || demoAnalysis
  const points = view.points || []
  const instruments = view.instruments || []
  const progress = duration ? current/duration : 0
  const visibleInstruments = active==='All instruments' ? instruments : instruments.filter(x=>x===active)
  const currentPoint = points.reduce((prev,p)=>Math.abs(p.second-Math.floor(current))<Math.abs(prev.second-Math.floor(current))?p:prev,points[0]||{second:0})
  const activeLevel = visibleInstruments.reduce((sum,k)=>sum+(Number(currentPoint[k])||0),0)
  const dominantPoints = useMemo(() => points.map(point => {
    const candidates = (active === 'All instruments' ? instruments : instruments.filter(name => name === active))
      .map(name => ({ name, score: Number(point[name]) || 0 }))
      .sort((a,b) => b.score-a.score)
    const top = candidates[0]
    return { second: point.second, dominantScore: top && top.score >= threshold ? top.score : null, dominantInstrument: top && top.score >= threshold ? top.name : 'No instrument above benchmark' }
  }), [points, instruments, active, threshold])
  const currentDominant = useMemo(() => {
    const candidates = (active === 'All instruments' ? instruments : instruments.filter(name => name === active)).map(name => ({name, score:Number(currentPoint[name])||0})).sort((a,b)=>b.score-a.score)
    return candidates[0] && candidates[0].score >= threshold ? candidates[0] : null
  }, [instruments, active, currentPoint, threshold])
  useEffect(()=>{ if(!audioRef.current)return; const el=audioRef.current; const tick=()=>setCurrent(el.currentTime||0); const play=()=>setPlaying(true); const pause=()=>setPlaying(false); el.addEventListener('timeupdate',tick);el.addEventListener('play',play);el.addEventListener('pause',pause);el.addEventListener('ended',pause);return()=>{el.removeEventListener('timeupdate',tick);el.removeEventListener('play',play);el.removeEventListener('pause',pause);el.removeEventListener('ended',pause)}},[audioUrl])
  useEffect(()=>()=>{if(audioUrl)URL.revokeObjectURL(audioUrl)},[audioUrl])
  const handleFile = async f => {
    if(!f)return
    if(!/^audio\/|\.mp3$|\.wav$|\.flac$|\.m4a$|\.ogg$/i.test(f.type+' '+f.name)){setError('Choose an audio file (MP3, WAV, FLAC, M4A or OGG).');return}
    setError('');setFile(f);setAnalysis(null);setDemo(false);setCurrent(0)
    const url=URL.createObjectURL(f);setAudioUrl(url)
    try { const w=await makeWaveform(f);setWave(w.values);setDuration(w.duration) } catch { setWave([]);setDuration(0) }
  }
  const runAnalysis = async () => {
    if(!file){inputRef.current?.click();return}
    setBusy(true);setError('')
    try {
      const raw=await analyzeAudio(file,setStatus)
      const normalized=normalizeAnalysis(raw,duration)
      if(!normalized.instruments.length) throw new Error('The backend responded, but no per-second instrument scores were found. Check the response shape in README.md and adapt normalizeAnalysis() in src/lib/audio.js.')
      setAnalysis(normalized);setStatus('Analysis complete')
    } catch(e) { setError(`${e.message}. Backend: ${apiBase()}`);setStatus('Analysis failed') }
    finally {setBusy(false)}
  }
  const togglePlay = async()=>{if(!audioRef.current){setError('Upload an audio file to play it.');return} if(audioRef.current.paused) await audioRef.current.play();else audioRef.current.pause()}
  const seek = fraction => {if(audioRef.current && Number.isFinite(audioRef.current.duration))audioRef.current.currentTime=fraction*audioRef.current.duration}
  const downloadJSON=()=>{const blob=new Blob([JSON.stringify(analysis?.raw||{demo:true,points},null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='sonora-analysis.json';a.click();URL.revokeObjectURL(url)}
  const summary = view.summary || {}
  const ranked = [...instruments].map((name,i)=>({name,value:summary[name]??summary[name.toLowerCase()]??Math.max(0,...points.map(p=>p[name]||0)),color:COLORS[i%COLORS.length]})).sort((a,b)=>Number(b.value)-Number(a.value))
  return <div className="app-shell">
    
    <aside className="sidebar glass">
      <div className="brand"><div className="brand-mark"><AudioLines size={22}/></div><div><strong>SONORA</strong><small>MUSIC INTELLIGENCE</small></div></div>
      <div className="side-label">WORKSPACE</div>
      <button className="nav-item active"><Activity size={17}/> Analysis studio <span className="nav-dot"/></button>
      <button className="nav-item" onClick={()=>inputRef.current?.click()}><Layers3 size={17}/> Import audio</button>
      <div className="side-label side-label-gap">YOUR LIBRARY</div>
      <div className="library-empty"><div className="tiny-disc"><Disc3 size={20}/></div><span>Your tracks appear here</span><small>Upload a song to get started</small></div>
      <div className="sidebar-bottom"><div className="connection"><span className="connection-dot"/><div><strong>API connection</strong><small>{apiBase().replace(/^https?:\/\//,'')}</small></div><button title="API details" onClick={()=>setApiOpen(!apiOpen)}><Settings2 size={16}/></button></div>{apiOpen&&<div className="api-hint">Set <code>VITE_API_BASE_URL</code> and <code>VITE_ANALYZE_ENDPOINT</code> in <code>.env</code>. See README.</div>}<div className="profile"><div className="avatar">S</div><div><strong>Studio workspace</strong><small>Local analysis</small></div><ChevronDown size={16}/></div></div>
    </aside>
    <main className="main-content">
      <header className="topbar"><div className="crumb">Workspace <span>/</span> <b>Analysis studio</b></div><div className="top-actions"><span className={`live-pill ${analysis?'connected':''}`}><i/>{analysis?'Analysis ready':'Interactive preview'}</span><button className="icon-button" title="Help" onClick={()=>setApiOpen(!apiOpen)}><CircleHelp size={18}/></button><button className="avatar mini">AS</button></div></header>
      <section className="welcome"><div><div className="eyebrow"><Sparkles size={13}/> SONIC FIELDNOTES / 001</div><h1>Listen beneath<br/><span>the surface.</span></h1><p>Explore instrument activity, second by second. A frame-by-frame reading of the sounds inside a track.</p></div><div className="welcome-orb"><div className="orb-ring ring-a"/><div className="orb-ring ring-b"/><AudioLines size={48}/><div className="orb-caption">SOUND<br/>STUDY</div></div></section>
      <section className="upload-card glass"><div className="upload-copy"><div className="upload-icon"><Upload size={20}/></div><div><h3>{file?file.name:'Bring a track into focus'}</h3><p>{file?`${(file.size/1024/1024).toFixed(2)} MB · ${duration?formatTime(duration):'Audio loaded'}`:'Drop an audio file here, or browse your device.'}</p></div></div><div className="upload-actions"><input ref={inputRef} type="file" accept="audio/*,.mp3,.wav,.flac" hidden onChange={e=>handleFile(e.target.files?.[0])}/><button className="button-secondary" onClick={()=>inputRef.current?.click()}><FileAudio size={16}/> Browse files</button><button className="button-primary" disabled={busy||!file} onClick={runAnalysis}>{busy?<RefreshCw size={16} className="spin"/>:<Sparkles size={16}/>} {busy?'Analyzing…':'Analyze track'}</button></div><div className="supported">MP3 <span/> WAV <span/> FLAC <span/> M4A</div></section>
      {error&&<div className="error-banner"><X size={17}/><div><strong>Couldn’t finish analysis</strong><p>{error}</p></div><button onClick={()=>setError('')}><X size={16}/></button></div>}
      {busy&&<div className="status-banner"><RefreshCw className="spin" size={16}/>{status||'Working on your track…'}</div>}
      <div className="section-heading"><div><div className="section-kicker">01 / OVERVIEW</div><h2>Track at a glance</h2></div><button className="subtle-button" onClick={downloadJSON}><Download size={15}/> Export data</button></div>
      <section className="stats-grid">
        <Stat label="TRACK LENGTH" value={formatTime(duration||view.duration)} sub={file?'Uploaded audio':'Illustrative preview'} icon={Headphones}/>
        <Stat label="INSTRUMENTS FOUND" value={instruments.length.toString().padStart(2,'0')} sub="Non-zero activity only" icon={Music2}/>
        <Stat label="TIME RESOLUTION" value="1 sec" sub="Per-frame instrument scores" icon={Activity}/>
        <Stat label="ANALYSIS STATUS" value={analysis?'Ready':demo?'Preview':'Pending'} sub={analysis?'Backend response received':demo?'Sample data shown':'Upload to begin'} icon={Radio}/>
      </section>
      <section className="glass timeline-card">
        <div className="card-heading"><div><div className="section-kicker">02 / PLAYBACK</div><h2>Song timeline</h2></div><div className="timeline-right"><span className="timecode">{formatTime(current)} <i>/</i> {formatTime(duration||view.duration)}</span><button className="play-button" onClick={togglePlay} title={playing?'Pause':'Play'}>{playing?<Pause size={18} fill="currentColor"/>:<Play size={18} fill="currentColor"/>}</button></div></div>
        <div className="track-meta"><div className="cover-art"><Waves size={25}/></div><div className="track-title"><strong>{file?.name?.replace(/\.[^/.]+$/,'')||view.metadata?.title||'Midnight City'}</strong><small>{file?'Local audio file':view.metadata?.artist||'Sample track · interactive preview'}</small></div><div className="wave-label"><span className="wave-led"/>{analysis?'ANALYZED TRACK':'PREVIEW TRACK'}</div></div>
        <Waveform values={wave} progress={progress} onSeek={seek}/>
        <div className="timeline-axis"><span>0:00</span><span>{formatTime((duration||view.duration)*.25)}</span><span>{formatTime((duration||view.duration)*.5)}</span><span>{formatTime((duration||view.duration)*.75)}</span><span>{formatTime(duration||view.duration)}</span></div>
        <div className="player-controls"><button onClick={togglePlay} className="play-inline">{playing?<Pause size={14}/>:<Play size={14}/>} {playing?'Pause':'Play track'}</button><div className="player-note"><Volume2 size={14}/> Audio preview uses the uploaded file</div><span className="volume-dots"><i/><i/><i/><i/><i/></span></div>
        {audioUrl&&<audio ref={audioRef} src={audioUrl} preload="metadata"/>}
      </section>
      <div className="section-heading graph-heading"><div><div className="section-kicker">03 / FRAME ANALYSIS</div><h2>Dominant instrument, frame by frame</h2><p>Each frame shows only its highest-scoring instrument when it clears the benchmark.</p></div><div className="filter-wrap"><Search size={15}/><select value={active} onChange={e=>setActive(e.target.value)}><option>All instruments</option>{instruments.map(k=><option key={k}>{k}</option>)}</select></div></div>
      <section className="glass chart-card">
        <div className="chart-top"><div><strong>Dominant instrument activity</strong><small>Only scores at or above the benchmark are shown</small></div><label className="benchmark-control">Benchmark <b>{Math.round(threshold*100)}%</b><input aria-label="Dominance benchmark" type="range" min="0.05" max="0.95" step="0.05" value={threshold} onChange={e=>setThreshold(Number(e.target.value))}/></label></div>
        <div className="main-chart">
          <ResponsiveContainer width="100%" height="100%"><LineChart data={dominantPoints} margin={{top:12,right:14,bottom:0,left:0}}>
            <CartesianGrid stroke="rgba(37,40,35,.14)" vertical={false}/>
            <XAxis dataKey="second" tickFormatter={v=>formatTime(v)} stroke="#77766D" tickLine={false} axisLine={false} tick={{fontSize:10}} minTickGap={45}/>
            <YAxis domain={[0,1]} tickFormatter={v=>`${Math.round(v*100)}%`} stroke="#77766D" tickLine={false} axisLine={false} tick={{fontSize:10}} width={38}/>
            <Tooltip content={({active:tipActive,payload,label})=>{if(!tipActive||!payload?.length)return null;const point=payload[0].payload;return <div className="chart-tooltip"><strong>{formatTime(Number(label)||0)}</strong><div>{point.dominantInstrument}</div><small>{point.dominantScore==null?'Below benchmark':`${Math.round(point.dominantScore*100)}% score`}</small></div>}}/>
            <Line type="stepAfter" dataKey="dominantScore" name="Dominant score" stroke="#D65336" strokeWidth={3} dot={false} activeDot={{r:5,strokeWidth:0}} connectNulls={false} isAnimationActive={false}/>
          </LineChart></ResponsiveContainer>
        </div>
        {!analysis&&<div className="preview-note"><Sparkles size={14}/> Sample visualisation — upload a song and run analysis to replace this with backend results.</div>}
        {analysis&&<div className="preview-note success-note"><Check size={14}/> Live backend data loaded · {points.length} one-second frames mapped</div>}
      </section>
      <section className="lower-grid">
        <div className="glass contribution-card"><div className="card-heading compact"><div><div className="section-kicker">04 / MIX PROFILE</div><h2>Instrument contribution</h2></div><span className="small-chip">SUMMARY</span></div><div className="contribution-list">{ranked.slice(0,6).map((item,i)=><div className="contribution-row" key={item.name}><div className="contribution-name"><i style={{background:item.color}}/>{prettyName(item.name)}</div><div className="contribution-track"><span style={{width:`${Math.max(0,Math.min(100,Number(item.value)>1?Number(item.value):Number(item.value)*100))}%`,background:item.color}}/></div><strong>{pct(item.value)}</strong></div>)}</div><small className="footnote">Contribution values are shown as returned by the analysis, when available.</small></div>
        <div className="glass insight-card"><div className="card-heading compact"><div><div className="section-kicker">05 / CURRENT FRAME</div><h2>Frame inspector</h2></div><span className="frame-chip">#{Math.floor(current)}</span></div><p className="insight-intro">Highest-scoring instrument at the current playhead, filtered by the benchmark.</p><div className="dominant-result">{currentDominant ? <><span className="dominant-result-name">{prettyName(currentDominant.name)}</span><strong>{pct(currentDominant.score)}</strong></> : <><span className="dominant-result-name muted-result">No instrument clears benchmark</span><strong>—</strong></>}</div><div className="insight-list">{currentDominant && <div className="insight-row"><span className="insight-dot" style={{background:COLORS[instruments.indexOf(currentDominant.name)%COLORS.length]}}/><span>{prettyName(currentDominant.name)}</span><div className="mini-meter"><i style={{width:`${Math.min(100,currentDominant.score*100)}%`,background:COLORS[instruments.indexOf(currentDominant.name)%COLORS.length]}}/></div><b>{pct(currentDominant.score)}</b></div>}</div><div className="insight-footer"><span><span className="connection-dot"/> {analysis?'Connected to analysis result':'Preview values'}</span><span>t = {formatTime(current)}</span></div></div>
      </section>
      <footer><div className="footer-brand"><AudioLines size={15}/> SONORA <span>·</span> Music intelligence workspace</div><span>Built for listening closer.</span></footer>
    </main>
  </div>
}