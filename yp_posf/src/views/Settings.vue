<template>
  <PageLayoutLoyverse title="Settings" :card="false" main-bg="var(--color-bg-light)">
    <div class="w-full max-w-[1600px] mx-auto space-y-4 sm:space-y-6 layout-container">
      <!-- Owner, Manager မဟုတ်ရင် ပြင်ခွင့်မရှိ ကြည့်ခွင့်သာ -->
      <div v-if="!canEditSettings" class="content-card p-4 rounded-xl border-amber-200 bg-amber-50 text-amber-800 text-sm font-medium">
        ပြင်ခွင့် မရှိပါ။ ကြည့်ခွင့်သာ ရှိပါသည်။ (Owner သို့မဟုတ် Manager သာ ချိန်ညှိခွင့်ရှိပါသည်။)
      </div>

      <!-- Technical settings: User Management, Roles (Owner/Manager only) -->
      <div v-if="canEditSettings" class="glass-card rounded-xl p-4 sm:p-5 md:p-6">
        <h2 class="text-base sm:text-lg font-semibold text-[var(--color-text)] mb-3 sm:mb-4">Management</h2>
        <div class="flex flex-wrap gap-2 sm:gap-3">
          <RouterLink
            to="/users"
            class="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium bg-[var(--color-primary)] text-white hover:opacity-90 transition min-h-[44px] items-center"
          >
            <Users class="w-4 h-4 shrink-0" /> User Management
          </RouterLink>
          <RouterLink
            to="/users/roles"
            class="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium border border-[var(--color-border)] text-[var(--color-text)] hover:border-[var(--color-primary)] hover:text-[var(--color-primary)] transition min-h-[44px] items-center"
          >
            <Shield class="w-4 h-4 shrink-0" /> Roles
          </RouterLink>
        </div>
      </div>

    <!-- Responsive grid: 1 col mobile, 2 col tablet+ -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-5 md:gap-6">
      <div class="settings-card settings-card-light glass-card p-4 sm:p-5 md:p-6 rounded-xl">
      <button
        type="button"
        @click="shopSectionOpen = !shopSectionOpen"
        class="w-full flex items-center justify-between text-left"
      >
        <h2 class="text-lg font-bold text-[#1a1a1a] flex items-center gap-2">
          <Store class="w-5 h-5 text-amber-600" />
          ဆိုင်အမည် နှင့် Logo
        </h2>
        <span class="text-[#6b7280] text-sm">
          {{ shopSectionOpen ? 'ပိတ်ရန် ▲' : 'ဖွင့်ရန် ▼' }}
        </span>
      </button>
      <div v-show="shopSectionOpen" class="mt-4">
      <p class="text-sm text-[#4b5563] mb-4">သင့်ဆိုင်ရဲ့ အမည်နဲ့ logo သတ်မှတ်ပါ</p>
      <form @submit.prevent="saveShop" class="space-y-4">
        <div>
          <label class="block mb-2 text-sm font-medium text-[#374151]">ဆိုင်အမည်</label>
          <input
            v-model="shopForm.shop_name"
            type="text"
            class="glass-input w-full px-4 py-3"
            placeholder="ဥပမာ - မြန်မာဂဟေဆော်ဆိုင်"
            :disabled="!canEditSettings"
          />
        </div>
        <div>
          <label class="block mb-2 text-sm font-medium text-[#374151]">Logo</label>
          <div class="flex items-center gap-4">
            <div class="w-16 h-16 rounded border border-[var(--color-border)] flex items-center justify-center overflow-hidden bg-[var(--color-bg-card)]">
              <img v-if="shopForm.logoPreview" :src="shopForm.logoPreview" class="w-full h-full object-contain" />
              <img v-else-if="shopStore.logo_url" :src="shopStore.logo_url" class="w-full h-full object-contain" />
              <span v-else class="text-xs text-[#9ca3af]">Logo</span>
            </div>
            <input
              type="file"
              accept="image/*"
              :disabled="!canEditSettings"
              @change="onLogoChange"
              class="text-sm text-[#1a1a1a] file:mr-2 file:py-2 file:px-4 file:rounded-lg file:border file:border-[var(--color-border)] file:bg-white file:text-[#1a1a1a]"
            />
          </div>
        </div>
        <div class="flex items-center gap-3 p-3 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-card)]">
          <input
            v-model="shopForm.filter_units_by_business_category"
            type="checkbox"
            id="filter_units"
            class="w-5 h-5 rounded accent-amber-500"
            :disabled="!canEditSettings"
          />
          <label for="filter_units" class="text-sm font-medium text-[#374151] cursor-pointer">
            ဆိုင်အမျိုးအစားအလိုက် unit ပဲပြမယ် (ပိတ်ရင် ယူနစ်အားလုံးပြမည်)
          </label>
        </div>
        <button
          v-if="canEditSettings"
          type="submit"
          :disabled="shopSaving"
          class="px-6 py-2.5 bg-amber-500 text-white rounded-xl font-bold hover:bg-amber-600 disabled:opacity-70"
        >
          {{ shopSaving ? 'သိမ်းနေပါသည်...' : 'သိမ်းပါ' }}
        </button>
        <p v-if="shopSuccess" class="text-emerald-600 text-sm font-medium mt-2">{{ shopSuccess }}</p>
      </form>
      </div>
      </div>

      <!-- License Key: always show remaining validity (Burmese) -->
      <div class="settings-card settings-card-light p-4 md:p-6">
        <h2 class="text-lg font-bold text-[#1a1a1a] mb-4 flex items-center gap-2">
          <Key class="w-5 h-5 text-amber-600" />
          လိုင်စင်ချိန်ညှိ
        </h2>
        <p class="text-sm text-[#4b5563] mb-3">လိုင်စင်ကုဒ်ပြောင်းလဲရန် သို့မဟုတ် အတည်ပြုရန်</p>
        <!-- Remaining validity: trial / licensed / grace / expired -->
        <div
          v-if="licenseStatusText"
          class="mb-4 p-4 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-card)] text-[#1a1a1a] text-sm md:text-base leading-relaxed"
        >
          {{ licenseStatusText }}
        </div>
        <RouterLink
          v-if="canEditSettings"
          to="/license-activate"
          class="inline-flex items-center gap-2 px-4 py-2 bg-amber-500 text-white rounded-xl font-bold hover:bg-amber-600 transition"
        >
          လိုင်စင်ချိန်ညှိရန်
        </RouterLink>
      </div>
    </div>

    <!-- Business Type (Industry Engine) -->
    <div class="settings-card p-4 md:p-6">
      <h2 class="text-xl font-bold text-fg mb-4 flex items-center gap-2">
        <Store class="w-6 h-6 text-primary" />
        လုပ်ငန်းအမျိုးအစား
      </h2>
      <p class="text-base text-fg-muted mb-4">ဆိုင်လုပ်ငန်းအမျိုးအစားရွေးပါ။ ပစ္စည်းထည့်သည့်အခါ IMEI/ယူနစ် စသည့် လုပ်ဆောင်ချက်များ ပြောင်းလဲမည်။</p>
      <div class="flex flex-wrap gap-3 items-center">
        <label class="text-base font-semibold text-fg">အမျိုးအစား</label>
        <select
          v-model="businessTypeValue"
          @change="saveBusinessType"
          class="a11y-select min-h-[80px] px-6 text-[25px] font-semibold text-fg bg-bg border border-border rounded-xl"
          aria-label="လုပ်ငန်းအမျိုးအစား"
          :disabled="!canEditSettings"
        >
          <option value="pharmacy_clinic">Pharmacy (ဆေးဆိုင်)</option>
          <option value="solar_aircon">Solar/AC</option>
          <option value="phone_electronics">Phone/PC (ဖုန်း/ကွန်ပျူတာ)</option>
          <option value="hardware_store">Hardware (သံ/ပစ္စည်း)</option>
          <option value="general_retail">General (ယေဘုယျ)</option>
        </select>
        <p v-if="businessTypeSaveStatus" class="text-base font-medium text-emerald-600">{{ businessTypeSaveStatus }}</p>
      </div>
    </div>

    <!-- Service & Installation toggles (solar/phone shops need; others may hide) -->
    <div class="settings-card p-4 md:p-6">
      <h2 class="text-xl font-bold text-fg mb-4 flex items-center gap-2">
        <Store class="w-6 h-6 text-primary" />
        ဝန်ဆောင်မှု / တပ်ဆင်မှု မီနူး
      </h2>
      <p class="text-base text-fg-muted mb-4">စက်ပြင်ဝန်ဆောင်မှု နှင့် တပ်ဆင်မှု မီနူးများကို ဖွင့်/ပိတ် ထားနိုင်သည်။ ဖုန်း/ကွန်ပျူတာ၊ ဆိုလာ စသည့်ဆိုင်များတွင် ဖွင့်ထားပါ။</p>
      <div class="space-y-4">
        <label class="flex items-center justify-between gap-4 cursor-pointer">
          <span class="text-base font-semibold text-fg">စက်ပြင်ဝန်ဆောင်မှု (Service)</span>
          <input type="checkbox" v-model="featureToggles.enable_service" :disabled="!canEditSettings" @change="saveFeatureToggles" class="w-6 h-6 rounded border-border" />
        </label>
        <label class="flex items-center justify-between gap-4 cursor-pointer">
          <span class="text-base font-semibold text-fg">တပ်ဆင်မှု (Installation)</span>
          <input type="checkbox" v-model="featureToggles.enable_installation" :disabled="!canEditSettings" @change="saveFeatureToggles" class="w-6 h-6 rounded border-border" />
        </label>
        <label class="flex items-center justify-between gap-4 cursor-pointer">
          <span class="text-base font-semibold text-fg">ကုသမှုမှတ်တမ်း (Treatment Records)</span>
          <input type="checkbox" v-model="featureToggles.enable_treatment_records" :disabled="!canEditSettings" @change="saveFeatureToggles" class="w-6 h-6 rounded border-border" />
        </label>
      </div>
    </div>

    <!-- ပစ္စည်းဖန်တီး ချိန်ညှိချက်များ (Warranty, Expiry, Model no, Units) -->
    <div class="settings-card p-4 md:p-6">
      <h2 class="text-xl font-bold text-fg mb-2 flex items-center gap-2">
        <Store class="w-6 h-6 text-primary" />
        ပစ္စည်းဖန်တီး ချိန်ညှိချက်များ
      </h2>
      <p class="text-base text-fg-muted mb-4">Add Product မှာ ပြမည့် အကွက်များကို အမှန်ချစ်နဲ့ ဖွင့်/ပိတ် ထားနိုင်သည်။ ယူနစ်များကို ရွေးပြီး သုံးလို့ရသည်။</p>
      <div class="space-y-4">
        <label class="flex items-center justify-between gap-4 cursor-pointer">
          <span class="text-base font-semibold text-fg">အာမခံသက်တမ်း (Warranty)</span>
          <input type="checkbox" v-model="productFieldSettings.show_warranty" :disabled="!canEditSettings" @change="saveProductFieldSettings" class="w-6 h-6 rounded border-border" />
        </label>
        <label class="flex items-center justify-between gap-4 cursor-pointer">
          <span class="text-base font-semibold text-fg">သက်တမ်းကုန်ရက် (Expiry date)</span>
          <input type="checkbox" v-model="productFieldSettings.show_expiry_date" :disabled="!canEditSettings" @change="saveProductFieldSettings" class="w-6 h-6 rounded border-border" />
        </label>
        <label class="flex items-center justify-between gap-4 cursor-pointer">
          <span class="text-base font-semibold text-fg">မော်ဒယ်နံပါတ် (Model number) — ဖုန်း/လျှပ်စစ်ပစ္စည်း</span>
          <input type="checkbox" v-model="productFieldSettings.show_model_number" :disabled="!canEditSettings" @change="saveProductFieldSettings" class="w-6 h-6 rounded border-border" />
        </label>
        <div class="pt-4 border-t border-[var(--color-border)]">
          <p class="text-sm font-bold text-fg mb-3">သုံးမည့်ယူနစ်များ (လိုအပ်ရင် အမှန်ချစ်ပြီး ရွေးပါ)</p>
          <div class="flex flex-wrap gap-3">
            <label
              v-for="u in allUnits"
              :key="u.id"
              class="inline-flex items-center gap-2 px-4 py-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-bg-card)] cursor-pointer hover:border-[var(--color-primary)]"
            >
              <input
                type="checkbox"
                :value="u.id"
                v-model="productFieldEnabledUnitIds"
                :disabled="!canEditSettings"
                @change="saveProductFieldUnits"
                class="w-4 h-4 rounded border-border"
              />
              <span class="text-sm font-medium text-fg">{{ u.name_my }} / {{ u.name_en }}</span>
            </label>
          </div>
          <div class="text-xs text-fg-muted mt-2 space-y-1">
            <p>အမှန်မချစ်ထားရင် ယူနစ်အားလုံး Add Product မှာ ပြမည်။</p>
            
          </div>
        </div>
      </div>
    </div>

    <!-- POS Feature Toggles (Tax, Discount, Loyalty) -->
    <div class="settings-card p-4 md:p-6">
      <h2 class="text-xl font-bold text-fg mb-4 flex items-center gap-2">
        <Store class="w-6 h-6 text-primary" />
        POS လုပ်ဆောင်ချက်များ
      </h2>
      <p class="text-base text-fg-muted mb-4">ဖွင့်/ပိတ်ထားသော လုပ်ဆောင်ချက်များကို POS မျက်နှာပြင်တွင်/မပြ ထိန်းချုပ်ပါ။</p>
      <div class="space-y-4">
        <label class="flex items-center justify-between gap-4 cursor-pointer">
          <span class="text-base font-semibold text-fg">အခွန် (Tax)</span>
          <input type="checkbox" v-model="posFeatures.enableTax" :disabled="!canEditSettings" @change="posFeatures.setEnableTax(posFeatures.enableTax)" class="w-6 h-6 rounded border-border" />
        </label>
        <label class="flex items-center justify-between gap-4 cursor-pointer">
          <span class="text-base font-semibold text-fg">လျှော့ဈေး (Discount)</span>
          <input type="checkbox" v-model="posFeatures.enableDiscount" :disabled="!canEditSettings" @change="posFeatures.setEnableDiscount(posFeatures.enableDiscount)" class="w-6 h-6 rounded border-border" />
        </label>
        <label class="flex items-center justify-between gap-4 cursor-pointer">
          <span class="text-base font-semibold text-fg">အစုအဖွဲ့အမှတ် (Loyalty Points)</span>
          <input type="checkbox" v-model="posFeatures.enableLoyalty" :disabled="!canEditSettings" @change="posFeatures.setEnableLoyalty(posFeatures.enableLoyalty)" class="w-6 h-6 rounded border-border" />
        </label>
        <label class="flex items-center justify-between gap-4 cursor-pointer">
          <span class="text-base font-semibold text-fg">အရောင်းအတည်ပြုချက် (Sale Approve) — ဖွင့်ထားရင် အမှန်ခြစ်ခြစ်မှ အတည်ပြုရမည်</span>
          <input type="checkbox" v-model="posFeatures.requireSaleApproval" :disabled="!canEditSettings" @change="posFeatures.setRequireSaleApproval(posFeatures.requireSaleApproval)" class="w-6 h-6 rounded border-border" />
        </label>
        <label class="flex items-center justify-between gap-4 cursor-pointer">
          <span class="text-base font-semibold text-fg">Dashboard / ခေါင်းစီးတွင် USD ဈေးနှုန်း ပြမည်</span>
          <input type="checkbox" v-model="posFeatures.showUsdRate" :disabled="!canEditSettings" @change="posFeatures.setShowUsdRate(posFeatures.showUsdRate)" class="w-6 h-6 rounded border-border" />
        </label>
      </div>
    </div>

    <!-- Exchange Rate (ဒေါ်လာဈေးနှုန်း): CBM scraping + manual edit, product price sync -->
    <div class="content-card p-4 md:p-6">
      <h2 class="text-lg font-bold text-[#1a1a1a] mb-2 flex items-center gap-2">
        <span class="text-2xl">💱</span>
        ဒေါ်လာဈေးနှုန်း (USD Exchange Rate)
      </h2>
      <p class="text-base text-[#4b5563] mb-4">
        မြန်မာဗဟိုဘဏ် (CBM) ဝဘ်မှ အလိုအလျောက်ဆွဲသုံးနိုင်သည် သို့မဟုတ် ကိုယ်ထိလက်ရောက်ပြင်နိုင်သည်။ ဈေးပြောင်းတိုင်း DYNAMIC_USD ပစ္စည်းဈေးများ အလိုအလျောက်ပြောင်းမည်။
      </p>
      <button
        type="button"
        @click="showExchangeRateModal = true"
        :class="[canEditSettings ? '' : 'opacity-60 cursor-not-allowed pointer-events-none', 'inline-flex items-center gap-2 min-h-[56px] px-5 py-2.5 rounded-xl font-bold bg-[#1078D1] text-white hover:bg-[#0d62a8] transition-colors']"
      >
        ဒေါ်လာဈေးနှုန်း ချိန်ညှိရန်
      </button>
      <RateManagementModal
        :is-open="showExchangeRateModal"
        @update:is-open="showExchangeRateModal = $event"
        @saved="() => {}"
      />
    </div>

    <!-- Payment Method Settings: full width -->
    <div class="settings-card settings-card-light p-4 md:p-6">
      <PaymentMethodSettings :read-only="!canEditSettings" />
    </div>

    <!-- Expense Category Settings: full width -->
    <div class="settings-card settings-card-light p-4 md:p-6">
      <ExpenseCategorySettings :read-only="!canEditSettings" />
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 md:gap-6">
      <div class="settings-card settings-card-light p-4 md:p-6">
        <h2 class="text-lg font-bold text-[#1a1a1a] mb-4 flex items-center gap-2">
          <User class="w-5 h-5 text-blue-600" />
          အကောင့်အချက်အလက်
        </h2>
        <p class="text-sm text-[#4b5563] mb-4">သင့်အကောင့်အချက်အလက်များ ကြည့်ရှုရန်</p>
        <p class="text-sm font-bold text-[#1a1a1a]">{{ user?.username || '—' }}</p>
        <p class="text-xs text-[#6b7280]">{{ user?.role_name || '—' }}</p>
      </div>

      <div class="settings-card settings-card-light p-4 md:p-6">
        <h2 class="text-lg font-bold text-[#1a1a1a] mb-4">HoBo POS</h2>
        <p class="text-sm text-[#4b5563]">အမျိုးအစား: Point of Sale & Inventory System</p>
        <p class="text-xs text-[#6b7280] mt-2">© {{ new Date().getFullYear() }} HoBo custom software pos</p>
      </div>
    </div>
    </div>
  </PageLayoutLoyverse>
