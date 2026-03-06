<template>
  <div class="flex-1 p-4 md:p-6 lg:p-8 space-y-6 max-w-[1600px] mx-auto bg-[#f4f4f4] min-h-full">
    <div class="flex justify-between items-center flex-wrap gap-4">
      <h1 class="text-2xl font-black text-[#1a1a1a] tracking-tight">
        ဆိုင်များ / ဆိုင်ခွဲ နှင့် နေရာများ
      </h1>
      <div class="flex items-center gap-3">
        <button
          @click="openSiteModal"
          class="bg-[#1078D1] hover:bg-[#0d62a8] text-white px-6 py-2.5 rounded-2xl font-bold border-0 transition flex items-center"
        >
          <Plus class="w-5 h-5 mr-2" /> ဆိုင်အသစ်
        </button>
        <button
          @click="openLocationModal"
          class="bg-[#1078D1] hover:bg-[#0d62a8] text-white px-6 py-2.5 rounded-2xl font-bold border-0 transition flex items-center"
        >
          <Plus class="w-5 h-5 mr-2" /> နေရာအသစ်
        </button>
      </div>
    </div>

    <div class="space-y-4">
      <h2 class="text-lg font-bold text-[#374151]">ဆိုင်များ / ဆိုင်ခွဲများ</h2>
      <div
        v-for="site in sites"
        :key="site.id"
        class="bg-white rounded-2xl overflow-hidden border border-[var(--color-border)] shadow-sm"
      >
        <div class="px-6 py-4 bg-[var(--color-bg-card)] border-b border-[var(--color-border)] flex justify-between items-center">
          <span class="font-bold text-[#1a1a1a]">{{ site.name }}</span>
          <span class="text-sm text-[#6b7280]">{{ site.locations_count }} နေရာ</span>
          <div class="flex gap-2">
            <button @click="editSite(site)" class="text-[#1078D1] font-semibold text-sm hover:underline">ပြင်မည်</button>
            <button @click="deleteSite(site.id)" class="text-rose-600 font-semibold text-sm hover:underline">ဖျက်မည်</button>
          </div>
        </div>
        <div class="divide-y divide-[var(--color-border)]">
          <div
            v-for="loc in locationsBySite(site.id)"
            :key="loc.id"
            class="px-6 py-4 flex items-center justify-between hover:bg-[var(--color-bg-card)]"
          >
            <div class="flex items-center gap-4">
              <span class="font-medium text-[#1a1a1a]">{{ loc.name }}</span>
              <span
                :class="loc.is_sale_location ? 'bg-blue-100 text-blue-800' : 'bg-amber-100 text-amber-800'"
                class="px-2 py-0.5 rounded text-xs font-bold uppercase border border-transparent"
              >
                {{ loc.is_sale_location ? 'ရောင်းချရန်' : 'ဂိုထောင်' }}
              </span>
            </div>
            <div class="flex gap-2">
              <button @click="editLocation(loc)" class="text-[#1078D1] font-semibold text-sm hover:underline">ပြင်မည်</button>
              <button @click="deleteLocation(loc.id)" class="text-rose-600 font-semibold text-sm hover:underline">ဖျက်မည်</button>
            </div>
          </div>
          <div v-if="locationsBySite(site.id).length === 0" class="px-6 py-4 text-[#6b7280] text-sm">
            ဤဆိုင်အောက်တွင် နေရာ မရှိသေးပါ
          </div>
        </div>
      </div>
      <p v-if="sites.length === 0" class="text-[#6b7280] text-sm">ဆိုင် မရှိသေးပါ။ ဆိုင်အသစ် ထည့်ပြီး အရောင်းဆိုင် + ဂိုထောင် တွဲထည့်နိုင်ပါသည်။</p>
    </div>

    <div class="space-y-4">
      <h2 class="text-lg font-bold text-[#374151]">သီးသန့် နေရာများ</h2>
      <div class="bg-white rounded-2xl overflow-hidden border border-[var(--color-border)] shadow-sm">
        <table class="w-full text-left">
          <thead class="bg-[var(--color-bg-card)] border-b border-[var(--color-border)]">
            <tr>
              <th class="px-6 py-4 text-xs font-bold text-[#6b7280] uppercase">အမည်</th>
              <th class="px-6 py-4 text-xs font-bold text-[#6b7280] uppercase text-center">အမျိုးအစား</th>
              <th class="px-6 py-4 text-xs font-bold text-[#6b7280] uppercase text-right">လုပ်ဆောင်ချက်</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-[var(--color-border)]">
            <tr v-for="l in standaloneLocations" :key="l.id" class="hover:bg-[var(--color-bg-card)]">
              <td class="px-6 py-4 font-medium text-[#1a1a1a]">{{ l.name }}</td>
              <td class="px-6 py-4 text-center">
                <span
                  :class="l.is_sale_location ? 'bg-blue-100 text-blue-800' : 'bg-amber-100 text-amber-800'"
                  class="px-2 py-0.5 rounded text-xs font-bold uppercase border border-transparent"
                >
                  {{ l.is_sale_location ? 'ရောင်းချရန်' : 'ဂိုထောင်' }}
                </span>
              </td>
              <td class="px-6 py-4 text-right space-x-2">
                <button @click="editLocation(l)" class="text-[#1078D1] font-semibold text-sm hover:underline">ပြင်မည်</button>
                <button @click="deleteLocation(l.id)" class="text-rose-600 font-semibold text-sm hover:underline">ဖျက်မည်</button>
              </td>
            </tr>
            <tr v-if="standaloneLocations.length === 0">
              <td colspan="3" class="px-6 py-8 text-center text-[#6b7280] text-sm">သီးသန့် နေရာ မရှိပါ</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Site modal: light -->
    <div v-if="showSiteModal" class="fixed inset-0 z-[100] flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-black/50" @click="showSiteModal = false"></div>
      <div class="bg-white w-full max-w-md p-6 md:p-8 rounded-2xl border border-[var(--color-border)] shadow-xl relative z-10">
        <h3 class="text-lg font-bold text-[#1a1a1a] mb-6">{{ isEditSite ? 'ဆိုင် ပြင်ဆင်မည်' : 'ဆိုင်အသစ် ထည့်မည်' }}</h3>
        <form @submit.prevent="saveSite" class="space-y-5">
          <div>
            <label class="block mb-1 text-sm font-medium text-[#374151]">ဆိုင်အမည်</label>
            <input v-model="siteForm.name" type="text" required class="glass-input w-full px-4 py-3 rounded-xl outline-none" />
          </div>
          <div>
            <label class="block mb-1 text-sm font-medium text-[#374151]">လိပ်စာ</label>
            <input v-model="siteForm.address" type="text" class="glass-input w-full px-4 py-3 rounded-xl outline-none" />
          </div>
          <div>
            <label class="block mb-1 text-sm font-medium text-[#374151]">ကုဒ် (ရွေးချယ်မှု)</label>
            <input v-model="siteForm.code" type="text" class="glass-input w-full px-4 py-3 rounded-xl outline-none" />
          </div>
          <div v-if="!isEditSite" class="flex items-center gap-3 p-4 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-card)]">
            <input v-model="siteForm.create_sales_and_warehouse" type="checkbox" id="create_pair" class="w-5 h-5 rounded accent-amber-500" />
            <label for="create_pair" class="text-sm font-semibold text-[#1a1a1a] cursor-pointer">အရောင်းဆိုင် + ဂိုထောင် တွဲထည့်မည်</label>
          </div>
          <div class="flex gap-3 pt-2">
            <button type="button" @click="showSiteModal = false" class="flex-1 py-3 font-bold rounded-xl border border-[var(--color-border)] bg-white text-[#1a1a1a] hover:bg-[#f3f4f6]">မလုပ်ပါ</button>
            <button type="submit" class="flex-1 py-3 bg-amber-500 text-white font-bold rounded-xl hover:bg-amber-600 transition">သိမ်းမည်</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Location modal: light -->
    <div v-if="showLocationModal" class="fixed inset-0 z-[100] flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-black/50" @click="showLocationModal = false"></div>
      <div class="bg-white w-full max-w-md p-6 md:p-8 rounded-2xl border border-[var(--color-border)] shadow-xl relative z-10 max-h-[90vh] overflow-y-auto">
        <h3 class="text-lg font-bold text-[#1a1a1a] mb-6">{{ isEditLocation ? 'နေရာ ပြင်ဆင်မည်' : 'နေရာအသစ်' }}</h3>
        <form @submit.prevent="saveLocation" class="space-y-5">
          <div>
            <label class="block mb-1 text-sm font-medium text-[#374151]">ဆိုင် (ရွေးချယ်မှု)</label>
            <select v-model="form.site" class="glass-input w-full px-4 py-3 rounded-xl outline-none">
              <option :value="null">သီးသန့် နေရာ</option>
              <option v-for="s in sites" :key="s.id" :value="s.id">{{ s.name }}</option>
            </select>
          </div>
          <div>
            <label class="block mb-1 text-sm font-medium text-[#374151]">နေရာအမည်</label>
            <input v-model="form.name" type="text" required class="glass-input w-full px-4 py-3 rounded-xl outline-none" />
          </div>
          <div>
            <label class="block mb-1 text-sm font-medium text-[#374151]">လိပ်စာ</label>
            <input v-model="form.address" type="text" class="glass-input w-full px-4 py-3 rounded-xl outline-none" />
          </div>
          <div>
            <label class="block mb-1 text-sm font-medium text-[#374151]">အမျိုးအစား</label>
            <select v-model="form.location_type" class="glass-input w-full px-4 py-3 rounded-xl outline-none">
              <option value="branch">ဆိုင်ခွဲ</option>
              <option value="shop_floor">ရောင်းချရန်နေရာ</option>
              <option value="warehouse">ဂိုဒေါင်</option>
            </select>
          </div>
          <div class="flex items-center gap-3 p-4 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-card)]">
            <input v-model="form.is_sale_location" type="checkbox" id="sale_loc" class="w-5 h-5 rounded accent-amber-500" />
            <label for="sale_loc" class="text-sm font-semibold text-[#1a1a1a] cursor-pointer">ရောင်းချရန် ဆိုင်ဖြစ်မည်</label>
          </div>
          <div>
            <label class="block mb-1 text-sm font-medium text-[#374151]">တာဝန်ကျ ဝန်ထမ်းများ</label>
            <div class="flex flex-wrap gap-2 p-4 rounded-xl max-h-28 overflow-y-auto border border-[var(--color-border)] bg-[var(--color-bg-card)]">
              <label v-for="u in users" :key="u.id" class="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" :value="u.id" v-model="form.staff_assigned" class="rounded accent-amber-500" />
                <span class="text-sm text-[#1a1a1a]">{{ u.username }}</span>
              </label>
              <span v-if="!users.length" class="text-[#6b7280] text-sm">ဝန်ထမ်း မရှိသေးပါ</span>
            </div>
          </div>
          <div class="flex gap-3 pt-2">
            <button type="button" @click="showLocationModal = false" class="flex-1 py-3 font-bold rounded-xl border border-[var(--color-border)] bg-white text-[#1a1a1a] hover:bg-[#f3f4f6]">မလုပ်ပါ</button>
            <button type="submit" class="flex-1 py-3 bg-amber-500 text-white font-bold rounded-xl hover:bg-amber-600 transition">သိမ်းမည်</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/services/api'
