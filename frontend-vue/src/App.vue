<script setup>
import { computed, onMounted, ref } from 'vue'

const API_URL = `${import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'}/checks`
const BASE_URL = import.meta.env.BASE_URL

const DASHBOARD_MS = 60_000   // 1 minute on the dashboard
const LOGO_MS = 60_000        // 1 minute on the logo screen

const checks = ref([])
const now = ref(new Date())
const screen = ref('dashboard')

function flipScreen() {
  if (screen.value === 'dashboard') {
    screen.value = 'logo'
    setTimeout(flipScreen, LOGO_MS)
  } else {
    screen.value = 'dashboard'
    setTimeout(flipScreen, DASHBOARD_MS)
  }
}

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
  setInterval(() => { now.value = new Date() }, 1000)
  setTimeout(flipScreen, DASHBOARD_MS)
})

const sortedChecks = computed(() => {
  return [...checks.value].sort((a, b) => {
    const priority = { MISSED: 0, HEALTHY: 1, PAUSED: 2, NEW: 3 }
    return (priority[a.runtime_status] ?? 99) - (priority[b.runtime_status] ?? 99)
  })
})

const statusCounts = computed(() => {
  const counts = { HEALTHY: 0, MISSED: 0, PAUSED: 0, NEW: 0 }
  for (const c of checks.value) {
    if (counts[c.runtime_status] != null) counts[c.runtime_status]++
  }
  return counts
})

const clockTime = computed(() =>
  now.value.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })
)
const clockDate = computed(() =>
  now.value.toLocaleDateString([], { weekday: 'long', month: 'long', day: 'numeric' })
)

