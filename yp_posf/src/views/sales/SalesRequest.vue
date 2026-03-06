<template>
  <!-- Full-bleed in main area: cancel layout padding so 12-col grid uses full width -->
  <div class="pos-layout flex flex-col flex-1 min-h-0 w-full max-w-full -m-4 md:-m-6 p-4 md:p-6" :class="posLang === 'my' ? 'font-myanmar pos-text' : ''">
    <!-- Mobile: Tab bar (Grid | Cart) - hidden on tablet/desktop (md+) -->
    <div class="flex md:hidden gap-2 mb-4 border-b border-border pb-2 shrink-0">
      <button
        type="button"
        class="flex-1 min-h-[80px] pos-text font-bold rounded-[12px] border-2 transition-colors"
        :class="mobilePosTab === 'products' ? 'bg-pos-teal text-white border-pos-teal' : 'bg-bg border-border text-fg'"
        @click="mobilePosTab = 'products'"
      >
        ပစ္စည်း
      </button>
      <button
        type="button"
        class="flex-1 min-h-[80px] pos-text font-bold rounded-[12px] border-2 transition-colors flex items-center justify-center gap-2"
        :class="mobilePosTab === 'cart' ? 'bg-pos-teal text-white border-pos-teal' : 'bg-bg border-border text-fg'"
        @click="mobilePosTab = 'cart'"
      >
        စာရင်း
        <span v-if="cart.length > 0" class="min-w-[32px] h-8 flex items-center justify-center rounded-full bg-white/20 text-sm">{{ cart.length }}</span>
      </button>
    </div>

    <!-- Grid: Left 60% = Products, Right 40% = Cart (Loyverse-style) -->
    <div class="pos-split flex-1 min-h-0 w-full gap-4 md:gap-6">
    <!-- Left (60%): Product search, categories, product cards -->
    <div
      class="pos-products flex flex-col min-w-0 w-full"
      :class="mobilePosTab === 'products' ? 'block' : 'hidden md:flex'"
    >
      <div class="pos-products-header flex flex-wrap items-center justify-between gap-2 sm:gap-3 mb-3 md:mb-4 shrink-0">
        <div class="flex items-center gap-2 md:gap-3 flex-wrap min-w-0">
            <h2 class="text-lg md:text-xl font-bold truncate" style="color: #000000;">ပစ္စည်းရွေးချယ်ရန်</h2>
            <span
              v-if="offlinePos.isOffline"
              class="text-xs font-bold px-2 py-1 rounded-lg bg-amber-500/20 text-amber-700 border border-amber-400/50"
            >
              Offline
            </span>
            <button
              v-if="offlinePos.isOffline"
              type="button"
              class="text-xs font-bold px-3 py-1.5 rounded-lg bg-pos-teal text-white border border-pos-teal hover:bg-pos-teal-700"
              @click="retryFetchProducts"
            >
              ပြန်ဆွဲမည်
            </button>
            <span
              v-if="offlinePos.isOnline && offlinePos.isSyncing"
              class="text-xs font-bold px-2 py-1 rounded-lg bg-gray-100 text-gray-700 border border-gray-300"
            >
              {{ offlinePos.syncProgressText || 'Syncing...' }}
            </span>
            <button
              v-else-if="offlinePos.isOnline && offlinePos.hasPendingSales"
              type="button"
              @click="syncNow"
              class="text-xs font-bold px-2 py-1 rounded-lg bg-rose-100 text-rose-700 border border-rose-300 hover:bg-rose-200"
            >
              Sync Now ({{ offlinePos.pendingCount }})
            </button>
            <span
              v-else-if="offlinePos.isOnline && offlinePos.lastSyncedAt"
              class="text-xs font-bold px-2 py-1 rounded-lg bg-emerald-100 text-emerald-700 border border-emerald-300"
            >
              Synced
            </span>
          </div>
          <div class="flex gap-2 flex-wrap items-center min-w-0 flex-1 md:flex-initial md:min-w-[280px]">
            <div class="flex gap-1 shrink-0">
              <button
                type="button"
                :class="posLang === 'my' ? 'bg-pos-teal text-white border-pos-teal' : 'bg-white text-black border-gray-300 hover:bg-gray-100'"
                class="min-h-[48px] px-3 rounded-[10px] border-2 text-sm font-bold"
                @click="posLang = 'my'"
              >MYA</button>
              <button
                type="button"
                :class="posLang === 'en' ? 'bg-pos-teal text-white border-pos-teal' : 'bg-white text-black border-gray-300 hover:bg-gray-100'"
                class="min-h-[48px] px-3 rounded-[10px] border-2 text-sm font-bold"
                @click="posLang = 'en'"
              >EN</button>
            </div>
            <div class="relative flex-1 min-w-0 w-full md:min-w-[200px]">
              <Search class="absolute left-3 md:left-4 top-1/2 -translate-y-1/2 w-8 h-8 md:w-10 md:h-10 text-fg-muted shrink-0" />
              <input
                v-model="searchQuery"
                @keyup.enter="handleBarcodeSearch"
                ref="searchInput"
                type="text"
                :placeholder="posLang === 'my' ? 'ပစ္စည်းရှာပါ...' : 'Search items here...'"
                class="w-full min-h-[56px] md:min-h-[64px] pl-11 md:pl-14 pr-3 md:pr-4 text-base md:text-xl font-semibold rounded-[12px] border-2 border-black bg-white"
                style="color: #000000;"
              />
            </div>
            <button
              type="button"
              @click="showScanner = true"
              class="min-h-[56px] md:min-h-[64px] min-w-[56px] md:min-w-[64px] flex items-center justify-center gap-1 md:gap-2 bg-bg border-2 border-black rounded-[12px] hover:bg-gray-100 shrink-0"
              style="color: #000000;"
              title="ကင်မရာဖြင့်စကင်န်"
            >
              <ScanLine class="w-8 h-8 md:w-10 md:h-10" />
              <span class="hidden sm:inline pos-text text-sm md:text-base">စကင်န်</span>
            </button>
          </div>
        </div>

        <!-- Category Tabs -->
        <div class="flex flex-wrap gap-2 mb-3 md:mb-4 shrink-0">
          <button
            type="button"
            class="min-h-[48px] md:min-h-[56px] px-4 md:px-6 font-semibold rounded-[12px] border-2 text-sm md:text-base"
            style="color: #000000; border-color: #000000; background: #ffffff;"
            :class="selectedCategoryId === null ? 'bg-pos-teal text-white border-pos-teal' : 'hover:bg-gray-100'"
            @click="selectedCategoryId = null"
          >
            {{ posLang === 'my' ? 'အားလုံး' : 'All' }}
          </button>
          <button
            v-for="cat in categories"
            :key="cat.id"
            type="button"
            class="min-h-[48px] md:min-h-[56px] px-4 md:px-6 font-semibold rounded-[12px] border-2 text-sm md:text-base"
            style="color: #000000; border-color: #000000; background: #ffffff;"
            :class="selectedCategoryId === cat.id ? 'bg-pos-teal text-white border-pos-teal' : 'hover:bg-gray-100'"
            @click="selectedCategoryId = cat.id"
          >
            {{ cat.name }}
          </button>
        </div>

        <SkeletonLoader v-if="productsLoading && filteredProducts.length === 0" :count="8" class="overflow-y-auto pr-2 flex-1 min-h-[200px] w-full" />
        <div
          v-else
          class="pos-product-grid overflow-y-auto pr-2 custom-scrollbar flex-1 min-h-0 w-full"
        >
          <div
            v-for="p in filteredProductsByCategory"
            :key="p.id"
            class="pos-product-card pos-product-card-span rounded-2xl overflow-hidden transition-all border border-gray-200 flex flex-col bg-white hover:shadow-lg hover:border-pos-teal/40"
            :class="[ posLang === 'my' ? 'pos-text' : '', isExpired(p) ? 'opacity-60 cursor-not-allowed' : 'cursor-pointer' ]"
            style="color: #000000;"
          >
            <div class="aspect-[4/5] max-h-[120px] bg-gray-100 flex items-center justify-center shrink-0 relative rounded-t-2xl overflow-hidden">
              <img
                v-if="p.image_url"
                :src="mediaUrl(p.image_url)"
                :alt="p.name"
                class="w-full h-full object-cover"
              />
              <span v-else class="text-3xl opacity-40">📦</span>
              <span v-if="isExpired(p)" class="absolute inset-0 flex items-center justify-center bg-red-900/40 text-white text-xs font-bold">{{ posLang === 'my' ? 'သက်တမ်းကုန်ပြီး' : 'Expired' }}</span>
            </div>
            <div class="p-3 flex flex-col flex-1 min-w-0">
              <h3 class="font-bold line-clamp-2 text-sm leading-tight" style="color: #000000;">{{ p.name }}</h3>
              <p class="mt-1 text-xs text-gray-500 line-clamp-2 min-h-[2rem]">{{ (p.description || '').trim() || (posLang === 'my' ? 'ပစ္စည်းအသေးစိတ်' : 'Product detail') }}</p>
              <div class="mt-auto pt-2 flex items-center justify-between gap-2">
                <div class="min-w-0">
                  <p class="font-bold text-sm text-gray-800">{{ formatMmk(itemDisplayPrice(p)) }} {{ posLang === 'my' ? 'ကျပ်' : 'MMK' }}{{ (p.base_unit_display && p.base_unit_display.split('/')[0]) ? `/${(p.base_unit_display.split('/')[0]).trim()}` : '' }}</p>
                  <p v-if="p.purchase_unit_factor && Number(p.purchase_unit_factor) > 1 && p.purchase_unit_display" class="text-xs text-gray-500 mt-0.5">{{ formatMmk(roundMmk((exchangeRate.priceInMmk(p) || p.retail_price || 0) * Number(p.purchase_unit_factor))) }} {{ posLang === 'my' ? 'ကျပ်' : 'MMK' }}/{{ (p.purchase_unit_display.split('/')[0] || '').trim() || 'ထုတ်' }}</p>
                </div>
                <button
                  type="button"
                  :disabled="isExpired(p)"
                  class="min-w-[40px] min-h-[40px] flex items-center justify-center rounded-xl bg-pos-teal text-white hover:bg-pos-teal-700 disabled:opacity-50 disabled:cursor-not-allowed shrink-0"
                  @click.stop="!isExpired(p) && onProductTap(p)"
                  aria-label="Add"
                >
                  <Plus class="w-5 h-5" />
                </button>
              </div>
              <p class="mt-1 text-xs text-gray-400">{{ posLang === 'my' ? 'လက်ကျန်' : 'Stock' }}: {{ p.total_stock ?? p.shop_stock ?? 0 }}</p>
              <p v-if="p.expiry_date && !isExpired(p) && isExpiringSoon(p)" class="mt-0.5 text-xs font-semibold text-amber-600">{{ posLang === 'my' ? 'သက်တမ်းကုန်ခါနီး' : 'Expiring soon' }}</p>
            </div>
          </div>
        </div>
      </div>

    <!-- Right (40%): Bills / Order summary (reference: Bills panel) -->
    <div
      class="pos-ticket flex flex-col bg-white rounded-2xl border border-gray-200 shadow-sm p-4 sm:p-6"
      :class="mobilePosTab === 'cart' ? 'block' : 'hidden md:flex'"
    >
      <h2 class="text-lg font-bold text-gray-800 mb-4" :class="posLang === 'my' ? 'pos-text' : ''">{{ posLang === 'my' ? 'ဘောက်ချာ' : 'Bills' }}</h2>
      <!-- ရောင်းပြီးပြီးချင်း စာရင်းပြန်ကြည့်ရန် / ပရင့်ထုတ်ရန် -->
      <div
        v-if="showSaleSuccessBanner && lastCompletedSaleId"
        class="mb-3 p-3 rounded-xl bg-emerald-50 border border-emerald-200 flex flex-wrap items-center gap-2"
      >
        <span class="text-emerald-800 font-medium text-sm">{{ posLang === 'my' ? 'အရောင်းအောင်မြင်ပါပြီ။' : 'Sale completed.' }}</span>
        <RouterLink
          :to="{ path: '/sales/history' }"
          class="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-emerald-600 text-white text-sm font-medium hover:bg-emerald-700"
        >
          {{ posLang === 'my' ? 'စာရင်းကြည့်ရန်' : 'View sales' }}
        </RouterLink>
        <button
          type="button"
          class="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-gray-600 text-white text-sm font-medium hover:bg-gray-700"
          @click="printLastCompletedSale"
        >
          {{ posLang === 'my' ? 'ပရင့်ထုတ်ရန်' : 'Print receipt' }}
        </button>
        <button
          type="button"
          class="ml-auto p-1 rounded text-gray-500 hover:bg-gray-200"
          aria-label="Close"
          @click="showSaleSuccessBanner = false"
        >
          <X class="w-4 h-4" />
        </button>
      </div>
      <div class="mb-3 md:mb-4 shrink-0">
        <label class="block text-fg-muted font-semibold mb-1 md:mb-2 pos-text text-sm md:text-base">ဖောက်သည်ရွေးချယ်ပါ</label>
        <select
          v-model="selectedCustomerId"
          class="w-full min-h-[56px] md:min-h-[64px] px-3 md:px-4 text-lg md:text-xl font-semibold text-fg bg-bg border border-border rounded-[12px] leading-myanmar"
        >
          <option :value="null">ဖောက်သည်မရွေးပါ</option>
          <option v-for="c in validCustomers" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>
      </div>

      <div v-if="saleLocations.length" class="mb-2 md:mb-3 shrink-0">
        <label class="block text-xs font-medium text-fg-muted mb-1">{{ posLang === 'my' ? 'ရောင်းချမည့်ဆိုင်' : 'Sale location' }}</label>
        <select
          v-model="selectedSaleLocationId"
          class="w-full min-h-[44px] px-3 rounded-[10px] border-2 border-border bg-white text-fg font-medium text-sm"
        >
          <option v-if="saleLocations.length > 1" value="">— {{ posLang === 'my' ? 'ရွေးပါ' : 'Select' }} —</option>
          <option v-for="loc in saleLocations" :key="loc.id" :value="loc.id">{{ loc.name }}</option>
        </select>
        <p v-if="saleLocations.length && !selectedSaleLocationId" class="text-amber-600 text-xs mt-1">{{ posLang === 'my' ? 'အရောင်းတင်မည်ဆိုင် ရွေးပါ' : 'Select sale location' }}</p>
      </div>
      <div v-else class="mb-2 p-2 rounded-lg bg-amber-50 border border-amber-200 text-amber-800 text-xs">
        {{ posLang === 'my' ? 'ရောင်းချရန်ဆိုင် သတ်မှတ်ခြင်း မရှိပါ။ Shop Locations နှင့် User Management မှ ဆိုင်ရွေးပါ။' : 'No sale location assigned. Set in Shop Locations & User Management.' }}
      </div>
      <div class="flex justify-between items-center mb-2 md:mb-3 shrink-0">
        <span class="font-semibold text-sm md:text-base" :class="posLang === 'my' ? 'pos-text' : ''">{{ posLang === 'my' ? 'စာရင်း' : 'Cart' }}</span>
        <span v-if="generatedInvoiceNo" class="text-fg-muted text-sm">#{{ generatedInvoiceNo }}</span>
      </div>
      <p v-if="cartExpiryWarning" class="mb-2 px-3 py-2 rounded-lg bg-amber-100 text-amber-800 text-sm font-medium">{{ cartExpiryWarning }}</p>
      <div class="flex-1 min-h-0 overflow-y-auto space-y-3 mb-4 pr-1 custom-scrollbar">
        <div
          v-for="(item, index) in cart"
          :key="index"
          class="p-3 bg-gray-50 rounded-xl border border-gray-200 flex gap-3 items-center"
        >
          <div class="w-12 h-12 rounded-full bg-gray-200 shrink-0 overflow-hidden flex items-center justify-center">
            <img v-if="item.image_url" :src="mediaUrl(item.image_url)" :alt="item.name" class="w-full h-full object-cover" />
            <span v-else class="text-lg opacity-50">📦</span>
          </div>
          <div class="min-w-0 flex-1">
            <p class="font-semibold text-gray-800 truncate pos-text">{{ item.name }}</p>
            <p v-if="item.serial_number" class="text-fg-muted text-[20px]">{{ item.serial_number }}</p>
            <div class="flex items-center gap-1.5 mt-1 flex-wrap">
              <button type="button" class="min-w-[36px] min-h-[36px] flex items-center justify-center rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-200 text-sm font-bold" @click="updateQty(index, -1)">−</button>
              <span class="min-w-[1.5rem] text-center font-bold pos-text text-sm">{{ formatQty(item.quantity) }}</span>
              <span class="text-gray-500 text-xs">{{ cartItemUnitLabel(item) }}</span>
              <button type="button" class="min-w-[36px] min-h-[36px] flex items-center justify-center rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-200 text-sm font-bold" @click="updateQty(index, 1)">+</button>
            </div>
          </div>
          <div class="flex items-center gap-2 shrink-0">
            <p class="font-bold pos-text text-gray-800 text-sm">{{ formatMmk(itemUnitPrice(item) * item.quantity) }} ကျပ်</p>
            <button type="button" class="min-w-[36px] min-h-[36px] flex items-center justify-center text-rose-600 hover:bg-rose-50 rounded-lg" @click="removeFromCart(index)" :aria-label="posLang === 'my' ? 'ဖယ်ရန်' : 'Remove'">
              <X class="w-5 h-5" />
            </button>
          </div>
        </div>
        <p v-if="cart.length === 0" class="text-fg-muted pos-text py-4 text-center">ပစ္စည်းမရှိသေးပါ။</p>
      </div>

      <div class="ticket-footer border-t border-border pt-4 space-y-2">
        <template v-if="posFeatures.enableDiscount">
          <div class="flex justify-between pos-text">
            <label class="text-fg-muted">လျှော့ဈေး</label>
          </div>
          <input
            v-model.number="discountAmount"
            type="number"
            min="0"
            step="1"
            class="w-full min-h-[56px] md:min-h-[64px] px-3 md:px-4 text-lg md:text-xl font-semibold text-fg bg-bg border border-border rounded-[12px] leading-myanmar"
            placeholder="၀"
          />
        </template>
        <template v-if="posFeatures.enableTax">
          <div class="flex justify-between pos-text">
            <label class="text-fg-muted">အခွန်</label>
          </div>
          <p class="text-fg-muted pos-text text-[20px]">အခွန်ကို ချိန်ညှိချက်မှ ဖွင့်ထားပါသည်။</p>
        </template>
        <template v-if="posFeatures.enableLoyalty">
          <div class="flex justify-between pos-text">
            <label class="text-fg-muted">အစုအဖွဲ့အမှတ်</label>
          </div>
          <p class="text-fg-muted pos-text text-[20px]">Loyalty ကို ချိန်ညှိချက်မှ ဖွင့်ထားပါသည်။</p>
        </template>
        <div class="flex justify-between font-semibold pos-text text-gray-600">
          <span>{{ posLang === 'my' ? 'စုစုပေါင်း' : 'Sub Total' }}</span>
          <span>{{ formatMmk(subtotal) }} ကျပ်</span>
        </div>
        <div v-if="posFeatures.enableTax" class="flex justify-between text-sm pos-text text-gray-500">
          <span>{{ posLang === 'my' ? 'အခွန် (VAT ပါဝင်)' : 'Tax (VAT Included)' }}</span>
          <span>{{ formatMmk(finalTotal - subtotal) }} ကျပ်</span>
        </div>
        <div class="flex justify-between font-bold pos-text text-emerald-600 text-base mt-1">
          <span>{{ posLang === 'my' ? 'ပေးချေရမည့်ပမာဏ' : 'Total' }}</span>
          <span>{{ formatMmk(finalTotal) }} ကျပ်</span>
        </div>

        <!-- POS Checkout: click payment = open checkout (amount tendered + change for cash) -->
        <template v-if="!generatedInvoiceNo">
          <div v-if="paymentMethods.length > 0" class="payment-buttons grid grid-cols-2 sm:grid-cols-3 gap-2 mt-3">
            <button
              v-for="pm in paymentMethods"
              :key="pm.id"
              type="button"
              class="min-h-[52px] rounded-xl font-bold leading-myanmar text-base border-0 transition-colors disabled:opacity-50"
              :class="paymentButtonClass(pm)"
              :disabled="cart.length === 0 || loading"
              @click="openCheckout(pm)"
            >
              <span class="pos-text">{{ paymentButtonLabel(pm.name) }}</span>
            </button>
          </div>
          <p class="mt-2 text-xs text-gray-500 pos-text">{{ posLang === 'my' ? 'ငွေပေးချေနည်းရွေးပြီး အမှာတင်မည်' : 'Select payment then place order' }}</p>
          <button
            v-if="paymentMethods.length === 0"
            type="button"
            class="w-full min-h-[56px] rounded-xl bg-gray-300 text-gray-600 font-bold cursor-not-allowed mt-3"
            disabled
          >
            {{ posLang === 'my' ? 'ငွေပေးချေမှုနည်းလမ်း မရှိပါ' : 'No payment method' }}
          </button>
        </template>
        <template v-else>
          <button type="button" class="w-full min-h-[52px] rounded-xl bg-pos-teal hover:bg-pos-teal-700 text-white font-bold flex items-center justify-center gap-2 mb-2 leading-myanmar" @click="printReceipt">
            <Printer class="w-5 h-5" /> {{ posLang === 'my' ? 'ဘောက်ချာပြန်ရိုက်မည်' : 'Print receipt' }}
          </button>
          <button type="button" class="w-full min-h-[80px] text-[25px] font-semibold text-fg-muted underline hover:text-fg leading-myanmar" @click="resetForm">အမှာစာအသစ်</button>
        </template>
      </div>
    </div>
    </div>

    <SerialInputModal :show="showSerialModal" @close="showSerialModal = false" @confirm="onSerialConfirm" />
    <UnitSelectorModal
      :show="showUnitModal"
      :mode="businessTypeStore.unitConversion ? 'hardware' : 'pharmacy'"
      @close="showUnitModal = false"
      @select="onUnitSelect"
    />

    <div
      v-if="showCustomerModal"
      class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50"
    ></div>

    <!-- AI Suggestion Modal -->
    <div
      v-if="showAISuggestion"
      class="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      @click.self="showAISuggestion = false"
    >
      <div class="w-full max-w-3xl max-h-[90vh] overflow-y-auto">
        <AIProductSuggestion
          @close="showAISuggestion = false"
          @select="handleAISelection"
        />
      </div>
    </div>

  <BarcodeScanner :show="showScanner" @scan="handleScanFromCamera" @close="showScanner = false" />

  <!-- Checkout modal: ပေးချေရမည့်ပမာဏ / ပေးလိုက်တဲ့ငွေ / ပြန်အမ်းရမည့်ငွေ -->
  <div v-if="showCheckoutModal" class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/50" @click.self="closeCheckout">
    <div class="bg-bg-card border border-border rounded-2xl shadow-xl max-w-md w-full p-6 pos-text" @click.stop>
      <h3 class="text-xl font-bold text-fg mb-4">ငွေပေးချေရန် (Checkout)</h3>
      <div class="space-y-4 mb-6">
        <div class="flex justify-between font-semibold text-fg">
          <span>ပေးချေရမည့်ပမာဏ</span>
          <span>{{ formatMmk(finalTotal) }} ကျပ်</span>
        </div>
        <template v-if="pendingPaymentMethod && isCashPayment(pendingPaymentMethod)">
          <div>
            <label class="block text-fg-muted font-semibold mb-2">ပေးလိုက်တဲ့ငွေ (Amount received)</label>
            <input
              ref="amountTenderedInputRef"
              v-model="amountTenderedInput"
              type="number"
              min="0"
              step="1"
              class="w-full min-h-[56px] px-4 text-[22px] font-bold text-fg bg-bg border border-border rounded-xl"
              placeholder="0"
              @keydown.enter="confirmCheckout"
            />
          </div>
          <div>
            <label class="block text-fg-muted font-semibold mb-2">ပြန်အမ်းရမည့်ငွေ (Change) — ရိုက်ထည့်နိုင်သည်</label>
            <input
              v-model="changeInputValue"
              type="number"
              min="0"
              step="1"
              class="w-full min-h-[56px] px-4 text-[22px] font-bold text-fg bg-bg border border-border rounded-xl"
              placeholder="0"
              @input="onChangeInput"
              @keydown.enter="confirmCheckout"
            />
          </div>
          <div v-if="changeInputValue !== '' && changeAmount >= 0" class="flex justify-between font-bold text-lg text-emerald-600">
            <span>ပေးလိုက်တဲ့ငွေ (တွက်ချက်)</span>
            <span>{{ formatMmk(finalTotal + (Number(changeInputValue) || 0)) }} ကျပ်</span>
          </div>
        </template>
        <template v-else>
          <p class="text-fg-muted text-[18px]">{{ pendingPaymentMethod ? paymentButtonLabel(pendingPaymentMethod.name) : '' }} ဖြင့် ပေးချေမည်။</p>
        </template>
      </div>
      <div class="flex gap-3">
        <button type="button" class="flex-1 min-h-[56px] font-bold rounded-xl border border-border bg-bg text-fg hover:bg-gray-100" @click="closeCheckout">
          မလုပ်ပါ
        </button>
        <button
          type="button"
          class="flex-1 min-h-[56px] font-bold rounded-xl bg-pos-teal text-white hover:bg-pos-teal-700 disabled:opacity-50"
          :disabled="pendingPaymentMethod && isCashPayment(pendingPaymentMethod) && (changeAmount < 0 || loading)"
          @click="confirmCheckout"
        >
          {{ loading ? 'ပြုလုပ်နေပါသည်...' : 'အရောင်းပြီးမည်' }}
        </button>
      </div>
    </div>
  </div>
  <!-- Hidden invoice for print-after-sale (ပရင့်ထုတ်ရန်) -->
  <InvoicePrint v-if="invoiceForPrint" :sale="invoiceForPrint" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, onUnmounted, nextTick, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { Search, X, Printer, ScanLine, Plus } from 'lucide-vue-next'
