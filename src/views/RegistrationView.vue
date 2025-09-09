<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  requiredValidator,
  emailValidator,
  passwordValidator,
  confirmedValidator,
} from '@/utils/validators'
import { supabase } from '@/utils/supabase'

const router = useRouter()

// Roles
const roles = ['Admin', 'Scholar', 'Staff']
const selectedRole = ref('Scholar') // default role

// Form data
const firstname = ref('')
const lastname = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const showPassword = ref(false)
const showConfirmPassword = ref(false)

const refVForm = ref()
const loading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

// Submit Registration
const register = async () => {
  errorMessage.value = ''
  successMessage.value = ''

  refVForm.value?.validate().then(async ({ valid }) => {
    if (!valid) return

    loading.value = true
    try {
      // Step 1: Create auth account
      const { data, error } = await supabase.auth.signUp({
        email: email.value,
        password: password.value,
        options: {
          data: {
            firstname: firstname.value,
            lastname: lastname.value,
            role: selectedRole.value,
          },
        },
      })

      if (error) throw error
      const user = data?.user

      if (user) {
        // Step 2: Insert role + info into users table
        const { error: insertError } = await supabase.from('users').insert([
          {
            id: user.id,
            email: email.value,
            role: selectedRole.value,
          },
        ])
        if (insertError) throw insertError

        successMessage.value = 'Successfully registered. You can now log in.'
        setTimeout(() => {
          router.push('/')
        }, 2000)
      }
    } catch (err) {
      console.error('Registration error:', err.message)
      errorMessage.value = err.message || 'Registration failed'
    }
    loading.value = false
  })
}
</script>

<template>
  <v-container class="register-bg d-flex justify-center align-center fill-height">
    <v-card class="pa-8 rounded-xl register-card">
      <!-- Logo + Title -->
      <div class="text-center mb-6">
        <v-img src="/logo.png" alt="Logo" contain max-width="70" class="mx-auto mb-2" />
        <h2 class="font-weight-bold">DOST Caraga</h2>
        <p class="text-subtitle-2 text-grey">Document Validation System</p>
      </div>

      <!-- Registration Form -->
      <v-form ref="refVForm" @submit.prevent="register">
        <v-row>
          <v-col cols="12" sm="6">
            <v-text-field
              v-model="firstname"
              label="First Name"
              outlined
              dense
              :rules="[requiredValidator]"
            />
          </v-col>
          <v-col cols="12" sm="6">
            <v-text-field
              v-model="lastname"
              label="Last Name"
              outlined
              dense
              :rules="[requiredValidator]"
            />
          </v-col>
        </v-row>

        <v-text-field
          v-model="email"
          label="Email"
          prepend-inner-icon="mdi-email"
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
          prepend-inner-icon="mdi-lock"
          :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
          @click:append-inner="showPassword = !showPassword"
          outlined
          dense
          class="mb-3"
          :rules="[requiredValidator, passwordValidator]"
        />

        <!-- Confirm Password -->
        <v-text-field
          v-model="confirmPassword"
          :type="showConfirmPassword ? 'text' : 'password'"
          label="Confirm Password"
          prepend-inner-icon="mdi-lock-check"
          :append-inner-icon="showConfirmPassword ? 'mdi-eye-off' : 'mdi-eye'"
          @click:append-inner="showConfirmPassword = !showConfirmPassword"
          outlined
          dense
          class="mb-3"
          :rules="[requiredValidator, (v) => confirmedValidator(v, password)]"
        />

        <!-- Role Selection -->
        <v-select
          v-model="selectedRole"
          :items="roles"
          label="Select Role"
          outlined
          dense
          class="mb-3"
          :rules="[requiredValidator]"
        />

        <!-- Error / Success Messages -->
        <v-alert v-if="errorMessage" type="error" border="start" class="mb-3" prominent>
          {{ errorMessage }}
        </v-alert>
        <v-alert v-if="successMessage" type="success" border="start" class="mb-3" prominent>
          {{ successMessage }}
        </v-alert>

        <!-- Register Button -->
        <v-btn :loading="loading" type="submit" color="primary" block> Register </v-btn>
      </v-form>

      <!-- Already have an account -->
      <div class="text-center mt-4">
        <p class="text-caption">
          Already have an account?
          <v-btn variant="text" size="small" color="primary" @click="router.push('/')">
            Log In
          </v-btn>
        </p>
      </div>
    </v-card>
  </v-container>
</template>

<style scoped>
.register-bg {
  background: url('/background.jpg') no-repeat center center;
  background-size: cover;
  min-height: 100vh;
}

.register-card {
  width: 100%;
  max-width: 700px; /* 👈 wider card */
}
</style>
