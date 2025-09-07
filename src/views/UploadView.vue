<template>
  <v-app>
    <v-main>
      <v-container class="pa-4 d-flex flex-column align-center">
        <!-- Header -->
        <div class="d-flex align-center mb-4 w-100">
          <v-btn icon @click="goBack">
            <v-icon>mdi-arrow-left</v-icon>
          </v-btn>
          <h3 class="ml-2 font-weight-bold">Upload Document</h3>
        </div>

        <!-- Upload Area (BIG Card) -->
        <v-card
          outlined
          class="pa-8 mb-4 text-center d-flex flex-column align-center justify-center"
          max-width="400"
          height="160"
          @click="triggerFileInput"
          style="cursor: pointer"
        >
          <v-icon size="40" color="primary">mdi-upload</v-icon>
          <p class="mt-2">Drag and drop or tap to upload</p>
          <p class="text-caption">PDF or Image files (max 10MB)</p>
          <input
            type="file"
            ref="fileInput"
            accept=".pdf, .jpg, .jpeg, .png"
            class="d-none"
            @change="handleFileUpload"
          />
        </v-card>

        <!-- Preview Box -->
        <v-card outlined class="pa-6 mb-4 text-center w-100" max-width="400">
          <div v-if="file">
            <v-icon size="32" color="primary">mdi-file</v-icon>
            <p class="mt-2">{{ file.name }}</p>
          </div>
          <div v-else>
            <v-icon size="32" color="grey">mdi-file-remove</v-icon>
            <p class="mt-2">No document selected</p>
          </div>
        </v-card>

        <!-- File Info -->
        <div class="text-center mb-4">
          <p class="text-caption">
            <v-icon small>mdi-file-pdf-box</v-icon>
            Supported formats: PDF, JPG, PNG
          </p>
          <p class="text-caption">Maximum file size: 10MB</p>
        </div>

        <!-- Start Validation Button -->
        <v-btn
          color="primary"
          block
          class="w-100"
          max-width="400"
          :disabled="!file"
          @click="startValidation"
        >
          Start Validation
        </v-btn>
      </v-container>
    </v-main>
  </v-app>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const file = ref(null)
const fileInput = ref(null)

const goBack = () => {
  router.back()
}

const triggerFileInput = () => {
  fileInput.value.click()
}

const handleFileUpload = (event) => {
  const selectedFile = event.target.files[0]
  if (selectedFile && selectedFile.size <= 10 * 1024 * 1024) {
    file.value = selectedFile
  } else {
    alert('File is too large or invalid format!')
  }
}

const startValidation = () => {
  if (!file.value) {
    alert('Please upload a document first!')
    return
  }
  console.log('Starting validation for:', file.value)
  // TODO: connect to backend validation API
}
</script>