import { Plus } from 'lucide-vue-next'

const sites = ref([])
const locations = ref([])
const users = ref([])
const showSiteModal = ref(false)
const showLocationModal = ref(false)
const isEditSite = ref(false)
const isEditLocation = ref(false)
const currentSiteId = ref(null)
const currentLocationId = ref(null)

const siteForm = ref({
  name: '',
  address: '',
  code: '',
  create_sales_and_warehouse: true,
})

const form = ref({
  site: null,
  name: '',
  address: '',
  location_type: 'branch',
  is_sale_location: false,
  staff_assigned: [],
})

const locationsBySite = (siteId) => {
  return locations.value.filter((l) => l.site === siteId)
}

const standaloneLocations = computed(() => {
  return locations.value.filter((l) => !l.site)
})

const fetchData = async () => {
  try {
    const [sitesRes, locRes, empRes] = await Promise.all([
      api.get('sites-admin/'),
      api.get('locations-admin/'),
      api.get('core/employees/'),
    ])
    sites.value = Array.isArray(sitesRes.data) ? sitesRes.data : (sitesRes.data?.results ?? [])
    locations.value = Array.isArray(locRes.data) ? locRes.data : (locRes.data?.results ?? [])
    users.value = Array.isArray(empRes.data) ? empRes.data : (empRes.data?.results ?? [])
  } catch (err) {
    console.error('Fetch Error:', err)
  }
}

