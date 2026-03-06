<template>
  <div class="glass-card p-4 md:p-6 rounded-2xl border border-[var(--surface-border)]">
    <div class="flex justify-between items-center mb-6">
      <div class="flex items-center gap-4">
        <h2 class="text-lg font-bold text-white/90 uppercase flex items-center gap-2">
          <CalendarIcon class="w-6 h-6 text-amber-400" />
          {{ currentMonthName }} {{ currentYear }}
        </h2>
        <div class="flex glass-surface p-1 rounded-xl border border-[var(--surface-border)]">
          <button
            @click="changeMonth(-1)"
            class="p-1.5 rounded-lg text-white/70 hover:bg-white/10 hover:text-white transition-all"
          >
            <ChevronLeft class="w-5 h-5" />
          </button>
          <button
            @click="changeMonth(1)"
            class="p-1.5 rounded-lg text-white/70 hover:bg-white/10 hover:text-white transition-all"
          >
            <ChevronRight class="w-5 h-5" />
          </button>
        </div>
      </div>

      <div class="hidden md:flex gap-2 text-[10px] font-bold">
        <span class="glass-surface px-2 py-1 rounded-lg border border-amber-400/30 text-amber-300 bg-amber-500/20">
          📥 RECEIVED
        </span>
        <span class="glass-surface px-2 py-1 rounded-lg border border-blue-400/30 text-blue-300 bg-blue-500/20">
          🚚 DELIVERY
        </span>
      </div>
    </div>

    <div class="grid grid-cols-7 gap-px glass-surface rounded-2xl overflow-hidden border border-[var(--surface-border)]">
      <div
        v-for="day in ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']"
        :key="day"
        class="bg-white/5 p-3 text-center text-xs font-bold text-white/50 uppercase border-b border-[var(--surface-border)]"
      >
        {{ day }}
      </div>

      <div
        v-for="date in calendarDays"
        :key="date.toISOString()"
        class="glass-surface min-h-[120px] p-2 hover:bg-white/10 transition relative group border border-[var(--surface-border)]"
        :class="{ 'opacity-40 pointer-events-none': !isSameMonth(date) }"
      >
        <span
          class="text-sm font-bold inline-flex items-center justify-center w-7 h-7 rounded-full"
          :class="
            isToday(date)
              ? 'bg-[var(--color-primary)] text-white'
              : 'text-white/50'
          "
        >
          {{ date.getDate() }}
        </span>

        <div class="mt-2 space-y-1">
          <div
            v-for="item in getRepairsForDate(date)"
            :key="item.id + (isReceivedDay(date, item) ? 'rec' : 'del')"
            @click="$emit('select', item)"
            class="cursor-pointer"
          >
            <div
              v-if="isReceivedDay(date, item)"
              @click="$emit('select', item)"
              class="text-[9px] p-1.5 rounded-lg border font-bold truncate transition bg-amber-500/20 text-amber-300 border-amber-400/30 hover:bg-amber-500/30"
            >
              📥 Rec: {{ item.item_name }}
            </div>

            <div
              v-if="isReturnDay(date, item)"
              @click="$emit('select', item)"
              :class="[
                'text-[9px] p-1.5 rounded-lg border font-bold truncate transition',
                item.status === 'ready'
                  ? 'bg-emerald-500/20 text-emerald-300 border-emerald-400/30 hover:bg-emerald-500/30'
                  : 'bg-blue-500/20 text-blue-300 border-blue-400/30 hover:bg-blue-500/30',
              ]"
            >
              🚚 Del: {{ item.item_name }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Calendar as CalendarIcon, ChevronLeft, ChevronRight } from 'lucide-vue-next'
import { ref, onMounted, computed } from 'vue'
import api from '@/services/api'

const repairs = ref([])
const calendarDays = ref([])
const viewDate = ref(new Date())

const currentMonthName = computed(() => viewDate.value.toLocaleString('default', { month: 'long' }))
const currentYear = computed(() => viewDate.value.getFullYear())

const getAuthConfig = () => {
  const token = localStorage.getItem('access_token')
  return { headers: { Authorization: `Bearer ${token}` } }
}

const fetchRepairs = async () => {
  try {
    const res = await api.get('service/repairs/', getAuthConfig())
    repairs.value = res.data.results || res.data || []
  } catch (err) {
    console.error(err)
  }
}

const generateCalendar = () => {
  const days = []
  const year = viewDate.value.getFullYear()
  const month = viewDate.value.getMonth()
  const firstDay = new Date(year, month, 1)
  const startDate = new Date(firstDay)
  startDate.setDate(startDate.getDate() - firstDay.getDay())
  for (let i = 0; i < 42; i++) {
    days.push(new Date(startDate))
    startDate.setDate(startDate.getDate() + 1)
  }
  calendarDays.value = days
}

const changeMonth = (offset) => {
  viewDate.value = new Date(viewDate.value.getFullYear(), viewDate.value.getMonth() + offset, 1)
  generateCalendar()
}

const getDateString = (date) => {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

const isReceivedDay = (date, item) => item.received_date?.split('T')[0] === getDateString(date)
const isReturnDay = (date, item) => item.return_date === getDateString(date)

const getRepairsForDate = (date) => {
  const dateStr = getDateString(date)
  return repairs.value.filter(
    (r) => r.received_date?.split('T')[0] === dateStr || r.return_date === dateStr,
  )
}

const isSameMonth = (date) => date.getMonth() === viewDate.value.getMonth()
const isToday = (date) => new Date().toDateString() === date.toDateString()

onMounted(() => {
  generateCalendar()
  fetchRepairs()
})
</script>