import AIProductSuggestion from '@/components/AIProductSuggestion.vue'
import CrossSellSuggestion from '@/components/CrossSellSuggestion.vue'
import InvoicePrint from '@/components/InvoicePrint.vue'
import SkeletonLoader from '@/components/SkeletonLoader.vue'
import BarcodeScanner from '@/components/BarcodeScanner.vue'
import SerialInputModal from '@/components/SerialInputModal.vue'
import UnitSelectorModal from '@/components/UnitSelectorModal.vue'
import { useToast } from '@/composables/useToast'
import { usePrintReceipt } from '@/composables/usePrintReceipt'
import { formatMmk, roundMmk } from '@/utils/currency'
import { startBarcodeListener, stopBarcodeListener } from '@/composables/useBarcodeListener'
import { useShopSettingsStore } from '@/stores/shopSettings'
import { useAuthStore } from '@/stores/auth'
import { useOfflinePosStore } from '@/stores/offlinePos'
import { usePosFeaturesStore } from '@/stores/posFeatures'
import { useExchangeRateStore } from '@/stores/exchangeRate'
import { useBusinessTypeStore } from '@/stores/businessType'
import { getConversionFactor, getUnitLabel, getPharmacyUnitLabel } from '@/utils/hardwareUnits'
import { mediaUrl } from '@/config'
import api from '@/services/api'

