<template>
  <div class="multiselect-container">
    <div class="multiselect" :class="{ 'is-open': isOpen, 'is-disabled': disabled }">
          <!-- Only one arrow and one cross per tag, and stop click propagation on arrow -->
    <div class="multiselect__tags" @click="toggleDropdown">
      <div class="multiselect__tags-wrap" v-if="selectedOptions.length > 0">
        <span 
            v-for="(option) in selectedOptions"
            :key="option[trackBy]"
            class="multiselect__tag"
            @click.stop="selectOption(option)"
        >
            <span class="text-white">{{ option[label] }}</span>
            <span 
                class="multiselect__tag-remove"
                @click.stop="selectOption(option)"
            >×</span>


        </span>
      </div>
      <input
        ref="searchInput"
        v-model="searchQuery"
        :placeholder="selectedOptions.length === 0 ? placeholder : ''"
        class="multiselect__input"
        type="text"
        @focus="openDropdown"
        @keydown.down.prevent="highlightNext"
        @keydown.up.prevent="highlightPrev"
        @keydown.enter.prevent="selectHighlighted"
        @keydown.esc="closeDropdown"
        @keydown.delete="removeLastOption"
      />
      <div class="multiselect__select" @click.stop="toggleDropdown">
        <div class="multiselect__select-icon">▼</div>
      </div>
    </div>
      
      <transition name="multiselect">
        <div v-show="isOpen" class="multiselect__content-wrapper">
          <ul class="multiselect__content">
            <li 
              v-if="filteredOptions.length === 0"
              class="multiselect__element"
            >
              <span class="multiselect__option multiselect__option--disabled">
                Nenhuma opção encontrada
              </span>
            </li>
            <li
              v-for="(option, index) in filteredOptions"
              :key="option[trackBy]"
              class="multiselect__element"
              @click="selectOption(option)"
            >
              <span 
                class="multiselect__option"
                :class="{
                  'multiselect__option--highlight': index === highlightedIndex,
                  'multiselect__option--selected': isSelected(option)
                }"
              >
                <span class="multiselect__option-text">{{ option[label] }}</span>
                <span v-if="isSelected(option)" class="multiselect__option-check">✓</span>
              </span>
            </li>
          </ul>
        </div>
      </transition>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AppMultiselect',
  props: {
    modelValue: {
      type: Array,
      default: () => []
    },
    options: {
      type: Array,
      required: true
    },
    multiple: {
      type: Boolean,
      default: false
    },
    closeOnSelect: {
      type: Boolean,
      default: true
    },
    clearOnSelect: {
      type: Boolean,
      default: true
    },
    preserveSearch: {
      type: Boolean,
      default: false
    },
    placeholder: {
      type: String,
      default: 'Select option'
    },
    label: {
      type: String,
      default: 'label'
    },
    trackBy: {
      type: String,
      default: 'id'
    },
    preselectFirst: {
      type: Boolean,
      default: false
    },
    disabled: {
      type: Boolean,
      default: false
    }
  },
  emits: ['update:modelValue', 'select', 'remove', 'search-change'],
  data() {
    return {
      isOpen: false,
      searchQuery: '',
      highlightedIndex: -1
    }
  },
  computed: {
    selectedOptions() {
      return this.modelValue || []
    },
    filteredOptions() {
      if (!this.searchQuery) {
        return this.options
      }
      return this.options.filter(option => 
        option[this.label].toLowerCase().includes(this.searchQuery.toLowerCase())
      )
    }
  },
  watch: {
    searchQuery(newVal) {
      this.$emit('search-change', newVal)
      this.highlightedIndex = -1
    },
    isOpen(newVal) {
      if (newVal) {
        this.$nextTick(() => {
          this.$refs.searchInput?.focus()
        })
      }
    }
  },
  mounted() {
    document.addEventListener('click', this.handleClickOutside)
    
    if (this.preselectFirst && this.options.length > 0 && this.selectedOptions.length === 0) {
      this.selectOption(this.options[0])
    }
  },
  beforeUnmount() {
    document.removeEventListener('click', this.handleClickOutside)
  },
  methods: {
    toggleDropdown() {
      if (this.disabled) return
      this.isOpen = !this.isOpen
    },
    openDropdown() {
      if (this.disabled) return
      this.isOpen = true
    },
    closeDropdown() {
      this.isOpen = false
      this.highlightedIndex = -1
      if (!this.preserveSearch) {
        this.searchQuery = ''
      }
    },
    selectOption(option) {
      if (this.multiple) {
        const newValue = [...this.selectedOptions]
        const existingIndex = newValue.findIndex(item => item[this.trackBy] === option[this.trackBy])
        
        if (existingIndex > -1) {
          newValue.splice(existingIndex, 1)
          this.$emit('remove', option)
        } else {
          newValue.push(option)
          this.$emit('select', option)
        }
        
        this.$emit('update:modelValue', newValue)
        
        if (this.clearOnSelect) {
          this.searchQuery = ''
        }
        
        if (!this.closeOnSelect) {
          this.$nextTick(() => {
            this.$refs.searchInput?.focus()
          })
        } else {
          this.closeDropdown()
        }
      } else {
        this.$emit('update:modelValue', [option])
        this.$emit('select', option)
        this.closeDropdown()
      }
    },
    removeOption(option) {
      const newValue = this.selectedOptions.filter(item => item[this.trackBy] !== option[this.trackBy])
      this.$emit('update:modelValue', newValue)
      this.$emit('remove', option)
    },
    removeLastOption() {
      if (this.searchQuery === '' && this.selectedOptions.length > 0) {
        const lastOption = this.selectedOptions[this.selectedOptions.length - 1]
        this.removeOption(lastOption)
      }
    },
    isSelected(option) {
      return this.selectedOptions.some(item => item[this.trackBy] === option[this.trackBy])
    },
    highlightNext() {
      if (this.highlightedIndex < this.filteredOptions.length - 1) {
        this.highlightedIndex++
      }
    },
    highlightPrev() {
      if (this.highlightedIndex > 0) {
        this.highlightedIndex--
      }
    },
    selectHighlighted() {
      if (this.highlightedIndex >= 0 && this.filteredOptions[this.highlightedIndex]) {
        this.selectOption(this.filteredOptions[this.highlightedIndex])
      }
    },
    handleClickOutside(event) {
      if (!this.$el.contains(event.target)) {
        this.closeDropdown()
      }
    }
  }
}
</script>

