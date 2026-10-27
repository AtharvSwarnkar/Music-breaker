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
  const windows = Array.isArray(raw)
    ? raw
    : raw?.windows ||
      raw?.analysis ||
      raw?.results ||
      raw?.frames ||
      [];

  const instrumentMap = new Map();

  const rows = windows.map((item, index) => {
    const time = Number(
      item.time ?? item.timestamp ?? item.start ?? index
    );

    let values =
      item.instruments ||
      item.scores ||
      item.predictions ||
      item.detected_instruments ||
      item;

    if (Array.isArray(values)) {
      values = Object.fromEntries(
        values.map((v) =>
          Array.isArray(v)
            ? [v[0], v[1]]
            : [
                v.instrument || v.label || v.name,
                v.score ?? v.value ?? v.confidence,
              ]
        )
      );
    }

    const clean = {};

    Object.entries(values || {}).forEach(([key, value]) => {
      if (
        [
          "time",
          "timestamp",
          "start",
          "end",
          "duration",
          "index",
          "window",
        ].includes(key)
      ) {
        return;
      }

      const score =
        typeof value === "object" && value !== null
          ? Number(
              value.score ??
                value.value ??
                value.confidence ??
                0
            )
          : Number(value);

      if (Number.isFinite(score) && score > 0) {
        clean[key] = score;
        instrumentMap.set(key, true);
      }
    });

    return { time, ...clean };
  });

  // Support responses containing only song-level instrument scores.
  if (!rows.length) {
    const summary =
      raw?.song_level_scores ||
      raw?.instrument_percentages ||
      raw?.instruments ||
      raw?.instrument_contribution ||
      raw?.contribution ||
      raw?.final_percentages ||
      raw?.percentages ||
      {};

    const entries = Object.entries(summary).filter(
      ([, value]) => {
        const score =
          typeof value === "object" && value !== null
            ? Number(
                value.score ??
                  value.value ??
                  value.confidence ??
                  0
              )
            : Number(value);

        return Number.isFinite(score) && score > 0;
      }
    );

    entries.forEach(([key]) => instrumentMap.set(key, true));

    if (entries.length) {
      rows.push({
        time: 0,
        ...Object.fromEntries(
          entries.map(([key, value]) => {
            const score =
              typeof value === "object" && value !== null
                ? Number(
                    value.score ??
                      value.value ??
                      value.confidence ??
                      0
                  )
                : Number(value);

            return [key, score];
          })
        ),
      });
    }
  }

  const keys = [...instrumentMap.keys()].filter((key) =>
    rows.some((row) => Number(row[key]) > 0)
  );

  const maxes = Object.fromEntries(
    keys.map((key) => [
      key,
      Math.max(...rows.map((row) => Number(row[key] || 0))),
    ])
  );

  // Normalize window scores to a 0–1 scale.
  const normalized = rows.map((row, index) => {
    const result = {
      second: Math.max(
        0,
        Math.round(
          Number.isFinite(row.time) ? row.time : index
        )
      ),
    };

    keys.forEach((key) => {
      const value = Number(row[key] || 0);
      const max = maxes[key] || 1;

      result[key] =
        value > 1
          ? value / 100
          : max > 0 && max <= 1
            ? value
            : value / max;
    });

    return result;
  });

  // Average records with duplicate timestamps.
  const bySecond = new Map();

  normalized.forEach((row) => {
    const second = row.second;

    if (!bySecond.has(second)) {
      bySecond.set(second, {
        second,
        count: 0,
        ...Object.fromEntries(keys.map((key) => [key, 0])),
      });
    }

    const destination = bySecond.get(second);
    destination.count++;

    keys.forEach((key) => {
      destination[key] += row[key] || 0;
    });
  });

  let points = [...bySecond.values()]
    .sort((a, b) => a.second - b.second)
    .map((row) => ({
      second: row.second,
      ...Object.fromEntries(
        keys.map((key) => [
          key,
          row[key] / row.count,
        ])
      ),
    }));

  // Fill missing seconds with zero-valued records.
  if (points.length > 1) {
    const filled = [];

    for (
      let second = points[0].second;
      second <= points[points.length - 1].second;
      second++
    ) {
      const exact = points.find(
        (point) => point.second === second
      );

      filled.push(
        exact ||
          {
            second,
            ...Object.fromEntries(
              keys.map((key) => [key, 0])
            ),
          }
      );
    }

    points = filled;
  }

  // Prefer the backend's song-level aggregate for the overview.
  const summary =
    raw?.song_level_scores ||
    raw?.instrument_contribution ||
    raw?.contribution ||
    raw?.instrument_percentages ||
    raw?.final_percentages ||
    raw?.percentages ||
    {};

  return {
    points,
    instruments: keys,
    summary,
    metadata: raw?.metadata || raw?.song || {},
    duration: Number(
      raw?.duration ||
        raw?.duration_seconds ||
        duration ||
        0
    ),
    raw,
  };
}