const toast = useToast()
const { printReceipt: doPrintReceipt } = usePrintReceipt()
const businessTypeStore = useBusinessTypeStore()

const shopStore = useShopSettingsStore()
const authStore = useAuthStore()
const posFeatures = usePosFeaturesStore()
/** ရောင်းချရန် ဆိုင်များ (me မှ assigned_locations_list) */
const saleLocations = computed(() => authStore.user?.assigned_locations_list || [])
const selectedSaleLocationId = ref(null)
const offlinePos = useOfflinePosStore()
const exchangeRate = useExchangeRateStore()
// Text input for USD rate so user can type (no spinner); synced to store
const usdRateInput = ref('')
function allowNumericOnly(val) {
  const s = String(val).replace(/[^\d.]/g, '')
  const parts = s.split('.')
  if (parts.length > 2) return parts[0] + '.' + parts.slice(1).join('')
  return s
}
const stopUsdRateWatch = watch(
  () => exchangeRate.usdExchangeRate,
  (v) => {
    try {
      if (usdRateInput != null && typeof usdRateInput.value !== 'undefined') {
        usdRateInput.value = v != null && v !== '' ? String(v) : ''
      }
    } catch (_) { /* ref may be torn down */ }
  },
  { immediate: true }
)
const isMounted = ref(true)
onBeforeUnmount(() => {
  isMounted.value = false
  stopUsdRateWatch?.()
})
const logoImage = computed(() => shopStore.logo_url || (import.meta.env.BASE_URL || '/') + 'logo.svg')