const TAG_PALETTE = [
  { bg: 'rgba(59,130,246,0.14)',  fg: '#93c5fd' },
  { bg: 'rgba(34,197,94,0.14)',   fg: '#86efac' },
  { bg: 'rgba(168,85,247,0.14)',  fg: '#d8b4fe' },
  { bg: 'rgba(236,72,153,0.14)',  fg: '#f9a8d4' },
  { bg: 'rgba(34,211,238,0.14)',  fg: '#67e8f9' },
  { bg: 'rgba(249,115,22,0.14)',  fg: '#fdba74' },
  { bg: 'rgba(250,204,21,0.14)',  fg: '#fcd34d' },
  { bg: 'rgba(20,184,166,0.14)',  fg: '#5eead4' },
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

function uptimeClass(pct) {
  if (pct == null) return 'uptime-none'
  if (pct >= 99) return 'uptime-great'
  if (pct >= 95) return 'uptime-ok'
  return 'uptime-bad'
}

function streakClass(n) {
  if (!n) return 'streak-none'
  if (n >= 50) return 'streak-hot'
  if (n >= 10) return 'streak-warm'
  return 'streak-cool'
}

function formatUptime(pct) {
  if (pct == null) return '—'
  return `${pct.toFixed(1)}%`
}
</script>

<template>
  <Transition name="fade" mode="out-in">

  <div v-if="screen === 'dashboard'" class="dashboard">

    <header class="topbar">
      <div class="brand">
        <h1 class="title">Automations</h1>
        <div class="clock">{{ clockDate }} &nbsp;·&nbsp; {{ clockTime }}</div>
      </div>
      <div class="summary">
        <span class="stat">
          <span class="stat-value v-healthy">{{ statusCounts.HEALTHY }}</span>
          <span class="stat-label">Healthy</span>
        </span>
        <span class="stat">
          <span class="stat-value v-missed">{{ statusCounts.MISSED }}</span>
          <span class="stat-label">Missed</span>
        </span>
        <span class="stat">
          <span class="stat-value v-paused">{{ statusCounts.PAUSED }}</span>
          <span class="stat-label">Paused</span>
        </span>
      </div>
    </header>

    <section class="list">

      <div class="head">
        <div class="c-status">Status</div>
        <div class="c-name">Automation</div>
        <div class="c-num c-streak">Streak</div>
        <div class="c-num c-uptime">Uptime</div>
        <div class="c-num c-lastrun">Last Run</div>
        <div class="c-source">Source</div>
      </div>

      <div class="body">
        <div
          v-for="check in sortedChecks"
          :key="check.slug"
          class="row"
          :class="`row-${check.runtime_status?.toLowerCase()}`"
        >
          <div class="c-status">
            <span
              class="status-text"
              :class="`text-${check.runtime_status?.toLowerCase()}`"
            >{{ check.runtime_status }}</span>
          </div>

          <div class="c-name">
            <span class="name">{{ check.name }}</span>
            <span v-if="check.period_label" class="schedule">{{ check.period_label }}</span>
          </div>

          <div class="c-num c-streak" :class="streakClass(check.streak)">
            <span class="num">{{ check.streak ?? 0 }}</span>
          </div>

          <div class="c-num c-uptime" :class="uptimeClass(check.uptime)">
            <span class="num">{{ formatUptime(check.uptime) }}</span>
          </div>

          <div class="c-num c-lastrun">
            <span class="num lastrun-num">{{ check.last_run_age }}</span>
          </div>

          <div class="c-source">
            <span
              v-for="tag in (check.tags || '').split(' ').filter(Boolean)"
              :key="tag"
              class="tag"
              :style="tagStyle(tag)"
            >{{ tag }}</span>
          </div>
        </div>
      </div>

    </section>

  </div>

  <div v-else class="logo-screen">
    <img :src="`${BASE_URL}LFX_Group.png`" alt="LFX Group" class="brand-logo" />
  </div>

  </Transition>
</template>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  background: radial-gradient(ellipse at top, #111c34 0%, #0a1020 70%);
  color: #e2e8f0;
  overflow: hidden;
  -webkit-font-smoothing: antialiased;
  font-feature-settings: "cv11", "ss01";
  line-height: 1;
}

.dashboard {
  width: 100vw;
  height: 100vh;
  padding: 3vh 3vw;
  display: flex;
  flex-direction: column;
  gap: 3vh;
  container-type: size;
  overflow: hidden;
}

/* ───────────────────── Top bar ─────────────────────
   Title and stat values share the same font-size so
   `align-items: baseline` makes them sit on the exact
   same typographic line. */

.topbar {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 3cqw;
  flex-shrink: 0;
}

.brand {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.55rem;
}

.title {
  font-size: clamp(2rem, 5cqh, 3.6rem);
  font-weight: 800;
  letter-spacing: -0.03em;
  color: #f8fafc;
  line-height: 1;
}

.clock {
  font-size: clamp(0.8rem, 1.6cqh, 1.15rem);
  font-weight: 500;
  color: #64748b;
  letter-spacing: 0.02em;
  font-variant-numeric: tabular-nums;
  line-height: 1;
}

.summary {
  display: flex;
  align-items: baseline;
  gap: 3cqw;
}

.stat {
  display: inline-flex;
  align-items: baseline;
  gap: 0.7rem;
}

.stat-value {
  font-size: clamp(2rem, 5cqh, 3.6rem);
  font-weight: 800;
  letter-spacing: -0.035em;
  line-height: 1;
  font-variant-numeric: tabular-nums;
}
.v-healthy { color: #4ade80; }
.v-missed  { color: #fb923c; }
.v-paused  { color: #94a3b8; }

.stat-label {
  font-size: clamp(0.7rem, 1.4cqh, 1rem);
  font-weight: 700;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: #64748b;
  line-height: 1;
}

/* ───────────────────── List ─────────────────────
   Head and row share an identical grid template and
   left-border width so columns line up to the pixel. */

.list {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.head,
.row {
  display: grid;
  grid-template-columns:
    minmax(7rem, 10cqw)      /* status   */
    minmax(0, 2.2fr)          /* name     */
    minmax(5rem, 7cqw)        /* streak   */
    minmax(7rem, 9cqw)        /* uptime   */
    minmax(7rem, 10cqw)       /* last run */
    minmax(0, 1.3fr);         /* source   */
  align-items: center;
  gap: 2cqw;
  padding-left: 1.5cqw;
  padding-right: 1.5cqw;
  border-left: 0.4rem solid transparent;
}

.head {
  height: 4.5cqh;
  flex-shrink: 0;
  border-bottom: 1px solid rgba(255,255,255,0.06);
  font-size: clamp(0.7rem, 1.45cqh, 1rem);
  font-weight: 700;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: #475569;
}

.body {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.row {
  flex: 1;
  min-height: 0;
  border-bottom: 1px solid rgba(255,255,255,0.04);
}

.row:last-child { border-bottom: none; }

.row-healthy { border-left-color: rgba(34,197,94,0.7); }
.row-missed  {
  border-left-color: #fb923c;
  background: linear-gradient(90deg, rgba(251,146,60,0.06) 0%, rgba(251,146,60,0) 35%);
}
.row-paused  { border-left-color: rgba(148,163,184,0.5); }
.row-new     { border-left-color: rgba(56,189,248,0.6); }

/* ───────────────────── Status column ───────────────────── */

.c-status { min-width: 0; overflow: hidden; }

.status-text {
  font-size: clamp(0.85rem, 1.9cqh, 1.2rem);
  font-weight: 700;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: #94a3b8;
  white-space: nowrap;
  line-height: 1;
}

.text-healthy { color: #4ade80; }
.text-missed  { color: #fb923c; }
.text-paused  { color: #cbd5e1; }
.text-new     { color: #7dd3fc; }

/* ───────────────────── Name column ─────────────────────
   Name, schedule chip, description all sit on one line
   and baseline-align to each other. */

.c-name {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  min-width: 0;
  overflow: hidden;
}

.head .c-name { display: block; }

.name {
  font-size: clamp(1rem, 2.8cqh, 1.75rem);
  font-weight: 600;
  color: #f1f5f9;
  letter-spacing: -0.018em;
  line-height: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex-shrink: 1;
  min-width: 0;
}

.schedule {
  padding: 0.3rem 0.65rem;
  border-radius: 0.35rem;
  background: rgba(148,163,184,0.1);
  color: #94a3b8;
  font-size: clamp(0.7rem, 1.5cqh, 0.95rem);
  font-weight: 500;
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.02em;
  line-height: 1;
  white-space: nowrap;
  flex-shrink: 0;
}

/* ───────────────────── Numeric columns ─────────────────────
   Big bold figures for STREAK / UPTIME, lighter for LAST RUN. */

.c-num {
  min-width: 0;
  overflow: hidden;
}

.num {
  font-size: clamp(1.2rem, 3.2cqh, 2.2rem);
  font-weight: 800;
  letter-spacing: -0.025em;
  font-variant-numeric: tabular-nums;
  color: #e2e8f0;
  line-height: 1;
  white-space: nowrap;
}

.lastrun-num {
  font-size: clamp(0.95rem, 2.4cqh, 1.55rem);
  font-weight: 500;
  color: #cbd5e1;
  letter-spacing: -0.01em;
}

.streak-none .num { color: #475569; }
.streak-cool .num { color: #f1f5f9; }
.streak-warm .num { color: #fcd34d; text-shadow: 0 0 0.8rem rgba(250,204,21,0.28); }
.streak-hot  .num { color: #fb923c; text-shadow: 0 0 1.1rem rgba(251,146,60,0.45); }

.uptime-none  .num { color: #475569; }
.uptime-great .num { color: #4ade80; }
.uptime-ok    .num { color: #facc15; }
.uptime-bad   .num { color: #f87171; }

/* ───────────────────── Source column ───────────────────── */

.c-source {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.4rem;
  min-width: 0;
  overflow: hidden;
  max-height: 100%;
}

.head .c-source { display: block; }

.tag {
  padding: 0.32rem 0.7rem;
  border-radius: 999px;
  font-size: clamp(0.7rem, 1.5cqh, 0.95rem);
  font-weight: 600;
  letter-spacing: 0.01em;
  line-height: 1;
  white-space: nowrap;
}

/* ───────────────────── Logo screen ───────────────────── */

.logo-screen {
  width: 100vw;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

.brand-logo {
  width: 95vw;
  height: 95vh;
  object-fit: contain;
}

/* ───────────────────── Slide transition ───────────────────── */

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.7s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
