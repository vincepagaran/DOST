<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { requiredValidator, emailValidator } from '@/utils/validators'
import { supabase } from '@/utils/supabase'

const router = useRouter()

// Role tabs
const roles = ['Admin', 'Scholar', 'Staff']
const activeTab = ref(0)

// Form fields
const email = ref('')
const password = ref('')
const showPassword = ref(false)
const refVForm = ref()

// State
const errorMessage = ref('')
const loading = ref(false)

const login = async () => {
  errorMessage.value = ''
  refVForm.value?.validate().then(async ({ valid }) => {
    if (!valid) return

    loading.value = true

    try {
      // Step 1: login with email + password
      const { data, error } = await supabase.auth.signInWithPassword({
        email: email.value,
        password: password.value,
      })

      if (error) {
        console.error(error.message)
        errorMessage.value = 'Invalid email or password'
        loading.value = false
        return
      }

      const user = data?.user
      if (!user) {
        errorMessage.value = 'Login failed'
        loading.value = false
        return
      }

      // Step 2: fetch the user role from "users" table
      const { data: profile, error: profileError } = await supabase
        .from('users')
        .select('role')
        .eq('id', user.id)
        .single()

      if (profileError) {
        console.error(profileError.message)
        errorMessage.value = 'User role not found'
        loading.value = false
        return
      }

      const selectedRole = roles[activeTab.value]
      const userRole = profile?.role

      // Step 3: check if role matches the selected tab
      if (userRole !== selectedRole) {
        errorMessage.value = `You are registered as "${userRole}", not "${selectedRole}".`
        await supabase.auth.signOut()
        loading.value = false
        return
      }

      // ✅ Role matches → allow login
      console.log('Logged in as:', userRole, user)
      router.push('/dashboard')
    } catch (err) {
      console.error('Unexpected login error:', err)
      errorMessage.value = 'Something went wrong'
    }

    loading.value = false
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

      <!-- Role Tabs -->
      <v-tabs v-model="activeTab" class="mb-4" align-tabs="center">
        <v-tab v-for="role in roles" :key="role">
          {{ role }}
        </v-tab>
      </v-tabs>

      <!-- Login Form -->
      <v-form ref="refVForm" @submit.prevent="login">
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
