<template>
  <v-app>
    <v-main>
      <v-container class="pa-4">
        <!-- Header -->
        <div class="flex align-center mb-6 d-flex">
          <v-btn icon @click="goBack"><v-icon>mdi-arrow-left</v-icon></v-btn>
          <h3 class="ml-2 font-weight-bold">Upload Form A</h3>
        </div>

        <v-row>
          <!-- Uploader -->
          <v-col cols="12" md="6">
            <v-card outlined class="pa-4">
              <h4 class="mb-4">I. PERSONAL DATA + II & III Checks</h4>

              <v-card
                outlined
                class="pa-6 mb-3 text-center d-flex flex-column align-center justify-center"
                height="160"
                style="cursor: pointer"
                @click="triggerInput"
              >
                <v-icon size="40" color="primary">mdi-upload</v-icon>
                <p class="mt-2">Click to upload</p>
                <p class="text-caption">PDF or Image (max 10MB)</p>
                <input
                  ref="fileInput"
                  type="file"
                  class="d-none"
                  accept=".pdf,application/pdf,image/*"
                  @change="onFile"
                />
              </v-card>

              <v-card outlined class="pa-4 text-center">
                <div v-if="file">
                  <v-icon size="28" color="primary">mdi-file</v-icon>
                  <p class="mt-2">{{ file.name }}</p>
                </div>
                <div v-else>
                  <v-icon size="28" color="grey">mdi-file-remove</v-icon>
                  <p class="mt-2">No document uploaded</p>
                </div>
              </v-card>

              <v-btn
                color="primary"
                block
                class="mt-4"
                :disabled="!file || loading"
                :loading="loading"
                @click="startValidation"
              >
                Start Validation
              </v-btn>
            </v-card>
          </v-col>

          <!-- Status / Missing-only Panel -->
          <v-col cols="12" md="6" v-if="panel.visible">
            <v-card class="pa-5">
              <div class="d-flex justify-space-between align-start">
                <div>
                  <h4 class="text-h6 mb-1">Application Status</h4>
                  <div class="text-body-2 text-medium-emphasis">Document Submission Progress</div>
                </div>
                <div class="d-flex flex-column align-center">
                  <v-progress-circular
                    :model-value="panel.percent"
                    :size="88"
                    :width="10"
                    color="primary"
                  >
                    <div class="text-subtitle-1 font-weight-bold">{{ panel.percent }}%</div>
                  </v-progress-circular>
                  <div class="text-caption mt-2">
                    {{ panel.complete }} of {{ panel.total }} verified
                  </div>
                </div>
              </div>

              <v-divider class="my-4" />

              <h4 class="text-h6 font-weight-bold">MISSING FIELDS</h4>

              <!-- I. PERSONAL DATA -->
              <div v-if="panel.personal.length" class="mt-4">
                <div class="text-subtitle-2 mb-2">I. PERSONAL DATA</div>
                <ul class="mt-1">
                  <li v-for="f in panel.personal" :key="f">{{ f }}</li>
                </ul>
              </div>

              <!-- II. FAMILY DATA -->
              <div v-if="panel.family.length" class="mt-4">
                <div class="text-subtitle-2 mb-2">II. FAMILY DATA</div>
                <ul class="mt-1">
                  <li v-for="f in panel.family" :key="f">{{ f }}</li>
                </ul>
              </div>

              <!-- III. FINANCIAL CONTRIBUTION -->
              <div v-if="panel.financial.length" class="mt-4">
                <div class="text-subtitle-2 mb-2">III. FINANCIAL CONTRIBUTION</div>
                <ul class="mt-1">
                  <li v-for="f in panel.financial" :key="f">{{ f }}</li>
                </ul>
              </div>

              <v-alert
                v-if="!panel.personal.length && !panel.family.length && !panel.financial.length"
                type="success"
                variant="tonal"
                class="mt-4"
                text="No missing fields detected in Form A."
              />
            </v-card>
          </v-col>
        </v-row>
      </v-container>
    </v-main>
  </v-app>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const file = ref(null)
const fileInput = ref(null)
const loading = ref(false)

const panel = reactive({
  visible: false,
  personal: [],
  family: [],
  financial: [],
  total: 0,
  complete: 0,
  percent: 0,
})

const goBack = () => router.back()
const triggerInput = () => fileInput.value?.click()

const onFile = (e) => {
  const f = e.target.files[0]
  if (!f) return
  if (f.size > 10 * 1024 * 1024) {
    alert('File is too large (max 10MB).')
    return
  }
  file.value = f
}

const startValidation = async () => {
  if (!file.value) return
  loading.value = true
  const fd = new FormData()
  fd.append('file', file.value)

  try {
    // if you set a Vite proxy to 8000, change URL to '/api/validate/formA'
    const res = await fetch('http://localhost:8000/api/validate/formA', {
      method: 'POST',
      body: fd,
    })
    let data
    try {
      data = await res.json()
    } catch {
      data = {}
    }

    if (!res.ok) {
      alert(data.detail || 'Server error')
      return
    }

    // build panel
    panel.personal = data?.missing_fields?.personal || []
    panel.family = data?.missing_fields?.family || []
    panel.financial = data?.missing_fields?.financial || []
    panel.total = data?.stats?.total || 0
    panel.complete = data?.stats?.complete || 0
    panel.percent = data?.stats?.percent || 0
    panel.visible = true
  } catch (e) {
    console.error(e)
    alert('Error connecting to validation server')
  } finally {
    loading.value = false
  }
}
</script>
