<template>
  <v-container class="d-flex justify-center align-center" style="height: 100vh">
    <v-card elevation="10" width="500" class="pa-6 rounded-xl">
      <v-card-title class="text-center text-h5 font-weight-bold"> Register </v-card-title>

      <v-form ref="refVForm" @submit.prevent="onFormSubmit">
        <!-- Firstname -->
        <v-text-field
          v-model="formData.firstname"
          label="First Name"
          prepend-inner-icon="mdi-account"
          :rules="[requiredValidator]"
          outlined
          dense
        />

        <!-- Lastname -->
        <v-text-field
          v-model="formData.lastname"
          label="Last Name"
          prepend-inner-icon="mdi-account"
          :rules="[requiredValidator]"
          outlined
          dense
        />

        <!-- Email -->
        <v-text-field
          v-model="formData.email"
          label="Email"
          prepend-inner-icon="mdi-email"
          :rules="[requiredValidator, emailValidator]"
          outlined
          dense
        />

        <!-- Password -->
        <v-text-field
          v-model="formData.password"
          label="Password"
          prepend-inner-icon="mdi-lock"
          :append-inner-icon="visible ? 'mdi-eye-off' : 'mdi-eye'"
          :type="visible ? 'text' : 'password'"
          @click:append-inner="visible = !visible"
          :rules="[requiredValidator, passwordValidator]"
          outlined
          dense
        />

        <!-- Confirm Password -->
        <v-text-field
          v-model="formData.password_confirmation"
          label="Confirm Password"
          prepend-inner-icon="mdi-lock-check"
          :append-inner-icon="visibleConfirm ? 'mdi-eye-off' : 'mdi-eye'"
          :type="visibleConfirm ? 'text' : 'password'"
          @click:append-inner="visibleConfirm = !visibleConfirm"
          :rules="[requiredValidator, (val) => confirmedValidator(val, formData.password)]"
          outlined
          dense
        />

        <!-- Error / Success Messages -->
        <v-alert
          v-if="formAction.formErrorMessage"
          type="error"
          class="mt-3"
          border="start"
          prominent
        >
          {{ formAction.formErrorMessage }}
        </v-alert>

        <v-alert
          v-if="formAction.formSuccessMessage"
          type="success"
          class="mt-3"
          border="start"
          prominent
        >
          {{ formAction.formSuccessMessage }}
        </v-alert>

        <!-- Submit Button -->
        <v-btn :loading="formAction.formProcess" color="primary" class="mt-4" block type="submit">
          Register
        </v-btn>
      </v-form>

      <!-- Already have an account? -->
      <div class="text-center mt-4">
        <p class="text-caption">
          Already have an account?
          <v-btn variant="text" size="small" color="primary" @click="goToLogin"> Log In </v-btn>
        </p>
      </div>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref } from 'vue'
import {
  requiredValidator,
  emailValidator,
  passwordValidator,
  confirmedValidator,
} from '@/utils/validators'
import { supabase, formActionDefault } from '@/utils/supabase'
import { useRouter } from 'vue-router'

const router = useRouter()
const visible = ref(false)
const visibleConfirm = ref(false)
const refVForm = ref()

const formDataDefault = {
  firstname: '',
  lastname: '',
  email: '',
  password: '',
  password_confirmation: '',
}

const formData = ref({ ...formDataDefault })
const formAction = ref({ ...formActionDefault })

const onSubmit = async () => {
  formAction.value = { ...formActionDefault }
  formAction.value.formProcess = true

  const { data, error } = await supabase.auth.signUp({
    email: formData.value.email,
    password: formData.value.password,
    options: {
      data: {
        firstname: formData.value.firstname,
        lastname: formData.value.lastname,
      },
    },
  })

  if (error) {
    console.log(error)
    formAction.value.formErrorMessage = error.message
    formAction.value.formProcess = false
  } else if (data) {
    console.log(data)
    formAction.value.formSuccessMessage = 'Successfully Registered.'
    router.replace('/')
  }

  refVForm.value?.reset()
  formAction.value.formProcess = false
}

const onFormSubmit = () => {
  refVForm.value?.validate().then(({ valid }) => {
    if (valid) onSubmit()
  })
}

const goToLogin = () => {
  router.push('/')
}
</script>