const products = computed(() => offlinePos.productsForPos)
const cart = ref([])
const customers = ref([])
const validCustomers = computed(() => (customers.value || []).filter((c) => c && (c.id != null)))
const selectedCustomerId = ref(null)
const loading = ref(false)
const productsLoading = ref(true)
const searchQuery = ref('')
const discountAmount = ref(0)
const generatedInvoiceNo = ref(null)
const showCustomerModal = ref(false)
const searchInput = ref(null)
const logoBase64 = ref('')

// Payment Method
const paymentMethods = ref([])
const selectedPaymentMethod = ref(null)
const showPaymentProofUpload = ref(false)
const paymentProofFile = ref(null)
const uploadingProof = ref(false)
const lastSaleId = ref(null)
const lastCompletedSaleId = ref(null)
const showSaleSuccessBanner = ref(false)
const invoiceForPrint = ref(null)
const showAISuggestion = ref(false)
const crossSellSuggestions = ref([])
const paymentMethodsLoading = ref(false)
const showScanner = ref(false)
const categories = ref([])
const selectedCategoryId = ref(null)
const showSerialModal = ref(false)
const showUnitModal = ref(false)
const pendingAddProduct = ref(null)
// Mobile tabbed POS: 'products' | 'cart' (FINAL MASTER BLUEPRINT §1)
const mobilePosTab = ref('products')