const openSiteModal = () => {
  isEditSite.value = false
  siteForm.value = { name: '', address: '', code: '', create_sales_and_warehouse: true }
  showSiteModal.value = true
}

const editSite = (site) => {
  isEditSite.value = true
  currentSiteId.value = site.id
  siteForm.value = { name: site.name, address: site.address || '', code: site.code || '', create_sales_and_warehouse: false }
  showSiteModal.value = true
}

const saveSite = async () => {
  try {
    if (isEditSite.value) {
      await api.patch(`sites-admin/${currentSiteId.value}/`, siteForm.value)
    } else {
      await api.post('sites-admin/', siteForm.value)
    }
    showSiteModal.value = false
    await fetchData()
  } catch (err) {
    alert(err.response?.data?.detail || JSON.stringify(err.response?.data) || 'သိမ်းဆည်းမှု မအောင်မြင်ပါ')
  }
}

const deleteSite = async (id) => {
  if (!confirm('ဤဆိုင်နှင့် အတွင်းနေရာများ ဖျက်မှာ သေချာပါသလား?')) return
  try {
    // api service က auto token injection လုပ်ပေးတယ်
    await api.delete(`sites-admin/${id}/`)
    fetchData()
  } catch (err) {
    alert(err.response?.data?.detail || 'ဖျက်ခြင်း မအောင်မြင်ပါ')
  }
}