</template>

<script setup>
import { ref, reactive, onMounted, watch, computed } from 'vue'
import { Key, User, Store, Users, Shield } from 'lucide-vue-next'
import PageLayoutLoyverse from '@/components/PageLayoutLoyverse.vue'
import api from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import { useShopSettingsStore } from '@/stores/shopSettings'
import { useBusinessTypeStore } from '@/stores/businessType'
import { usePosFeaturesStore } from '@/stores/posFeatures'
import { useFeatureTogglesStore } from '@/stores/featureToggles'
import { useProductFieldSettingsStore } from '@/stores/productFieldSettings'
import PaymentMethodSettings from './settings/PaymentMethodSettings.vue'
import ExpenseCategorySettings from './settings/ExpenseCategorySettings.vue'
import RateManagementModal from '@/components/RateManagementModal.vue'

const authStore = useAuthStore()
const canEditSettings = computed(() => {
  const r = (authStore.role || '').toLowerCase()
  return ['owner', 'admin', 'manager', 'super_admin'].includes(r)
})
const user = ref(null)
const showExchangeRateModal = ref(false)
const shopStore = useShopSettingsStore()
const businessTypeStore = useBusinessTypeStore()
const posFeatures = usePosFeaturesStore()
const featureToggles = useFeatureTogglesStore()
const productFieldSettings = useProductFieldSettingsStore()
const allUnits = ref([])
const productFieldEnabledUnitIds = ref([])
const businessTypeValue = ref('general_retail')
const businessTypeSaveStatus = ref('')