// POS display language: 'my' = Myanmar (မြန်မာ), 'en' = English (စာမြင်ရအောင် ခလုတ်နဲ့ပြောင်းမယ်)
const posLang = ref('my')

// AI: ဒါလေးရောမလိုဘူးလား + ဈ/ပရိုမိုး အကြံပြု (prompt မလို)
const aiSuggestions = ref([])
const aiSuggestLoading = ref(false)
const salePriceTip = ref('')
const salePromotionTip = ref('')
const aiAskQuestion = ref('')
const aiAskAnswer = ref('')
const aiAskLoading = ref(false)
let suggestDebounce = null

// --- Methods ---

// 1. Barcode / Quick add: Enter ခေါက်လိုက်ရင် SKU နဲ့တိုက်ရင် (သို့) ရှာထားတဲ့ ပထမဆုံး ပစ္စည်းကို Cart ထဲ တန်းထည့်မယ် (ဘာမှမသိရင်တောင် partial ရိုက်ပြီး Enter နဲ့ ရောင်းလို့ရအောင်)
const handleBarcodeSearch = () => {
  if (!searchQuery.value) return

  const query = searchQuery.value.toLowerCase().trim()
  const list = offlinePos.productsForPos
  const exactSku = list.find((p) => p.sku && p.sku.toLowerCase() === query)
  if (exactSku) {
    onProductTap(exactSku)
    searchQuery.value = ''
    nextTick(() => searchInput.value?.focus())
    return
  }
  const filtered = list.filter(
    (p) => p.name.toLowerCase().includes(query) || (p.sku && p.sku.toLowerCase().includes(query)),
  )
  if (filtered.length >= 1) {
    onProductTap(filtered[0])
    searchQuery.value = ''
    nextTick(() => searchInput.value?.focus())
  }
  // ရှာမတွေ့ရင် searchQuery ဒီအတိုင်းထား — စာရင်းကြည့်ပြီး ရွေးနိုင်မယ်
}

// Scan from camera: call products/search/?q= then add to cart or show toast
const handleScanFromCamera = async (code) => {
  showScanner.value = false
  const q = (code || '').trim()
  if (!q) return
  try {
    const res = await api.get('products/search/', { params: { q } })
    if (res.data?.found && res.data?.product) {
      const product = res.data.product
      const forCart = { ...product, total_stock: product.current_stock ?? product.total_stock }
      onProductTap(forCart)
      toast.success('ပစ္စည်းထည့်ပြီးပါပြီ')
    } else {
      searchQuery.value = q
      nextTick(() => searchInput.value?.focus())
      toast.error('No product found for this code. You can search or add manually.')
    }
  } catch (err) {
    toast.error(err.response?.data?.error || 'Search failed')
    searchQuery.value = q
    nextTick(() => searchInput.value?.focus())
  }
}

// Pharmacy: သက်တမ်းကုန်ပြီး ရောင်းလို့မရ / ကုန်ခါနီး သတိပေး
function isExpired(product) {
  const d = product.expiry_date
  if (!d) return false
  const today = new Date().toISOString().slice(0, 10)
  return String(d).slice(0, 10) < today
}
function isExpiringSoon(product, days = 30) {
  const d = product.expiry_date
  if (!d) return false
  const today = new Date()
  const exp = new Date(d)
  const diff = Math.ceil((exp - today) / (24 * 60 * 60 * 1000))
  return diff >= 0 && diff <= days
}

// 2. Add to Cart with Stock Check (opts: { serial_number?, unit?, quantity? })
const addToCart = (product, opts = {}) => {
  const qty = opts.quantity != null ? Number(opts.quantity) : 1
  if (qty < 0.01) return
  if (isExpired(product)) {
    toast.error(posLang.value === 'my' ? 'သက်တမ်းကုန်ပြီးသော ပစ္စည်းကို ရောင်းလို့မရပါ။' : 'Cannot sell expired product.')
    return
  }
  if (isExpiringSoon(product)) {
    toast.warning(posLang.value === 'my' ? 'သက်တမ်းကုန်ခါနီးပါသည်။ သတိထားပါ။' : 'Expiring soon. Please check.')
  }
  const existing = cart.value.find((i) => i.id === product.id && (i.serial_number || '') === (opts.serial_number || '') && (i.unit || '') === (opts.unit || ''))
  const currentInCart = existing ? existing.quantity : 0
  // Shopfloor only: use shop_stock (stock at selected sale location) so POS only allows selling what's on shopfloor
  const stock = product.shop_stock ?? product.total_stock ?? 0

  if (stock < currentInCart + qty) {
    toast.error(posLang.value === 'my' ? `လက်ကျန် မလုံလောက်ပါ (ဆိုင်တွင်လက်ကျန်: ${stock})` : `Insufficient stock at this location (${stock})`)
    return
  }

  if (existing) {
    existing.quantity += qty
  } else {
    cart.value.push({
      ...product,
      quantity: qty,
      serial_number: opts.serial_number || null,
      unit: opts.unit ?? 'piece',
    })
  }

  fetchCrossSellSuggestions()
  nextTick(() => searchInput.value?.focus())
}

const fetchCrossSellSuggestions = async () => {
  if (cart.value.length === 0) {
    crossSellSuggestions.value = []
    return
  }

  try {
    const productIds = cart.value.map(item => item.id)
    const res = await api.post('ai/cross-sell/', {
      product_ids: productIds,
      max_results: 6,
    })
    crossSellSuggestions.value = res.data.suggestions || []
  } catch (err) {
    console.error('Failed to fetch cross-sell suggestions:', err)
    crossSellSuggestions.value = []
  }
}

const handleCrossSellAdd = (product) => {
  onProductTap(product)
}

const fetchAiSuggestions = () => {
  if (cart.value.length === 0) {
    aiSuggestions.value = []
    salePriceTip.value = ''
    salePromotionTip.value = ''
    return
  }
  if (suggestDebounce) clearTimeout(suggestDebounce)
  suggestDebounce = setTimeout(async () => {
    aiSuggestLoading.value = true
    salePriceTip.value = ''
    salePromotionTip.value = ''
    try {
      // api service က auto token injection လုပ်ပေးတယ်
      const res = await api.post('ai/sale-auto-tips/', {
        product_ids: cart.value.map((i) => i.id),
        product_names: cart.value.map((i) => i.name),
      })
      aiSuggestions.value = res.data?.suggestions || []
      salePriceTip.value = res.data?.price_tip || ''
      salePromotionTip.value = res.data?.promotion_tip || ''
    } catch {
      aiSuggestions.value = []
      salePriceTip.value = ''
      salePromotionTip.value = ''
    } finally {
      aiSuggestLoading.value = false
    }
  }, 400)
}

const addSuggestedToCart = (s) => {
  const product = products.value.find((p) => p.id === s.product_id)
  if (product) onProductTap(product)
}

const handleAISelection = (product) => {
  const existingProduct = products.value.find((p) => p.id === product.id)
  if (existingProduct) onProductTap(existingProduct)
  else onProductTap(product)
}