<style scoped>
/* Dark theme for custom Multiselect */
.multiselect-container {
  position: relative;
  width: 100%;
}

.multiselect {
  position: relative;
  min-height: 40px;
  display: block;
  cursor: pointer;
}

.multiselect.is-disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.multiselect__tags {
  min-height: 40px;
  display: flex;
  align-items: center;
  padding: 8px 40px 8px 8px;
  border-radius: 5px;
  border: 1px solid #3d3d40;
  background: #2b2b2e;
  color: #e5e5e7;
  font-size: 14px;
  position: relative;
}

.multiselect.is-open .multiselect__tags {
  border-color: #0d6efd;
  box-shadow: 0 0 0 2px rgba(13,110,253,.35);
}

.multiselect__tags-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-right: 8px;
}

.multiselect__tag {
  display: inline-flex;
  align-items: center;
  background: #0d6efd;
  color: #fff;
  border-radius: 3px;
  padding: 2px 6px;
  font-size: 12px;
  line-height: 1.4;
  gap: 4px;
}

.multiselect__tag-icon {
  margin-left: 4px;
  cursor: pointer;
  font-weight: bold;
  font-size: 14px;
  line-height: 1;
}

.multiselect__tag-icon:hover {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 2px;
}

.multiselect__input {
  border: none;
  outline: none;
  background: transparent;
  color: #e5e5e7;
  flex: 1;
  min-width: 4em;
  font-size: 14px;
  padding: 0;
  appearance: none;
  -webkit-appearance: none;
}

.multiselect__input::placeholder {
  color: #b5b5b7;
}

.multiselect__select {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.multiselect__select-icon {
  font-size: 12px;
  color: #b5b5b7;
  transition: transform 0.2s;
}

.multiselect.is-open .multiselect__select-icon {
  transform: rotate(180deg);
}

.multiselect__content-wrapper {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  z-index: 1000;
  background: #262629;
  border: 1px solid #3d3d40;
  border-top: none;
  border-radius: 0 0 5px 5px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.4);
  max-height: 200px;
  overflow-y: auto;
}

.multiselect__content {
  list-style: none;
  margin: 0;
  padding: 0;
}

.multiselect__element {
  display: block;
}

.multiselect__option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  cursor: pointer;
  font-size: 14px;
  line-height: 1.4;
  background: #262629;
  color: #e5e5e7;
  transition: background-color 0.2s;
}
.multiselect__option:hover,
.multiselect__option--highlight {
  background: #0d6efd;
  color: #fff;
}
.multiselect__option--selected {
  background: #1c1c1e;
  color: #0d6efd;
}

.multiselect__option--disabled {
  color: #999;
  cursor: not-allowed;
}

.multiselect__option-text {
  flex: 1;
}

.multiselect__option-check {
  color: #0d6efd;
  font-weight: bold;
  margin-left: 8px;
}

/* Transitions */
.multiselect-enter-active,
.multiselect-leave-active {
  transition: all 0.2s ease;
}

.multiselect-enter-from,
.multiselect-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>