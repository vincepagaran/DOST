<template>
  <v-app>
    <v-main>
      <v-container class="pa-4">
        <!-- Header -->
        <div class="d-flex align-center mb-6">
          <v-btn icon @click="goBack">
            <v-icon>mdi-arrow-left</v-icon>
          </v-btn>
          <h3 class="ml-2 font-weight-bold">Upload Documents</h3>
        </div>

        <!-- Loop through forms and render upload card for each -->
        <v-row>
          <v-col v-for="(form, index) in forms" :key="index" cols="12" md="6">
            <v-card outlined class="pa-4">
              <!-- Form Label -->
              <h4 class="mb-4">{{ form }}</h4>

              <!-- Upload Area -->
              <v-card
                outlined
                class="pa-6 mb-3 text-center d-flex flex-column align-center justify-center"
                height="160"
                style="cursor: pointer"
                @click="triggerFileInput(form)"
              >
                <v-icon size="40" color="primary">mdi-upload</v-icon>
                <p class="mt-2">Click to upload</p>
                <p class="text-caption">PDF or Image (max 10MB)</p>
                <input
                  type="file"
                  :ref="(el) => (fileInputs[form] = el)"
                  accept=".pdf, .jpg, .jpeg, .png"
                  class="d-none"
                  @change="handleFileUpload($event, form)"
                />
              </v-card>

              <!-- Preview -->
              <v-card outlined class="pa-4 text-center">
                <div v-if="files[form]">
                  <v-icon size="28" color="primary">mdi-file</v-icon>
                  <p class="mt-2">{{ files[form].name }}</p>
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
                :disabled="!files[form]"
                @click="startValidation(form)"
              >
                Start Validation
              </v-btn>
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

// Forms list
const forms = [
  'Form A',
  'Form B',
  'Form C',
  'Form D',
  'Form E',
  'Form E1',
  'Form E2',
  'Form E3',
  'Form E4',
  'Form E5',
  'Form F',
  'Form G',
  'Form H',
  'Form I',
  'Form J',
]

// Store selected files per form
const files = ref({})
const fileInputs = {}

const goBack = () => {
  router.back()
}

const triggerFileInput = (form) => {
  fileInputs[form]?.click()
}

const handleFileUpload = (event, form) => {
  const selectedFile = event.target.files[0]
  if (selectedFile && selectedFile.size <= 10 * 1024 * 1024) {
    files.value[form] = selectedFile
  } else {
    alert('File is too large or invalid format!')
  }
}

const startValidation = (form) => {
  if (!files.value[form]) {
    alert(`Please upload a document for ${form}`)
    return
  }
  console.log(`Validating ${form}:`, files.value[form])
  // TODO: connect to backend validation API
}
</script>