// Watch cart changes to update cross-sell suggestions
watch(cart, () => {
  fetchCrossSellSuggestions()
}, { deep: true })

const submitAiAsk = async () => {
  const q = aiAskQuestion.value?.trim()
  if (!q || aiAskLoading.value) return
  aiAskLoading.value = true
  aiAskAnswer.value = ''
  try {
    // api service က auto token injection လုပ်ပေးတယ်
    const res = await api.post('ai/ask/', { question: q })
    aiAskAnswer.value = res.data?.answer || 'အဖြေမရပါ။'
  } catch {
    aiAskAnswer.value = 'ချိတ်ဆက်မှု မအောင်မြင်ပါ။'
  } finally {
    aiAskLoading.value = false
  }
}

watch(cart, () => fetchAiSuggestions(), { deep: true })

// When sale location changes: set session and refetch products so shop_stock is for that shopfloor
watch(selectedSaleLocationId, async (locId) => {
  if (!locId || !authStore.token) return
  try {
    await api.post('core/select-location/', { location_id: locId })
    await offlinePos.fetchProductsAndCache()
  } catch (_) {
    // ignore; products may still have cached stock
  }
})

// Payment methods: fetch once on mount (Staff and Admin both use same list endpoint)
onMounted(() => {
  fetchPaymentMethods()
})

const updateQty = (index, delta) => {
  const item = cart.value[index]
  const product = offlinePos.productsForPos.find((p) => p.id === item.id)
  // Shopfloor only: cap quantity by shop_stock at selected sale location (stock in base unit)
  const stock = product ? (product.shop_stock ?? product.total_stock ?? 0) : 0
  const factor = getUnitFactorForItem(item)
  const effectiveQty = item.quantity * factor

  if (delta > 0 && product && effectiveQty + factor > stock) {
    toast.error(posLang.value === 'my' ? `ဆိုင်တွင်လက်ကျန် မလုံလောက်ပါ (လက်ကျန်: ${stock})` : `Insufficient stock at this location (${stock})`)
    return
  }

  const newQty = item.quantity + delta
  if (newQty >= (item.unit ? 0.01 : 1)) {
    item.quantity = item.unit ? (Math.round(newQty * 100) / 100) : Math.max(1, Math.round(newQty))
  }
}

const removeFromCart = (index) => cart.value.splice(index, 1)

/** 1 လုံး တန်ဖိုး = base price။ ကဒ်/ဗူး စသည့် purchase unit ဆိုရင် 1 Purchase unit = X Base units ဖြစ်အောင် factor ယူမယ် (အပြောင်းအလဲရှိနေမယ်)။ */
function getUnitFactorForItem(item) {
  const unit = (item.unit || 'piece').toString().toLowerCase()
  if (!unit) return 1
  // ပစ္စည်းရဲ့ purchase unit (ကဒ်/ဗူး) နဲ့ ရွေးထားတာ ကိုက်ရင် 1 ကဒ် = purchase_unit_factor လုံး
  const purchaseCode = (item.purchase_unit_code || '').toLowerCase()
  if (purchaseCode && unit === purchaseCode) {
    const f = Number(item.purchase_unit_factor)
    return Number.isFinite(f) && f > 0 ? f : 1
  }
  // လုံး (base unit) သို့မဟုတ် ပစ္စည်းရဲ့ base_unit_code နဲ့ ကိုက်ရင် တစ်လုံးတန်ဖိုး
  if (unit === 'piece') return 1
  const baseCode = (item.base_unit_code || '').toLowerCase()
  if (baseCode && unit === baseCode) return 1
  // Hardware ယူနစ် (ဒါဇင်/ဖာ/ပေ စသည်)
  return getConversionFactor(item.unit)
}

// --- Unit price: base price (တစ်လုံးတန်ဖိုး) × unit factor (ကဒ်ဆိုရင် 1 ကဒ် = X လုံး) ---
const itemUnitPrice = (item) => {
  const basePrice = exchangeRate.priceInMmk(item) || item.retail_price || 0
  const factor = getUnitFactorForItem(item)
  return roundMmk(Number(basePrice) * factor)
}
const itemDisplayPrice = (product) => roundMmk(exchangeRate.priceInMmk(product) || product.retail_price || 0)
/** Display quantity: whole number for POS (MMK whole-number system) */
const formatQty = (qty) => {
  const n = Number(qty)
  if (Number.isNaN(n)) return '0'
  return n % 1 === 0 ? String(Math.round(n)) : String(Math.round(n * 100) / 100)
}
/** Cart line: unit label (လုံး/တစ်ကတ်/ဗူး for pharmacy, ခု/ဒါဇင်/... for hardware). Always show a unit. */
function cartItemUnitLabel(item) {
  if (item.unit_label) return item.unit_label
  const u = item.unit || 'piece'
  if (businessTypeStore.multiUnit && !businessTypeStore.unitConversion) return getPharmacyUnitLabel(u) || 'လုံး'
  return getUnitLabel(u) || 'ခု'
}
let saveRateDebounce = null
const onUsdRateInput = () => {
  const raw = usdRateInput.value
  const cleaned = allowNumericOnly(raw)
  if (cleaned !== raw) usdRateInput.value = cleaned
  const num = cleaned === '' ? null : parseFloat(cleaned)
  exchangeRate.setExchangeRate(num)
  if (saveRateDebounce) clearTimeout(saveRateDebounce)
  saveRateDebounce = setTimeout(async () => {
    const rate = exchangeRate.usdExchangeRate
    if (rate == null || Number(rate) <= 0) return
    try {
      await api.patch('settings/exchange-rate/', { usd_exchange_rate: Number(rate) })
    } catch (_) {
      // 403 if not admin – rate stays in local store for display only
    }
  }, 800)
}

// --- Computed & APIs ---
const subtotal = computed(() =>
  roundMmk(cart.value.reduce((sum, i) => sum + itemUnitPrice(i) * i.quantity, 0))
)
const finalTotal = computed(() => Math.max(0, roundMmk(subtotal.value - (discountAmount.value || 0))))

const filteredProducts = computed(() => {
  const list = offlinePos.productsForPos
  if (!searchQuery.value) return list
  const q = searchQuery.value.toLowerCase()
  return list.filter(
    (p) => p.name.toLowerCase().includes(q) || (p.sku && p.sku.toLowerCase().includes(q)),
  )
})

const filteredProductsByCategory = computed(() => {
  const list = filteredProducts.value
  if (selectedCategoryId.value == null) return list
  const cid = selectedCategoryId.value
  return list.filter((p) => p.category_id === cid || (p.category && p.category.id === cid) || p.category === cid)
})

// Cart items that are expiring soon (for AI / banner warning)
const cartExpiryWarning = computed(() => {
  const items = cart.value.filter((i) => i.expiry_date && isExpiringSoon(i))
  if (items.length === 0) return null
  return posLang.value === 'my'
    ? `သက်တမ်းကုန်ခါနီး ပစ္စည်း ${items.length} မျိုး စာရင်းထဲတွင်ရှိပါသည်။`
    : `${items.length} item(s) in cart are expiring soon.`
})

// Industry Engine: Pharmacy = 3-level units (hide serial). Solar/AC = Serial + Bundle + Site Survey. Phone/PC = Serial only. Hardware = Dozen/Bulk + Credit.
function onProductTap(product) {
  if (isExpired(product)) {
    toast.error(posLang.value === 'my' ? 'သက်တမ်းကုန်ပြီးသော ပစ္စည်းကို ရောင်းလို့မရပါ။' : 'Cannot sell expired product.')
    return
  }
  if (businessTypeStore.serialTracking && product.is_serial_tracked) {
    pendingAddProduct.value = product
    showSerialModal.value = true
    return
  }
  if (businessTypeStore.multiUnit || businessTypeStore.unitConversion) {
    pendingAddProduct.value = product
    showUnitModal.value = true
    return
  }
  addToCart(product)
}

