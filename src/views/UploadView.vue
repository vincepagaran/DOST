<template>
  <v-app>
    <v-main>
      <v-container class="py-6">
        <div class="d-flex align-center mb-6">
          <v-btn icon @click="goBack">
            <v-icon>mdi-arrow-left</v-icon>
          </v-btn>
          <h3 class="ml-2 font-weight-bold">Upload Form A</h3>
        </div>

        <v-row>
          <!-- LEFT -->
          <v-col cols="12" md="6">
            <v-card variant="outlined" class="pa-5">
              <h4 class="mb-4">Upload your Form A (PDF or Image)</h4>

              <v-card
                variant="outlined"
                class="pa-8 mb-4 text-center d-flex flex-column align-center justify-center"
                height="200"
                style="cursor: pointer"
                @click="triggerFileInput"
              >
                <v-icon size="48" color="primary">mdi-upload</v-icon>
                <div class="mt-3">Click to upload</div>
                <div class="text-caption">PDF or Image (max 10MB)</div>
                <input
                  type="file"
                  ref="fileInput"
                  accept=".pdf, .jpg, .jpeg, .png"
                  class="d-none"
                  @change="handleFileChange"
                />
              </v-card>

              <v-card variant="outlined" class="pa-4">
                <div v-if="file">
                  <v-icon size="24" color="primary">mdi-file</v-icon>
                  <span class="ml-2">{{ file.name }}</span>
                </div>
                <div v-else>
                  <v-icon size="24" color="grey">mdi-file-remove</v-icon>
                  <span class="ml-2">No document uploaded</span>
                </div>
              </v-card>

              <v-btn
                color="primary"
                class="mt-4"
                block
                :loading="loading"
                :disabled="!file || loading"
                @click="startValidation"
              >
                START VALIDATION
              </v-btn>

              <v-alert
                v-if="serverError"
                type="error"
                class="mt-4"
                density="comfortable"
                border
                variant="tonal"
              >
                {{ serverError }}
              </v-alert>
            </v-card>
          </v-col>

          <!-- RIGHT -->
          <v-col cols="12" md="6">
            <v-card variant="outlined" class="pa-5">
              <div class="d-flex justify-space-between align-center">
                <div>
                  <h4 class="mb-1">Application Status</h4>
                  <div class="text-medium-emphasis">Document Submission Progress</div>
                </div>
                <div class="d-flex align-center">
                  <v-progress-circular
                    :model-value="progressPercent"
                    :size="90"
                    :width="10"
                    color="primary"
                  >
                    <span class="text-h6">{{ progressPercent }}%</span>
                  </v-progress-circular>
                </div>
              </div>
              <div class="text-right mt-2 text-medium-emphasis">
                {{ verifiedCount }} of {{ totalCount }} verified
              </div>

              <v-divider class="my-5"></v-divider>

              <h4 class="mb-3">MISSING FIELDS</h4>

              <div v-if="noResultsYet" class="text-medium-emphasis">
                Upload a file and click <strong>Start Validation</strong>.
              </div>

              <div v-else>
                <v-alert
                  v-if="allComplete"
                  type="success"
                  variant="tonal"
                  border
                  density="comfortable"
                  class="mb-4"
                >
                  Form A looks valid. All required fields are present.
                </v-alert>

                <template v-else>
                  <div class="mb-4" v-if="missing.personal.length">
                    <div class="text-subtitle-1 font-weight-bold">I. PERSONAL DATA</div>
                    <ul class="mt-2">
                      <li v-for="(item, i) in missing.personal" :key="'mp' + i">{{ item }}</li>
                    </ul>
                  </div>

                  <div class="mb-4" v-if="missing.family.length">
                    <div class="text-subtitle-1 font-weight-bold">II. FAMILY DATA</div>
                    <ul class="mt-2">
                      <li v-for="(item, i) in missing.family" :key="'mf' + i">{{ item }}</li>
                    </ul>
                  </div>

                  <div v-if="missing.financial.length">
                    <div class="text-subtitle-1 font-weight-bold">III. FINANCIAL CONTRIBUTION</div>
                    <ul class="mt-2">
                      <li v-for="(item, i) in missing.financial" :key="'mfi' + i">{{ item }}</li>
                    </ul>
                  </div>
                </template>

                <v-divider class="my-5"></v-divider>

                <h4 class="mb-3">FILLED FIELDS</h4>
                <div class="mb-4" v-if="filled.personal.length">
                  <div class="text-subtitle-1 font-weight-bold">I. PERSONAL DATA</div>
                  <ul class="mt-2">
                    <li v-for="(item, i) in filled.personal" :key="'fp' + i">{{ item }}</li>
                  </ul>
                </div>
                <div class="mb-4" v-if="filled.family.length">
                  <div class="text-subtitle-1 font-weight-bold">II. FAMILY DATA</div>
                  <ul class="mt-2">
                    <li v-for="(item, i) in filled.family" :key="'ff' + i">{{ item }}</li>
                  </ul>
                </div>
                <div v-if="filled.financial.length">
                  <div class="text-subtitle-1 font-weight-bold">III. FINANCIAL CONTRIBUTION</div>
                  <ul class="mt-2">
                    <li v-for="(item, i) in filled.financial" :key="'ffi' + i">{{ item }}</li>
                  </ul>
                </div>
              </div>
            </v-card>
          </v-col>
        </v-row>
      </v-container>
    </v-main>
  </v-app>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const file = ref(null)
