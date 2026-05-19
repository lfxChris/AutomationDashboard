<script setup>
import { computed, onMounted, ref } from 'vue'

const API_URL = `${import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'}/checks`

const checks = ref([])

async function loadChecks() {
  try {
    const res = await fetch(API_URL)
    const data = await res.json()

    checks.value = data.checks || []

  } catch (err) {
    console.error(err)
  }
}

onMounted(() => {
  loadChecks()

  setInterval(loadChecks, 30000)
})

const sortedChecks = computed(() => {
  return [...checks.value].sort((a, b) => {
    const priority = {
      DEAD: 0,
      DELAYED: 1,
      HEALTHY: 2,
      PAUSED: 3,
      NEW: 4
    }

    return (
      (priority[a.runtime_status] ?? 99)
      -
      (priority[b.runtime_status] ?? 99)
    )
  })
})

const TAG_PALETTE = [
  { bg: 'rgba(59,130,246,0.14)',  fg: '#93c5fd' },  // blue
  { bg: 'rgba(34,197,94,0.14)',   fg: '#86efac' },  // green
  { bg: 'rgba(168,85,247,0.14)',  fg: '#d8b4fe' },  // purple
  { bg: 'rgba(236,72,153,0.14)',  fg: '#f9a8d4' },  // pink
  { bg: 'rgba(34,211,238,0.14)',  fg: '#67e8f9' },  // cyan
  { bg: 'rgba(249,115,22,0.14)',  fg: '#fdba74' },  // orange
  { bg: 'rgba(250,204,21,0.14)',  fg: '#fcd34d' },  // amber
  { bg: 'rgba(20,184,166,0.14)',  fg: '#5eead4' },  // teal
]

function tagStyle(tag) {
  let hash = 0
  for (let i = 0; i < tag.length; i++) {
    hash = ((hash << 5) - hash) + tag.charCodeAt(i)
    hash |= 0
  }
  const { bg, fg } = TAG_PALETTE[Math.abs(hash) % TAG_PALETTE.length]
  return { background: bg, color: fg }
}

</script>

<template>
  <div class="dashboard">

    <div class="table">

      <div class="thead">
        <div class="col-status">STATUS</div>
        <div class="col-name">AUTOMATION</div>
        <div class="col-time">LAST RUN</div>
        <div class="col-time">NEXT RUN</div>
        <div class="col-runs">RUNS</div>
        <div class="col-meta">PERIOD</div>
        <div class="col-tags">TAGS</div>
      </div>

      <div class="tbody">

        <div
          v-for="check in sortedChecks"
          :key="check.slug"
          class="row"
          :class="`row-${check.runtime_status?.toLowerCase()}`"
        >

          <div class="col-status">
            <span
              class="statusDot"
              :class="`dot-${check.runtime_status?.toLowerCase()}`"
            ></span>
            <span
              class="statusLabel"
              :class="`label-${check.runtime_status?.toLowerCase()}`"
            >{{ check.runtime_status }}</span>
          </div>

          <div class="col-name">
            <div class="name">{{ check.name }}</div>
            <div v-if="check.desc" class="desc">{{ check.desc }}</div>
          </div>

          <div class="col-time">{{ check.last_run_age }}</div>

          <div class="col-time">{{ check.next_expected_relative }}</div>

          <div class="col-runs">{{ (check.total_runs || 0).toLocaleString() }}</div>

          <div class="col-meta">{{ check.period_label || '—' }}</div>

          <div class="col-tags">
            <span
              v-for="tag in (check.tags || '').split(' ').filter(Boolean)"
              :key="tag"
              class="tag"
              :style="tagStyle(tag)"
            >{{ tag }}</span>
          </div>

        </div>

      </div>

    </div>

  </div>
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: Inter, sans-serif;
  background: #0b1220;
  color: #e2e8f0;
  overflow: hidden;
}

.dashboard {
  width: 100vw;
  height: 100vh;
  padding: 1.5vh 2vw;
  overflow: hidden;
}

.table {
  width: 100%;
  height: 100%;

  display: flex;
  flex-direction: column;

  container-type: size;
}

.thead,
.row {
  display: grid;

  grid-template-columns:
    minmax(7rem, 9cqw)        /* status */
    minmax(0, 1.7fr)          /* name */
    minmax(6rem, 8cqw)        /* last run */
    minmax(6rem, 8cqw)        /* next run */
    minmax(4rem, 6cqw)        /* runs */
    minmax(5rem, 8cqw)        /* period */
    minmax(0, 1fr);           /* tags */

  align-items: center;
  gap: 1.5cqw;

  padding: 0 1.5cqw;
}

.thead {
  height: 5cqh;

  font-size: clamp(0.7rem, 2.2cqh, 1.05rem);
  font-weight: 700;
  letter-spacing: 0.12em;
  color: #f1f5f9;

  border-bottom: 1px solid rgba(255,255,255,0.15);
}

.tbody {
  flex: 1;
  display: flex;
  flex-direction: column;

  min-height: 0;
}

.row {
  flex: 1;
  min-height: 0;

  border-bottom: 1px solid rgba(255,255,255,0.04);
  border-left: 3px solid transparent;

  transition: background 0.2s ease;
}

.row:hover {
  background: rgba(255,255,255,0.02);
}

.row-healthy { border-left-color: #22c55e; }
.row-delayed { border-left-color: #facc15; }
.row-dead    { border-left-color: #ef4444; }
.row-paused  { border-left-color: #94a3b8; }
.row-new     { border-left-color: #38bdf8; }

.row-dead {
  background: rgba(239,68,68,0.04);
}

.col-status {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  min-width: 0;
}

.statusDot {
  width: 0.6rem;
  height: 0.6rem;
  border-radius: 999px;
  background: #475569;
  flex-shrink: 0;
}

.dot-healthy { background: #22c55e; box-shadow: 0 0 0.5rem rgba(34,197,94,0.5); }
.dot-delayed { background: #facc15; box-shadow: 0 0 0.5rem rgba(250,204,21,0.5); }
.dot-dead    { background: #ef4444; box-shadow: 0 0 0.5rem rgba(239,68,68,0.6); }
.dot-paused  { background: #94a3b8; }
.dot-new     { background: #38bdf8; }

.statusLabel {
  font-size: clamp(0.65rem, 2cqh, 1rem);
  font-weight: 700;
  letter-spacing: 0.1em;
  color: #94a3b8;
}

.label-healthy { color: #4ade80; }
.label-delayed { color: #facc15; }
.label-dead    { color: #f87171; }
.label-paused  { color: #cbd5e1; }
.label-new     { color: #7dd3fc; }

.col-name {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.name {
  font-size: clamp(0.9rem, 2.6cqh, 1.4rem);
  font-weight: 600;
  color: #f1f5f9;
  letter-spacing: -0.01em;

  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.desc {
  font-size: clamp(0.65rem, 1.7cqh, 0.9rem);
  color: #64748b;

  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.row .col-time,
.row .col-meta {
  font-size: clamp(0.75rem, 2.2cqh, 1.15rem);
  color: #cbd5e1;

  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.row .col-meta {
  color: #94a3b8;
}

.col-runs {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.row .col-runs {
  font-size: clamp(0.8rem, 2.4cqh, 1.25rem);
  font-weight: 700;
  color: #e2e8f0;
}

.col-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  min-width: 0;
  overflow: hidden;
}

.tag {
  padding: 0.15rem 0.55rem;
  border-radius: 999px;
  font-size: clamp(0.55rem, 1.6cqh, 0.75rem);
  font-weight: 600;
  white-space: nowrap;
}

</style>
