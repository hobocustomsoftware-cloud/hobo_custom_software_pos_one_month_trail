<template>
  <div
    :class="[
      'relative inline-flex items-center justify-center overflow-hidden bg-gray-200 rounded-full border-2 border-white shadow-sm',
      sizeClasses[size] || sizeClasses['medium'],
    ]"
  >
    <img v-if="src" :src="src" alt="User Avatar" class="w-full h-full object-cover" />

    <span v-else class="font-medium text-gray-600 uppercase">
      {{ initial }}
    </span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  src: {
    type: String,
    default: null,
  },
  name: {
    type: String,
    default: 'User',
  },
  size: {
    type: String,
    default: 'medium', // small, medium, large
  },
})

const initial = computed(() => props.name.charAt(0))

const sizeClasses = {
  small: 'w-8 h-8 text-xs',
  medium: 'w-10 h-10 text-sm',
  large: 'w-12 h-12 text-base',
}
</script>