const saveFeatureToggles = async () => {
  try {
    await featureToggles.patch({
      enable_service: featureToggles.enable_service,
      enable_installation: featureToggles.enable_installation,
      enable_treatment_records: featureToggles.enable_treatment_records,
    })
  } catch (e) {
    console.error('Failed to save feature toggles', e)
  }
}

const saveProductFieldSettings = async () => {
  try {
    await productFieldSettings.patch({
      show_warranty: productFieldSettings.show_warranty,
      show_expiry_date: productFieldSettings.show_expiry_date,
      show_model_number: productFieldSettings.show_model_number,
    })
  } catch (e) {
    console.error('Failed to save product field settings', e)
  }
}

const saveProductFieldUnits = async () => {
  try {
    await productFieldSettings.patch({ enabled_unit_ids: productFieldEnabledUnitIds.value })
  } catch (e) {
    console.error('Failed to save enabled units', e)
  }
}

const saveBusinessType = async () => {
  businessTypeSaveStatus.value = ''
  try {
    await businessTypeStore.setBusinessType(businessTypeValue.value)
    businessTypeSaveStatus.value = 'သိမ်းပြီးပါပြီ။'
    setTimeout(() => { businessTypeSaveStatus.value = '' }, 2000)
  } catch (e) {
    businessTypeSaveStatus.value = 'မအောင်မြင်ပါ။'
  }
}
const shopForm = reactive({ shop_name: '', logoFile: null, logoPreview: null, filter_units_by_business_category: true })
// ဆိုင်အမည် နှင့် Logo ကဒ်ကို default ဖွင့်ထားမယ် (အစတုန်းက ရသလို ပြန်မြင်ရအောင်)
const shopSectionOpen = ref(true)
const shopSaving = ref(false)
const shopSuccess = ref('')
const licenseStatus = ref(null)