const openLocationModal = () => {
  isEditLocation.value = false
  form.value = { site: null, name: '', address: '', location_type: 'branch', is_sale_location: false, staff_assigned: [] }
  showLocationModal.value = true
}

const editLocation = (l) => {
  isEditLocation.value = true
  currentLocationId.value = l.id
  form.value = {
    site: l.site || null,
    name: l.name,
    address: l.address || '',
    location_type: l.location_type || 'branch',
    is_sale_location: l.is_sale_location || false,
    staff_assigned: (l.staff_assigned || l.staff_names || []).map((x) => (typeof x === 'object' ? x.id : x)),
  }
  showLocationModal.value = true
}

const saveLocation = async () => {
  try {
    const payload = { ...form.value }
    if (payload.site === null || payload.site === '') payload.site = null
    if (isEditLocation.value) {
      await api.patch(`locations-admin/${currentLocationId.value}/`, payload)
    } else {
      await api.post('locations-admin/', payload)
    }
    showLocationModal.value = false
    await fetchData()
  } catch (err) {
    alert(err.response?.data?.detail || 'သိမ်းဆည်းမှု မအောင်မြင်ပါ')
  }
}

const deleteLocation = async (id) => {
  if (!confirm('ဤနေရာကို ဖျက်မှာ သေချာပါသလား?')) return
  try {
    // api service က auto token injection လုပ်ပေးတယ်
    await api.delete(`locations-admin/${id}/`)
    fetchData()
  } catch (err) {
    alert('ဖျက်ခြင်း မအောင်မြင်ပါ')
  }
}

onMounted(fetchData)
</script>