const fileInput = ref(null)
const loading = ref(false)
const serverError = ref('')

const result = ref(null)

const noResultsYet = computed(() => result.value === null)
const totalCount = computed(() => result.value?.stats?.total ?? 0)
const verifiedCount = computed(() => result.value?.stats?.complete ?? 0)
const progressPercent = computed(() => result.value?.stats?.percent ?? 0)
const allComplete = computed(() => !noResultsYet.value && verifiedCount.value === totalCount.value)

const missing = computed(() => ({
  personal: result.value?.missing_fields?.personal ?? [],
  family: result.value?.missing_fields?.family ?? [],
  financial: result.value?.missing_fields?.financial ?? [],
}))

const filled = computed(() => ({
  personal: result.value?.filled_fields?.personal ?? [],
  family: result.value?.filled_fields?.family ?? [],
  financial: result.value?.filled_fields?.financial ?? [],
}))

const goBack = () => router.back()
const triggerFileInput = () => fileInput.value?.click()

const handleFileChange = (e) => {
  serverError.value = ''
  const f = e.target.files?.[0]
  if (!f) return
  const okType =
    /application\/pdf|image\/jpeg|image\/png/i.test(f.type) || /\.(pdf|jpg|jpeg|png)$/i.test(f.name)
  if (!okType) {
    serverError.value = 'Only PDF, JPG or PNG files are allowed.'
    file.value = null
    return
  }
  if (f.size > 10 * 1024 * 1024) {
    serverError.value = 'File is too large (max 10MB).'
    file.value = null
    return
  }
  file.value = f
}

const startValidation = async () => {
  serverError.value = ''
  if (!file.value) {
    serverError.value = 'Please upload a file first.'
    return
  }
  const formData = new FormData()
  formData.append('file', file.value)
  loading.value = true
  try {
    // thanks to Vite proxy, this reaches FastAPI w/o CORS
    const res = await fetch('/api/validate/formA?debug=0', {
      method: 'POST',
      body: formData,
    })
    const data = await res.json()
    if (!res.ok) {
      console.error('Server error:', data)
      serverError.value = data.detail || data.reason || 'Server error. Check backend console.'
      result.value = {
        stats: { total: 0, complete: 0, percent: 0 },
        missing_fields: { personal: [], family: [], financial: [] },
        filled_fields: { personal: [], family: [], financial: [] },
      }
      return
    }
    result.value = data
  } catch (err) {
    console.error(err)
    serverError.value = 'Could not reach the validation server. Is it running?'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.text-medium-emphasis {
  opacity: 0.7;
}
</style>
