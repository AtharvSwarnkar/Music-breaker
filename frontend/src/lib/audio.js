export function formatTime(seconds = 0) {
  if (!Number.isFinite(seconds)) return '0:00'
  const s = Math.max(0, Math.floor(seconds))
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`
}
export async function makeWaveform(file, samples = 900) {
  const ctx = new (window.AudioContext || window.webkitAudioContext)()
  try {
    const buffer = await ctx.decodeAudioData(await file.arrayBuffer())
    const data = buffer.getChannelData(0)
    const block = Math.max(1, Math.floor(data.length / samples))
    const values = []
    for (let i = 0; i < samples; i++) {
      const start = i * block
      let peak = 0
      for (let j = start; j < Math.min(start + block, data.length); j += 8) peak = Math.max(peak, Math.abs(data[j]))
      values.push(peak)
    }
    return { values, duration: buffer.duration }
  } finally { await ctx.close() }
}
export function normalizeAnalysis(raw, duration = 0) {
  // Accepts: {windows:[{time, instruments:{Drums: .8}}]}, arrays of window records,
  // {analysis:[...]}, {instrument_percentages:{...}}, or {instruments:{...}}.
  const windows = Array.isArray(raw) ? raw : raw?.windows || raw?.analysis || raw?.results || raw?.frames || []
  const instrumentMap = new Map()
  const rows = windows.map((item, index) => {
    const time = Number(item.time ?? item.timestamp ?? item.start ?? index)
    let values = item.instruments || item.scores || item.predictions || item.detected_instruments || item
    if (Array.isArray(values)) values = Object.fromEntries(values.map(v => Array.isArray(v) ? [v[0], v[1]] : [v.instrument || v.label || v.name, v.score ?? v.value ?? v.confidence]))
    const clean = {}
    Object.entries(values || {}).forEach(([key, value]) => {
      if (['time','timestamp','start','end','duration','index','window'].includes(key)) return
      const score = typeof value === 'object' && value !== null ? Number(value.score ?? value.value ?? value.confidence ?? 0) : Number(value)
      if (Number.isFinite(score) && score > 0) { clean[key] = score; instrumentMap.set(key, true) }
    })
    return { time, ...clean }
  })
  if (!rows.length) {
    const summary = raw?.instrument_percentages || raw?.instruments || raw?.instrument_contribution || raw?.percentages || {}
    const entries = Object.entries(summary).filter(([,v]) => Number(v) > 0)
    entries.forEach(([k]) => instrumentMap.set(k, true))
    if (entries.length) rows.push({ time: 0, ...Object.fromEntries(entries.map(([k,v]) => [k, Number(v)])) })
  }
  // Convert percentages/fractions into a consistent 0–1 chart scale per instrument.
  const keys = [...instrumentMap.keys()].filter(k => rows.some(r => Number(r[k]) > 0))
  const maxes = Object.fromEntries(keys.map(k => [k, Math.max(...rows.map(r => Number(r[k] || 0)))]))
  const normalized = rows.map((r, i) => {
    const out = { second: Math.max(0, Math.round(Number.isFinite(r.time) ? r.time : i)) }
    keys.forEach(k => {
      const v = Number(r[k] || 0), max = maxes[k] || 1
      out[k] = v > 1 ? v / 100 : (max > 0 && max <= 1 ? v : v / max)
    })
    return out
  })
  // Make one point per second. Duplicate timestamps are averaged; missing seconds remain zero.
  const bySecond = new Map()
  normalized.forEach(r => {
    const s = r.second
    if (!bySecond.has(s)) bySecond.set(s, { second: s, count: 0, ...Object.fromEntries(keys.map(k => [k, 0])) })
    const dest = bySecond.get(s); dest.count++
    keys.forEach(k => dest[k] += r[k] || 0)
  })
  let points = [...bySecond.values()].sort((a,b) => a.second-b.second).map(r => ({ second: r.second, ...Object.fromEntries(keys.map(k => [k, r[k] / r.count])) }))
  if (points.length > 1) {
    const filled = []
    for (let s = points[0].second; s <= points[points.length-1].second; s++) {
      const exact = points.find(p => p.second === s)
      filled.push(exact || { second: s, ...Object.fromEntries(keys.map(k => [k, 0])) })
    }
    points = filled
  }
  return { points, instruments: keys, summary: raw?.instrument_percentages || raw?.final_percentages || raw?.percentages || {}, metadata: raw?.metadata || raw?.song || {}, duration: Number(raw?.duration || raw?.duration_seconds || duration || 0), raw }
}