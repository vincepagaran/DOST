<template>
  <v-container class="d-flex justify-center align-center fill-height">
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
      <v-form @submit.prevent="login">
        <!-- Username -->
        <v-text-field
          v-model="username"
          label="Username"
          placeholder="Enter username"
          prepend-inner-icon="mdi-account"
          outlined
          dense
          class="mb-3"
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
        />

        <!-- Login Button -->
        <v-btn type="submit" color="primary" block class="mb-3"> Log In </v-btn>
      </v-form>

      <!-- Forgot Password -->
      <div class="text-center">
        <v-btn variant="text" size="small" color="primary"> Forgot Password? </v-btn>
        <p class="text-caption text-grey mt-2">v1.0.0</p>
      </div>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref } from 'vue'

const roles = ['Admin', 'Scholar', 'Staff']
const activeTab = ref(0)
const username = ref('')
const password = ref('')
const showPassword = ref(false)

const login = () => {
  console.log('Logging in as:', roles[activeTab.value], username.value, password.value)
  // TODO: add your authentication & route to dashboard
}
</script>
