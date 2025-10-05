<template>
  <v-app>
    <v-main>
      <v-container class="pa-4">
        <div class="d-flex align-center mb-6">
          <v-btn icon @click="goBack">
            <v-icon>mdi-arrow-left</v-icon>
          </v-btn>
          <h3 class="ml-2 font-weight-bold">Upload Documents</h3>
        </div>

        <v-row>
          <v-col cols="12" md="6">
            <v-card outlined class="pa-4">
              <h4 class="mb-4">Form A</h4>

              <!-- Upload Area (PDF or Image) -->
              <v-card
                outlined
                class="pa-6 mb-3 text-center d-flex flex-column align-center justify-center"
                height="160"
                style="cursor: pointer"
                @click="triggerFileInput('Form A')"
              >
                <v-icon size="40" color="primary">mdi-upload</v-icon>
                <p class="mt-2">Click to upload</p>
                <p class="text-caption">PDF or Image (max 10MB)</p>
                <input
                  type="file"
                  :ref="(el) => (fileInputs['Form A'] = el)"
                  accept=".pdf,application/pdf,image/*"
                  class="d-none"
                  @change="handleFileUpload($event, 'Form A')"
                />
              </v-card>

              <!-- Preview -->
              <v-card outlined class="pa-4 text-center">
                <div v-if="files['Form A']">
                  <v-icon size="28" color="primary">mdi-file</v-icon>
                  <p class="mt-2">{{ files['Form A'].name }}</p>
                </div>
                <div v-else>
                  <v-icon size="28" color="grey">mdi-file-remove</v-icon>
                  <p class="mt-2">No document uploaded</p>
                </div>
              </v-card>

              <!-- Start Validation -->
              <v-btn
                color="primary"
                block
                class="mt-4"
                :disabled="!files['Form A']"
                @click="startValidation('Form A')"
              >
                Start Validation
              </v-btn>

              <!-- Validation Result -->
              <div v-if="results['Form A']" class="mt-3 text-left">
                <div v-if="results['Form A'].valid" class="text-success">
                  ✅ {{ results['Form A'].message }}
                </div>
                <div v-else class="text-error">
                  ❌ {{ results['Form A'].reason }}
                  <ul v-if="results['Form A'].details" class="mt-2">
                    <li v-for="(msg, key) in results['Form A'].details" :key="key">• {{ msg }}</li>
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
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const files = ref({})
const results = ref({})
const fileInputs = {}

const goBack = () => router.back()

const triggerFileInput = (form) => fileInputs[form]?.click()

const handleFileUpload = (event, form) => {
  const selectedFile = event.target.files[0]
  if (!selectedFile) return

  if (selectedFile.size > 10 * 1024 * 1024) {
    alert('File is too large (max 10MB).')
    event.target.value = ''
    return
  }

  files.value[form] = selectedFile
}

const startValidation = async (form) => {
  if (!files.value[form]) {
    alert('Please upload a document for Form A.')
    return
  }

  const formData = new FormData()
  formData.append('file', files.value[form])

  try {
    const res = await fetch('http://localhost:8000/api/validate/formA', {
      method: 'POST',
      body: formData,
    })

    // Try to read JSON; if it fails, make a generic object
    let data
    try {
      data = await res.json()
    } catch {
      data = {}
    }

    // Handle HTTP errors from FastAPI (it returns { detail: "..." })
    if (!res.ok) {
      const msg = data.detail || 'Server error'
      results.value[form] = { valid: false, reason: msg }
      alert('Validation failed: ' + msg)
      return
    }

    // Normal success/fail payload from our validator
    results.value[form] = data

    if (data.valid) {
      alert(data.message || 'Validation OK')
    } else {
      // Prefer detailed errors; fall back to reason; fall back to detail
      let more = ''
      if (data.details) {
        // support both {field: "msg"} and {missing_anchors: [...]}
        if (Array.isArray(data.details.missing_anchors)) {
          more = 'Missing anchors: ' + data.details.missing_anchors.join(', ')
        } else {
          more = Object.values(data.details).filter(Boolean).join('; ')
        }
      }
      more = more || data.reason || data.detail || 'Unknown validation error'
      alert('Validation failed: ' + more)
    }
  } catch (err) {
    console.error(err)
    alert('Error connecting to validation server')
  }
}
</script>
