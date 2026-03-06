<template>
  <header
    class="min-h-[52px] sm:min-h-[56px] md:min-h-[60px] bg-[var(--color-bg-card)] flex items-center justify-between px-3 sm:px-4 md:px-6 border-b border-[var(--color-border)] shadow-sm relative z-50"
    style="padding-top: max(0.5rem, env(safe-area-inset-top)); padding-left: max(0.75rem, env(safe-area-inset-left)); padding-right: max(0.75rem, env(safe-area-inset-right)); padding-bottom: 0.5rem;"
  >
    <div class="flex items-center gap-2 min-w-0">
      <button
        type="button"
        class="lg:hidden min-w-[44px] min-h-[44px] flex items-center justify-center rounded-xl text-[var(--color-text-muted)] hover:bg-[var(--color-bg-light)] hover:text-[var(--color-text)] touch-manipulation -ml-1 transition-colors"
        aria-label="Open menu"
        @click="$emit('toggle-sidebar')"
      >
        <svg class="w-6 h-6 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="1.8"><path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h16M4 18h16" /></svg>
      </button>
    </div>

    <div class="flex items-center gap-1 sm:gap-3 md:gap-4 min-w-0">
      <!-- Language: EN / မြန်မာ -->
      <div class="flex rounded-xl overflow-hidden border border-[var(--color-border)] bg-[var(--color-bg-light)]">
        <button
          type="button"
          :class="[locale.isEn ? 'bg-[var(--color-primary)] text-white' : 'text-[var(--color-text-muted)] hover:bg-[var(--color-bg-card)] hover:text-[var(--color-text)]']"
          class="px-2.5 py-2 sm:px-3 text-xs font-semibold transition-colors min-w-[40px] min-h-[40px] sm:min-w-0 sm:min-h-0 sm:py-1.5"
          @click="locale.setLang('en')"
        >
          EN
        </button>
        <button
          type="button"
          :class="[locale.isMm ? 'bg-[var(--color-primary)] text-white' : 'text-[var(--color-text-muted)] hover:bg-[var(--color-bg-card)] hover:text-[var(--color-text)]']"
          class="px-2.5 py-2 sm:px-3 text-xs font-semibold transition-colors min-w-[40px] min-h-[40px] sm:min-w-0 sm:min-h-0 sm:py-1.5"
          @click="locale.setLang('mm')"
        >
          မြန်မာ
        </button>
      </div>
      <div class="relative notification-area">
        <button
          @click="toggleNotify"
          class="min-w-[44px] min-h-[44px] flex items-center justify-center text-[var(--color-text-muted)] hover:bg-[var(--color-bg-light)] hover:text-[var(--color-text)] rounded-xl relative transition-colors touch-manipulation"
        >
          <Bell class="w-5 h-5 sm:w-6 sm:h-6" />
          <span
            v-if="unreadCount > 0"
            class="absolute top-1.5 right-1.5 w-2 h-2 bg-rose-500 rounded-full border-2 border-[var(--color-bg-card)]"
          ></span>
          <span
            v-if="unreadCount > 0"
            class="absolute -top-0.5 -right-0.5 bg-rose-500 text-white text-[10px] min-w-[18px] h-[18px] flex items-center justify-center rounded-full font-bold"
          >
            {{ unreadCount }}
          </span>
        </button>

        <div
          v-if="isNotifyOpen"
          class="absolute right-0 mt-2 w-[min(100vw-2rem,320px)] sm:w-80 bg-[var(--color-bg-card)] rounded-xl shadow-lg border border-[var(--color-border)] py-2 z-[100] max-h-[70vh] overflow-y-auto custom-scrollbar"
        >
          <div class="px-4 py-2.5 border-b border-[var(--color-border)] flex justify-between items-center">
            <span class="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wide">{{ locale.isEn ? 'Notifications' : 'အကြောင်းကြားချက်များ' }}</span>
            <button
              @click="markAllAsRead"
              class="text-xs font-medium text-[var(--color-primary)] hover:underline"
            >
              {{ locale.isEn ? 'Mark all read' : 'အားလုံး ဖတ်ပြီး' }}
            </button>
          </div>
          <div
            v-if="notifications.length === 0"
            class="p-6 text-center text-sm text-[var(--color-text-subtle)]"
          >
            {{ locale.isEn ? 'No notifications yet.' : 'အကြောင်းကြားချက် မရှိသေးပါ။' }}
          </div>
          <div
            v-for="n in notifications"
            :key="n.id"
            @click="markAsRead(n)"
            :class="[
              'px-4 py-3 hover:bg-[var(--color-bg-light)] cursor-pointer border-b border-[var(--color-border)] last:border-0 transition-colors',
              !n.is_read ? 'bg-[var(--color-bg-light)]/50' : '',
            ]"
          >
            <div class="flex gap-3">
              <div
                :class="['w-2 h-2 mt-1.5 rounded-full shrink-0', !n.is_read ? 'bg-[var(--color-primary)]' : 'bg-transparent']"
              ></div>
              <div class="min-w-0">
                <p class="text-sm font-medium text-[var(--color-text)] leading-snug">{{ n.message }}</p>
                <p class="text-xs text-[var(--color-text-subtle)] mt-1">{{ formatDate(n.created_at) }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="relative profile-area border-l border-[var(--color-border)] pl-2 sm:pl-3">
        <button
          @click="toggleProfile"
          class="min-w-[44px] min-h-[44px] sm:min-w-0 sm:min-h-0 flex items-center justify-center sm:justify-end gap-2 sm:gap-3 rounded-xl hover:bg-[var(--color-bg-light)] transition-colors touch-manipulation py-1"
        >
          <div class="text-right hidden sm:block min-w-0">
            <p class="text-sm font-semibold text-[var(--color-text)] truncate leading-none">
              {{ user?.username || '...' }}
            </p>
            <p class="text-xs text-[var(--color-text-muted)] mt-0.5 truncate">
              {{ user?.role_name || 'Staff' }}
            </p>
          </div>
          <div
            class="w-9 h-9 sm:w-10 sm:h-10 rounded-full bg-[var(--color-bg-light)] border border-[var(--color-border)] flex items-center justify-center text-[var(--color-text-muted)] overflow-hidden shrink-0"
          >
            <img v-if="user?.avatar" :src="user.avatar" class="w-full h-full object-cover" alt="" />
            <User v-else class="w-5 h-5" />
          </div>
        </button>

        <div
          v-if="isProfileOpen"
          class="absolute right-0 mt-2 w-52 bg-[var(--color-bg-card)] rounded-xl shadow-lg border border-[var(--color-border)] py-2 z-[110] overflow-hidden"
        >
          <div class="px-4 py-2.5 border-b border-[var(--color-border)]">
            <p class="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wide">Account</p>
          </div>
          <button
            class="w-full flex items-center gap-3 px-4 py-3 text-[var(--color-text)] hover:bg-[var(--color-bg-light)] transition-colors text-sm font-medium"
          >
            <CircleUser class="w-4 h-4 text-[var(--color-text-muted)]" /> My Profile
          </button>
          <button
            @click="handleLogout"
            class="w-full flex items-center gap-3 px-4 py-3 text-rose-600 hover:bg-rose-50 transition-colors text-sm font-semibold border-t border-[var(--color-border)]"
          >
            <LogOut class="w-4 h-4" /> Logout
          </button>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { Bell, User, LogOut, CircleUser } from 'lucide-vue-next'
import { useLocaleStore } from '@/stores/locale'
import { useAuthStore } from '@/stores/auth'
import { getLoginPath } from '@/router'

defineEmits(['toggle-sidebar'])
const locale = useLocaleStore()
const router = useRouter()
const authStore = useAuthStore()

// --- States ---
const user = ref(null)
const notifications = ref([])
const isNotifyOpen = ref(false)
const isProfileOpen = ref(false)
import api from '@/services/api'
let pollingTimer = null

// --- Methods ---

// Dropdown ပိတ်/ဖွင့် Logic
const toggleNotify = () => {
  isNotifyOpen.value = !isNotifyOpen.value
  isProfileOpen.value = false
}

const toggleProfile = () => {
  isProfileOpen.value = !isProfileOpen.value
  isNotifyOpen.value = false
}

// User Data ဆွဲယူခြင်း
const fetchUserData = async () => {
  try {
    // api service က auto token injection လုပ်ပေးတယ်
    const res = await api.get('core/me/')
    user.value = res.data
  } catch (err) {
    console.error('User profile fetch error:', err)
  }
}

// Notifications ဆွဲယူခြင်း
const fetchNotifications = async () => {
  const token = localStorage.getItem('access_token')
  if (!token) return
  try {
    // api service က auto token injection လုပ်ပေးတယ်
    const res = await api.get('notifications/')
    notifications.value = Array.isArray(res?.data) ? res.data : []
  } catch (err) {
    console.error('Notification fetch error:', err)
    notifications.value = []
  }
}

// တစ်ခုချင်းစီကို Read လုပ်ခြင်း
const markAsRead = async (notification) => {
  if (notification.is_read) return
  try {
    // api service က auto token injection လုပ်ပေးတယ်
    await api.patch(`notifications/${notification.id}/read/`, { is_read: true })
    notification.is_read = true
  } catch (err) {
    console.error('Mark as read failed:', err)
  }
}

// အားလုံးကို Read လုပ်ခြင်း
const markAllAsRead = async () => {
  if (unreadCount.value === 0) return
  try {
    // api service က auto token injection လုပ်ပေးတယ်
    await api.post('notifications/mark-all-read/', {})
    notifications.value = (Array.isArray(notifications.value) ? notifications.value : []).map((n) => ({ ...n, is_read: true }))
  } catch (err) {
    console.error('Mark all read failed:', err)
  }
}

// Logout လုပ်ခြင်း — SPA base path သုံးပြီး /app/login သို့ သွားမယ် (404 မဖြစ်အောင်)
const handleLogout = () => {
  if (confirm('စနစ်ထဲမှ ထွက်မှာ သေချာပါသလား?')) {
    authStore.logout()
    router.push(getLoginPath())
  }
}

// Click Outside ပိတ်ပေးရန်
const handleClickOutside = (event) => {
  if (!event.target.closest('.notification-area') && !event.target.closest('.profile-area')) {
    isNotifyOpen.value = false
    isProfileOpen.value = false
  }
}

// --- Computed ---
const unreadCount = computed(() => (Array.isArray(notifications.value) ? notifications.value : []).filter((n) => !n.is_read).length)

const formatDate = (dateStr) => {
  return new Date(dateStr).toLocaleString('en-GB', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}

// Dropdown ဖွင့်တိုင်း နောက်ဆုံး notification စာရင်း ပြန်ဆွဲခြင်း
watch(isNotifyOpen, (open) => {
  if (open) fetchNotifications()
})

// --- Lifecycle Hooks ---
onMounted(() => {
  fetchUserData()
  fetchNotifications()
  pollingTimer = setInterval(fetchNotifications, 15000) // 15 စက္ကန့်တစ်ခါစစ်
  window.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  if (pollingTimer) clearInterval(pollingTimer)
  window.removeEventListener('click', handleClickOutside)
})
</script>
