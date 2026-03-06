<template>
  <PageLayoutLoyverse
    title="Items"
    :card="false"
    main-bg="#f4f4f4"
  >
    <template #actions>
      <!-- ADD ITEM ကို ဦးစွာထားပြီး responsive မှာ ပေါ်နေစေရန် -->
      <button
        v-if="activeTab === 'items'"
        type="button"
        class="loyverse-btn-primary px-4 py-2 sm:px-5 sm:py-2.5 rounded-xl text-sm font-medium text-white flex items-center gap-2 shrink-0"
        @click="productRef?.openAddModal?.()"
      >
        <Plus class="w-4 h-4" /> ADD ITEM
      </button>
      <router-link
        v-if="activeTab === 'items'"
        to="/products/import"
        class="loyverse-btn-secondary px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 shrink-0"
      >
        <Upload class="w-3.5 h-3.5" /> IMPORT
      </router-link>
      <button
        v-if="activeTab === 'items'"
        type="button"
        class="loyverse-btn-secondary px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 shrink-0"
        @click="productRef?.openPrintLabelsModal?.()"
      >
        <Printer class="w-3.5 h-3.5" /> PRINT
      </button>
      <button
        v-if="activeTab === 'categories'"
        type="button"
        class="loyverse-btn-primary px-4 py-2 sm:px-5 sm:py-2.5 rounded-xl text-sm font-medium text-white flex items-center gap-2 shrink-0"
        @click="categoryRef?.openAddModal?.()"
      >
        <Plus class="w-4 h-4" /> ADD CATEGORY
      </button>
    </template>

    <!-- Loyverse-style Tabs: Items | Categories | Modifiers -->
    <div class="bg-white rounded-t-xl border border-b-0 border-[var(--color-border)] px-4 pt-2">
      <div class="flex gap-0 border-b border-[var(--color-border)] -mb-px">
        <button
          type="button"
          class="loyverse-tab px-4 py-3 text-sm font-medium"
          :class="{ 'loyverse-tab-active': activeTab === 'items' }"
          @click="activeTab = 'items'"
        >
          Items
        </button>
        <button
          type="button"
          class="loyverse-tab px-4 py-3 text-sm font-medium"
          :class="{ 'loyverse-tab-active': activeTab === 'categories' }"
          @click="activeTab = 'categories'"
        >
          Categories
        </button>
        <button
          type="button"
          class="loyverse-tab px-4 py-3 text-sm font-medium"
          :class="{ 'loyverse-tab-active': activeTab === 'modifiers' }"
          @click="activeTab = 'modifiers'"
        >
          Modifiers
        </button>
      </div>
    </div>

    <!-- Tab content in white card -->
    <div class="bg-white rounded-b-xl border border-t-0 border-[var(--color-border)] shadow-sm min-h-[400px] p-4 md:p-6">
      <div v-show="activeTab === 'items'" class="text-[#1a1a1a]">
        <ProductManagement ref="productRef" hide-header />
      </div>
      <div v-show="activeTab === 'categories'" class="text-[#1a1a1a]">
        <CategoryManagement ref="categoryRef" hide-header />
      </div>
      <div v-show="activeTab === 'modifiers'">
        <ItemsModifiers />
      </div>
    </div>
  </PageLayoutLoyverse>
</template>

<script setup>
import { ref } from 'vue'
import { Plus, Upload, Printer } from 'lucide-vue-next'
import PageLayoutLoyverse from '@/components/PageLayoutLoyverse.vue'
import ProductManagement from '@/views/inventory/ProductManagement.vue'
import CategoryManagement from '@/views/inventory/CategoryManagement.vue'
import ItemsModifiers from '@/views/items/ItemsModifiers.vue'

const activeTab = ref('items')
const productRef = ref(null)
const categoryRef = ref(null)
</script>

<style scoped>
.loyverse-tab {
  color: var(--color-fg-muted);
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  transition: color 0.15s, border-color 0.15s;
}
.loyverse-tab:hover {
  color: var(--loyverse-blue);
}
.loyverse-tab-active {
  color: var(--loyverse-blue);
  border-bottom-color: var(--loyverse-blue);
}
</style>
