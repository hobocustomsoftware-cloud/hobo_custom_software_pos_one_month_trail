<template>
  <div class="space-y-6 text-[#1a1a1a]">
    <div v-if="!hideHeader" class="flex flex-wrap justify-between items-center gap-4">
      <h1 class="text-xl font-semibold text-[#1a1a1a]">Category Management</h1>
      <button @click="openAddModal" class="loyverse-btn-primary px-5 py-2.5 flex items-center gap-2 rounded-xl text-sm font-medium text-white">
        <Plus class="w-4 h-4" /> ADD CATEGORY
      </button>
    </div>

    <FilterDataTable
      ref="tableRef"
      title="Categories"
      :light="hideHeader"
      :columns="columns"
      :data="categories"
      :total-count="totalCount"
      :loading="loading"
      search-placeholder="Category name ရှာပါ..."
      :default-page-size="20"
      empty-message="အမျိုးအစား မရှိသေးပါ။"
      @fetch-data="fetchData"
    >
      <template #cell-name="{ value }">
        <span class="font-semibold text-[#1a1a1a]">{{ value }}</span>
      </template>
      <template #cell-description="{ value }">
        <span class="text-[var(--color-fg-muted)] text-sm">{{ value || '–' }}</span>
      </template>
      <template #actions="{ row }">
        <div class="flex items-center justify-end gap-2">
          <button @click="openEditModal(row)" class="text-[var(--loyverse-blue)] font-medium text-sm hover:underline">EDIT</button>
          <button @click="deleteCategory(row.id)" class="text-rose-600 font-medium text-sm hover:underline">DELETE</button>
        </div>
      </template>
    </FilterDataTable>

    <div v-if="showModal" class="fixed inset-0 z-[100] flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="showModal = false" />
      <div class="bg-white w-full max-w-md p-8 relative z-10 rounded-xl border border-[var(--color-border)] shadow-xl">
        <h3 class="text-xl font-semibold text-[#1a1a1a] mb-6">
          {{ isEdit ? 'Edit Category' : 'Add Category' }}
        </h3>
        <form @submit.prevent="saveCategory" class="space-y-5">
          <div>
            <label class="block mb-2 text-sm font-medium text-[#374151]">Name</label>
            <input v-model="form.name" type="text" required class="glass-input w-full px-4 py-3 rounded-xl" />
          </div>
          <div>
            <label class="block mb-2 text-sm font-medium text-[#374151]">Description</label>
            <textarea v-model="form.description" class="glass-input w-full px-4 py-3 rounded-xl" rows="3" />
          </div>
          <div class="flex gap-3 pt-4">
            <button type="button" @click="showModal = false" class="loyverse-btn-secondary flex-1 py-3 rounded-xl">
              CANCEL
            </button>
            <button type="submit" :disabled="submitting" class="loyverse-btn-primary flex-1 py-3 rounded-xl text-white disabled:opacity-50">
              {{ submitting ? 'SAVING...' : 'CONFIRM' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { getLoginPath } from '@/router'
import { Plus } from 'lucide-vue-next'
import FilterDataTable from '@/components/FilterDataTable.vue'
import api from '@/services/api'

defineProps({
  hideHeader: { type: Boolean, default: false },
})
defineExpose({ openAddModal })

const router = useRouter()
const tableRef = ref(null)
const categories = ref([])
const totalCount = ref(0)
const loading = ref(false)
const showModal = ref(false)
const submitting = ref(false)
const isEdit = ref(false)
const currentId = ref(null)
const form = ref({ name: '', description: '' })

const columns = [
  { key: 'name', label: 'Category Name', sortable: true },
  { key: 'description', label: 'Description', sortable: false },
]

function fetchData({ search, page, pageSize, ordering }) {
  loading.value = true
  const params = { page, page_size: pageSize }
  if (search) params.search = search
  if (ordering) params.ordering = ordering
  api
    .get('categories/', { params })
    .then((res) => {
      categories.value = res.data.results ?? res.data ?? []
      totalCount.value = res.data.count ?? categories.value.length
    })
    .catch((err) => {
      if (err.response?.status === 401) {
        router.push(getLoginPath())
        return
      }
      categories.value = []
      totalCount.value = 0
    })
    .finally(() => {
      loading.value = false
    })
}

async function saveCategory() {
  submitting.value = true
  try {
    if (isEdit.value) {
      await api.patch(`categories/${currentId.value}/`, form.value)
    } else {
      await api.post('categories/', form.value)
    }
    showModal.value = false
    tableRef.value?.emitFetch()
  } catch (err) {
    if (err.response?.status === 401) router.push(getLoginPath())
    else alert('Failed to save category.')
  } finally {
    submitting.value = false
  }
}

function openAddModal() {
  isEdit.value = false
  form.value = { name: '', description: '' }
  showModal.value = true
}

function openEditModal(cat) {
  isEdit.value = true
  currentId.value = cat.id
  form.value = { name: cat.name, description: cat.description || '' }
  showModal.value = true
}

async function deleteCategory(id) {
  if (!confirm('Are you sure?')) return
  try {
    await api.delete(`categories/${id}/`)
    tableRef.value?.emitFetch()
  } catch (err) {
    alert('Cannot delete category')
  }
}
</script>