const licenseStatusText = computed(() => {
  const s = licenseStatus.value
  if (!s) return ''
  if (s.status === 'trial' && s.days_remaining != null) {
    return `အစမ်းသုံးနေပါသည်။ သက်တမ်း ${s.days_remaining} ရက်သာကျန်ပါတော့သည်။`
  }
  if (s.status === 'grace' && s.days_remaining != null) {
    return `Trial ကုန်ပြီး Grace period ထဲရှိပါသည်။ ${s.days_remaining} ရက်အတွင်း License ဝယ်ပါ။`
  }
  if (s.status === 'licensed') {
    return s.expires_at ? `လိုင်စင်မှန်ကန်ပါသည်။ သက်တမ်းကုန်ဆုံးရက်: ${s.expires_at.slice(0, 10)}` : 'လိုင်စင်မှန်ကန်ပါသည်။ (သက်တမ်းမကုန်)'
  }
  if (s.status === 'expired' || s.status === 'blocked') {
    return s.message || 'လိုင်စင် သက်တမ်းကုန်ပြီး သို့မဟုတ် ဝယ်ယူပါ။'
  }
  return s.message || ''
})

onMounted(async () => {
  try {
    const token = localStorage.getItem('access_token')
    if (token) {
      const res = await api.get('core/me/')
      user.value = res.data
    }
  } catch {
    // ignore
  }
  try {
    const res = await api.get('license/status/')
    licenseStatus.value = res.data
  } catch {
    licenseStatus.value = null
  }
  await shopStore.fetch()
  await businessTypeStore.fetch()
  businessTypeValue.value = businessTypeStore.business_type
  await featureToggles.fetch()
  await productFieldSettings.fetch()
  productFieldEnabledUnitIds.value = [...(productFieldSettings.enabled_unit_ids || [])]
  try {
    const uRes = await api.get('units/')
    allUnits.value = Array.isArray(uRes.data) ? uRes.data : (uRes.data?.results ?? [])
  } catch {
    allUnits.value = []
  }
  shopForm.shop_name = shopStore.shop_name
  shopForm.filter_units_by_business_category = shopStore.filter_units_by_business_category !== false
})

watch(shopSectionOpen, (v) => {
  localStorage.setItem('settings_shop_open', String(v))
})

const onLogoChange = (e) => {
  const file = e.target.files?.[0]
  if (file) {
    shopForm.logoFile = file
    shopForm.logoPreview = URL.createObjectURL(file)
  }
}

const saveShop = async () => {
  shopSaving.value = true
  shopSuccess.value = ''
  try {
    await shopStore.update({
      shop_name: shopForm.shop_name,
      logo: shopForm.logoFile,
      filter_units_by_business_category: shopForm.filter_units_by_business_category,
    })
    shopSuccess.value = 'သိမ်းဆည်းပြီးပါပြီ။'
    shopForm.logoFile = null
    shopForm.logoPreview = null
  } catch (e) {
    shopSuccess.value = e.response?.data?.detail || 'မအောင်မြင်ပါ။'
  } finally {
    shopSaving.value = false
  }
}
</script>