function onSerialConfirm(serialNumber) {
  const product = pendingAddProduct.value
  pendingAddProduct.value = null
  if (!product) return
  addToCart(product, { serial_number: serialNumber })
}

function onUnitSelect(payload) {
  const product = pendingAddProduct.value
  pendingAddProduct.value = null
  if (!product) return
  // Pharmacy: payload is string (unit). Hardware: payload is { unit, quantity } (quantity can be fractional)
  if (typeof payload === 'string') {
    addToCart(product, { unit: payload })
  } else if (payload && typeof payload.unit === 'string') {
    addToCart(product, { unit: payload.unit, quantity: payload.quantity })
  }
}

const submitSaleRequest = async () => {
  if (cart.value.length === 0) return alert('ပစ္စည်းရွေးချယ်ပါ')
  if (!selectedPaymentMethod.value) return alert('ငွေပေးချေမှု နည်းလမ်း ရွေးချယ်ပါ')
  if (saleLocations.value.length && !selectedSaleLocationId.value) {
    return alert(posLang.value === 'my' ? 'ရောင်းချမည့်ဆိုင် ရွေးပါ။' : 'Select sale location.')
  }
  loading.value = true
  try {
    const pm = selectedPaymentMethod.value
    const payload = {
      customer: selectedCustomerId.value,
      discount_amount: roundMmk(discountAmount.value || 0),
      payment_method: typeof pm === 'object' && pm?.id != null ? pm.id : pm,
      sale_items: cart.value.map((i) => {
        const item = { product: i.id, quantity: i.quantity, unit_price: itemUnitPrice(i) }
        if (i.serial_number) item.serial_number = i.serial_number
        return item
      }),
    }
    if (selectedSaleLocationId.value) payload.sale_location = selectedSaleLocationId.value
    if (!posFeatures.requireSaleApproval) payload.auto_approve = true
    const result = await offlinePos.submitSale(payload)
    if (!isMounted.value) return
    if (result.ok && result.offline) {
      generatedInvoiceNo.value = 'PENDING (Offline)'
      alert('အင်တာနက်မရှိသေးသဖြင့် ဒေတာသိမ်းပြီး နောက်မှ အလိုအလျောက်တင်မည်။')
    } else if (result.ok) {
      generatedInvoiceNo.value = result.invoice_number || 'SUCCESS'
      lastSaleId.value = result.id || result.sale_id
      lastCompletedSaleId.value = result.id || result.sale_id
      showSaleSuccessBanner.value = true
      const pm = getSelectedPaymentMethod()
      showPaymentProofUpload.value = pm && pm.name.toLowerCase() !== 'cash' && pm.qr_code_url
      toast.success(posLang.value === 'my' ? 'အရောင်းအောင်မြင်ပါပြီ။ စာရင်းပြန်ကြည့်ရန် Sales History သို့ သွားပါ။' : 'Sale successful. Go to Sales History to view or print.')
      window.dispatchEvent(new CustomEvent('sale-completed'))
    } else {
      alert('Error: ' + (result.error || 'Unknown'))
    }
  } finally {
    if (isMounted.value) loading.value = false
  }
}

const resetForm = () => {
  cart.value = []
  generatedInvoiceNo.value = null
  discountAmount.value = 0
  selectedCustomerId.value = null
  selectedPaymentMethod.value = null
  showPaymentProofUpload.value = false
  paymentProofFile.value = null
  lastSaleId.value = null
  lastCompletedSaleId.value = null
  showSaleSuccessBanner.value = false
  lastAmountTendered.value = null
  lastChange.value = null
  nextTick(() => searchInput.value?.focus())
}

async function printLastCompletedSale() {
  const id = lastCompletedSaleId.value
  if (!id) return
  try {
    const res = await api.get(`invoice/${id}/`)
    invoiceForPrint.value = res.data
    await nextTick()
    setTimeout(() => window.print(), 300)
  } catch (err) {
    console.error('Print invoice error:', err)
    toast.error(posLang.value === 'my' ? 'Invoice ဆွဲယူ၍မရပါ။' : 'Could not load invoice.')
  }
}

const getSelectedPaymentMethod = () => {
  return paymentMethods.value.find(pm => pm.id === selectedPaymentMethod.value)
}

// --- Checkout modal: ပေးလိုက်တဲ့ငွေ / ပြန်အမ်းရမည့်ငွေ (POS-style) ---
const showCheckoutModal = ref(false)
const pendingPaymentMethod = ref(null)
const amountTenderedInput = ref('')
const amountTenderedInputRef = ref(null)
const changeInputValue = ref('')
const lastAmountTendered = ref(null)
const lastChange = ref(null)

const isCashPayment = (pm) => {
  if (!pm || !pm.name) return false
  const n = String(pm.name).toLowerCase()
  return n.includes('cash') || n === 'ငွေသား'
}

const changeAmount = computed(() => {
  if (!pendingPaymentMethod.value || !isCashPayment(pendingPaymentMethod.value)) return 0
  const tendered = roundMmk(Number(amountTenderedInput.value) || 0)
  return Math.max(0, roundMmk(tendered - finalTotal.value))
})

function onChangeInput() {
  const ch = Number(changeInputValue.value) || 0
  if (ch >= 0) amountTenderedInput.value = String(roundMmk(finalTotal.value + ch))
}

function openCheckout(pm) {
  pendingPaymentMethod.value = pm
  amountTenderedInput.value = String(roundMmk(finalTotal.value))
  changeInputValue.value = ''
  showCheckoutModal.value = true
  nextTick(() => {
    if (isCashPayment(pm) && amountTenderedInputRef.value) amountTenderedInputRef.value?.focus()
  })
}

function closeCheckout() {
  showCheckoutModal.value = false
  pendingPaymentMethod.value = null
  amountTenderedInput.value = ''
  changeInputValue.value = ''
}

async function confirmCheckout() {
  if (!pendingPaymentMethod.value) return
  if (isCashPayment(pendingPaymentMethod.value)) {
    const tendered = parseFloat(amountTenderedInput.value) || 0
    if (tendered < finalTotal.value) {
      toast.error('ပေးလိုက်တဲ့ငွေသည် ပေးချေရမည့်ပမာဏထက် နည်းနေပါသည်။')
      return
    }
    lastAmountTendered.value = roundMmk(tendered)
    const changeVal = changeInputValue.value !== '' ? (Number(changeInputValue.value) || 0) : changeAmount.value
    lastChange.value = roundMmk(changeVal)
  } else {
    lastAmountTendered.value = null
    lastChange.value = null
  }
  selectedPaymentMethod.value = pendingPaymentMethod.value.id
  closeCheckout()
  await submitSaleRequest()
}

// Fast payment: open checkout first, then complete (POS with change)
// Modes: Cash, KPay, WavePay, AYAPay, Card, Credit/အကြွေး (Master Blueprint §5)
function paymentButtonLabel(name) {
  if (!name) return ''
  const n = name.toLowerCase()
  if (n.includes('cash') || n === 'ငွေသား') return 'ငွေသား'
  if (n.includes('kpay')) return 'KPay'
  if (n.includes('wave')) return 'WavePay'
  if (n.includes('aya')) return 'AYAPay'
  if (n.includes('card') || n.includes('mpu')) return 'Card/MPU'
  if (n.includes('credit') || n.includes('အကြွေး') || n.includes('cre')) return 'အကြွေး'
  return name
}

