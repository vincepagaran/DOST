<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { requiredValidator, emailValidator } from '@/utils/validators'
import { supabase } from '@/utils/supabase' // 👈 make sure supabase client is set up

const router = useRouter()

const roles = ['Admin', 'Scholar', 'Staff']
const activeTab = ref(0)
const email = ref('')
const password = ref('')
const showPassword = ref(false)
const refVForm = ref()

// For error/success messages
const errorMessage = ref('')
const loading = ref(false)

const login = async () => {
  errorMessage.value = ''
  refVForm.value?.validate().then(async ({ valid }) => {
    if (valid) {
      loading.value = true

      const { data, error } = await supabase.auth.signInWithPassword({
        email: email.value,
        password: password.value,
      })

      if (error) {
        console.error(error.message)
        errorMessage.value = 'Invalid email or password'
      } else if (data?.user) {
        console.log('Logged in as:', roles[activeTab.value], data.user)
        router.push('/dashboard') // 👈 redirect if login successful
      }

      loading.value = false
    }
  })
}

const goToRegister = () => {
  router.push('/register')
}
</script>

<template>
  <v-container class="login-bg d-flex justify-center align-center fill-height">
    <v-card class="pa-6 rounded-xl" max-width="400">
      <!-- Logo + Title -->
      <div class="text-center mb-4">
        <v-img src="/logo.png" alt="Logo" contain max-width="70" class="mx-auto mb-2" />
        <h2 class="font-weight-bold">DOST Caraga</h2>
        <p class="text-subtitle-2 text-grey">Document Validation System</p>
      </div>

      <!-- Tabs -->
      <v-tabs v-model="activeTab" class="mb-4" align-tabs="center">
        <v-tab v-for="role in roles" :key="role">
          {{ role }}
        </v-tab>
      </v-tabs>

      <!-- Form -->
      <v-form ref="refVForm" @submit.prevent="login">
        <!-- Email -->
        <v-text-field
          v-model="email"
          label="Email"
          placeholder="Enter Email"
          prepend-inner-icon="mdi-account"
          outlined
          dense
          class="mb-3"
          :rules="[requiredValidator, emailValidator]"
        />

        <!-- Password -->
        <v-text-field
          v-model="password"
          :type="showPassword ? 'text' : 'password'"
          label="Password"
          placeholder="Enter password"
          prepend-inner-icon="mdi-lock"
          :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
          @click:append-inner="showPassword = !showPassword"
          outlined
          dense
          class="mb-4"
          :rules="[requiredValidator]"
        />

        <!-- Error Message -->
        <v-alert v-if="errorMessage" type="error" border="start" class="mb-3" prominent>
          {{ errorMessage }}
        </v-alert>

        <!-- Login Button -->
        <v-btn :loading="loading" type="submit" color="primary" block class="mb-3"> Log In </v-btn>
      </v-form>

      <!-- Forgot Password + Register -->
      <div class="text-center">
        <v-btn variant="text" size="small" color="primary"> Forgot Password? </v-btn>
        <p class="text-caption text-grey mt-2">v1.0.0</p>

        <p class="text-caption mt-4">
          Don’t have an account?
          <v-btn variant="text" size="small" color="primary" @click="goToRegister">
            Register
          </v-btn>
        </p>
      </div>
    </v-card>
  </v-container>
</template>

<style scoped>
.login-bg {
  background: url('/background.jpg') no-repeat center center;
  background-size: cover;
  min-height: 100vh;
}
</style>
