<template>
  <v-container class="d-flex justify-center align-center fill-height">
    <v-card class="pa-8 rounded-xl" max-width="600">
      <!-- Logo + Title -->
      <div class="text-center mb-6">
        <v-img src="/logo.png" alt="Logo" contain max-width="80" class="mx-auto mb-2" />
        <h2 class="font-weight-bold">DOST Caraga</h2>
        <p class="text-subtitle-2 text-grey">Create Your Account</p>
      </div>

      <!-- Form -->
      <v-form ref="refVForm" @submit.prevent="register">
        <v-row dense>
          <!-- Full Name -->
          <v-col cols="12" md="6">
            <v-text-field
              v-model="fullName"
              label="Full Name"
              placeholder="Enter your name"
              prepend-inner-icon="mdi-account"
              outlined
              dense
              class="mb-3"
              :rules="[requiredValidator]"
            />
          </v-col>

          <!-- Email -->
          <v-col cols="12" md="6">
            <v-text-field
              v-model="email"
              label="Email"
              placeholder="Enter your email"
              prepend-inner-icon="mdi-email"
              outlined
              dense
              class="mb-3"
              :rules="[requiredValidator, emailValidator]"
            />
          </v-col>

          <!-- Username -->
          <v-col cols="12" md="6">
            <v-text-field
              v-model="username"
              label="Username"
              placeholder="Choose a username"
              prepend-inner-icon="mdi-account-circle"
              outlined
              dense
              class="mb-3"
              :rules="[requiredValidator]"
            />
          </v-col>

          <!-- Password -->
          <v-col cols="12" md="6">
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
              class="mb-3"
              :rules="[requiredValidator, passwordValidator]"
            />
          </v-col>

          <!-- Confirm Password -->
          <v-col cols="12">
            <v-text-field
              v-model="confirmPassword"
              :type="showConfirmPassword ? 'text' : 'password'"
              label="Confirm Password"
              placeholder="Re-enter password"
              prepend-inner-icon="mdi-lock-check"
              :append-inner-icon="showConfirmPassword ? 'mdi-eye-off' : 'mdi-eye'"
              @click:append-inner="showConfirmPassword = !showConfirmPassword"
              outlined
              dense
              class="mb-4"
              :rules="[requiredValidator, confirmPasswordValidator]"
            />
          </v-col>
        </v-row>

        <!-- Register Button -->
        <v-btn type="submit" color="primary" block class="mb-3"> Register </v-btn>
      </v-form>

      <!-- Already have account -->
      <div class="text-center">
        <p class="text-caption">
          Already have an account?
          <v-btn variant="text" size="small" color="primary" @click="$router.push('/')">
            Log In
          </v-btn>
        </p>
      </div>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref } from 'vue'
import { requiredValidator, emailValidator } from '@/utils/validators'

const fullName = ref('')
const email = ref('')
const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const showPassword = ref(false)
const showConfirmPassword = ref(false)

const refVForm = ref(null)

// Custom password validator (min 6 chars as example)
const passwordValidator = (value) => value?.length >= 6 || 'Password must be at least 6 characters'

// Confirm password validator
const confirmPasswordValidator = (value) => value === password.value || 'Passwords do not match'

const register = () => {
  refVForm.value?.validate().then(({ valid }) => {
    if (valid) {
      console.log('Registering:', {
        fullName: fullName.value,
        email: email.value,
        username: username.value,
        password: password.value,
      })

      // TODO: send data to backend
      alert('Registration successful!')
      window.location.href = '/'
    }
  })
}
</script>