function paymentButtonClass(pm) {
  const n = (pm.name || '').toLowerCase()
  if (n.includes('cash') || n === 'ငွေသား') return 'bg-pos-teal hover:bg-pos-teal-700 text-white'
  return 'bg-gray-600 hover:bg-gray-700 text-white'
}

async function submitWithPayment(paymentMethodId) {
  if (cart.value.length === 0) return
  selectedPaymentMethod.value = paymentMethodId
  await submitSaleRequest()
}

const handlePaymentProofFile = (event) => {
  const file = event.target.files?.[0]
  if (file) {
    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      alert('File size must be less than 5MB')
      return
    }
    // Validate file type
    if (!file.type.startsWith('image/')) {
      alert('Only image files are allowed')
      return
    }
    paymentProofFile.value = file
  }
}

const uploadPaymentProof = async () => {
  if (!paymentProofFile.value || !lastSaleId.value) return
  
  uploadingProof.value = true
  try {
    const formData = new FormData()
    formData.append('payment_proof', paymentProofFile.value)
    formData.append('payment_status', 'paid')
    
    // api service က auto token injection လုပ်ပေးတယ်
    const res = await api.post(
      `sales/${lastSaleId.value}/upload-payment-proof/`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    )
    
    alert('Payment proof uploaded successfully!')
    showPaymentProofUpload.value = false
    paymentProofFile.value = null
  } catch (error) {
    console.error(error)
    alert('Payment proof upload failed: ' + (error.response?.data?.error || error.message))
  } finally {
    uploadingProof.value = false
  }
}

const fetchPaymentMethods = async () => {
  paymentMethodsLoading.value = true
  try {
    // Prefer ViewSet list (payment-methods/) then list endpoint (payment-methods/list/) to avoid 404
    const res = await api.get('payment-methods/').catch(() => api.get('payment-methods/list/'))
    const data = res.data
    const list = Array.isArray(data) ? data : (data?.results ?? data?.data ?? [])
    const all = Array.isArray(list) ? list : []
    paymentMethods.value = all.filter((pm) => pm.is_active !== false)
  } catch (error) {
    console.warn('Payment methods fetch failed (using empty list):', error?.response?.status ?? error?.message)
    paymentMethods.value = []
    if (error?.response?.status !== 404) {
      toast.error(error.response?.data?.error || 'Payment methods could not be loaded')
    }
  } finally {
    paymentMethodsLoading.value = false
  }
}

const printReceipt = () => {
  doPrintReceipt({
    shopName: shopStore.shop_name || 'HoBo POS',
    invoiceNumber: generatedInvoiceNo.value || '',
    date: new Date(),
    items: cart.value.map((i) => ({
      name: i.name,
      quantity: i.quantity,
      unitPrice: itemUnitPrice(i),
      subtotal: roundMmk(itemUnitPrice(i) * i.quantity),
    })),
    discount: roundMmk(discountAmount.value || 0),
    total: finalTotal.value,
    amountTendered: lastAmountTendered.value != null ? roundMmk(lastAmountTendered.value) : undefined,
    change: lastChange.value != null ? roundMmk(lastChange.value) : undefined,
    widthMm: 80,
  })
}
const convertLogoToBase64 = () => {
  // Optional: load shop logo for receipt; receipt HTML can be extended to show logoBase64
  if (shopStore.logo_url) {
    fetch(shopStore.logo_url)
      .then((r) => r.blob())
      .then((blob) => {
        const reader = new FileReader()
        reader.onloadend = () => { logoBase64.value = reader.result }
        reader.readAsDataURL(blob)
      })
      .catch(() => {})
  }
}

/** Manual Sync Now (Task F - A to K recommendation) */
async function syncNow() {
  if (!offlinePos.isOnline || offlinePos.isSyncing) return
  await offlinePos.syncPendingSales()
}

/** Retry fetching products when Offline (e.g. after backend is back or fixed). */
async function retryFetchProducts() {
  productsLoading.value = true
  try {
    await offlinePos.fetchProductsAndCache()
    if (offlinePos.isOnline) {
      toast.success('ပစ္စည်းစာရင်း ပြန်ဆွဲပြီးပါပြီ')
    } else {
      toast.error('ချိတ်ဆက်မှု မအောင်မြင်ပါ။ Backend စတင်ထားပါသလား စစ်ပါ။')
    }
  } catch (e) {
    console.error(e)
    toast.error('ပြန်ဆွဲရန် မအောင်မြင်ပါ။')
  } finally {
    productsLoading.value = false
  }
}

// USB barcode scanner (keyboard wedge): same flow as camera scan
const onBarcodeScanned = (barcode) => {
  handleScanFromCamera(barcode)
}

onMounted(async () => {
  posFeatures.load()
  convertLogoToBase64()
  startBarcodeListener(onBarcodeScanned)
  fetchPaymentMethods()
  await authStore.fetchUserProfile()
  if (saleLocations.value.length === 1) selectedSaleLocationId.value = saleLocations.value[0].id
  await businessTypeStore.fetch()
  productsLoading.value = true
  try {
    await offlinePos.ensureProducts()
    await exchangeRate.fetchExchangeRate()
    const custRes = await api.get('customers/').catch(() => ({ data: [] }))
    const data = custRes.data
    customers.value = Array.isArray(data) ? data : (data?.results ?? data ?? [])
    if (customers.value.length === 0) {
      try {
        const created = await api.post('customers/', { name: 'Walk-in / ဖောက်သည်မရွေးပါ' })
        if (created?.data?.id) customers.value = [created.data]
      } catch (_) {
        // ignore if create fails (e.g. permission)
      }
    }
    const catRes = await api.get('categories/').catch(() => ({ data: [] }))
    const catData = catRes.data
    categories.value = Array.isArray(catData) ? catData : (catData?.results ?? catData ?? [])
    searchInput.value?.focus()
    fetchAiSuggestions()
  } catch (e) {
    console.error(e)
  } finally {
    productsLoading.value = false
  }
})

onUnmounted(() => {
  stopBarcodeListener()
})
</script>

<style scoped>
/* POS layout: mobile = 1 column; desktop = 12-column grid (ticket 4, products 8) */
.pos-layout {
  display: flex;
  flex-direction: column;
  min-height: 0;
  width: 100%;
  max-width: 100%;
  overflow: hidden;
}

.pos-split {
  display: grid;
  grid-template-columns: 1fr;
  flex: 1;
  min-height: 280px;
  align-items: stretch;
  width: 100%;
  gap: 1rem;
}

/* Desktop: 60% Products (left), 40% Cart (right) — Loyverse-style */
@media (min-width: 768px) {
  .pos-split {
    grid-template-columns: 60% 40%;
  }
  .pos-ticket {
    min-width: 0;
    min-height: 0;
    overflow: hidden;
    display: flex !important;
    flex-direction: column;
  }
  .pos-ticket .ticket-footer {
    flex-shrink: 0;
  }
  .pos-products {
    min-width: 0;
    width: 100%;
    max-width: 100%;
    min-height: 0;
    overflow: hidden;
    display: flex !important;
    flex-direction: column;
  }
}

.pos-product-card {
  font-size: clamp(14px, 1.5vw + 12px, 25px);
}

/* Product grid: ၂ခုစီပဲ (2 per row) */
.pos-product-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.75rem;
  overflow-x: hidden;
  overflow-y: auto;
  width: 100%;
  min-width: 0;
  align-content: start;
}
.pos-product-card-span {
  grid-column: span 1;
}
</style>
