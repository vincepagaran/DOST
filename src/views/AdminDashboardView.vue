<template>
  <v-container>
    <v-row class="align-center justify-space-between mb-6">
      <h1 class="text-h4">Admin Dashboard</h1>

      <!-- Profile Avatar + Logout -->
      <v-menu>
        <template #activator="{ props }">
          <v-avatar v-bind="props" size="40" color="grey-lighten-2" class="cursor-pointer">
            <v-icon color="grey-darken-3">mdi-account-circle</v-icon>
          </v-avatar>
        </template>
        <v-list>
          <v-list-item>
            <v-list-item-title class="font-weight-bold">
              {{ profileEmail }}
            </v-list-item-title>
          </v-list-item>
          <v-divider></v-divider>
          <v-list-item @click="logout">
            <v-icon start color="red">mdi-logout</v-icon>
            Logout
          </v-list-item>
        </v-list>
      </v-menu>
    </v-row>

    <v-card class="pa-4 rounded-xl shadow-lg">
      <v-card-title>User Management</v-card-title>

      <!-- Custom Header Labels -->
      <v-row class="px-4 py-2 font-weight-bold text-subtitle-2 grey--text">
        <v-col cols="5">Email</v-col>
        <v-col cols="3">Role</v-col>
        <v-col cols="2">Actions</v-col>
      </v-row>
      <v-divider></v-divider>

      <!-- User List -->
      <v-row v-for="user in accounts" :key="user.id" class="px-4 py-2 align-center">
        <v-col cols="5">{{ user.email }}</v-col>
        <v-col cols="3">
          <v-chip
            :color="user.role === 'Scholar' ? 'blue' : 'green'"
            text-color="white"
            size="small"
          >
            {{ user.role }}
          </v-chip>
        </v-col>
        <v-col cols="2">
          <v-btn variant="text" color="red" @click="deleteUser(user)">Delete</v-btn>
        </v-col>
      </v-row>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { supabase } from '@/utils/supabase'
import { useRouter } from 'vue-router'

const router = useRouter()
const accounts = ref([])
const profileEmail = ref('')

// Fetch users + current profile
const fetchUsers = async () => {
  const {
    data: { session },
  } = await supabase.auth.getSession()
  if (!session) return

  profileEmail.value = session.user.email

  const { data: currentUser } = await supabase
    .from('users')
    .select('role')
    .eq('id', session.user.id)
    .single()

  if (currentUser?.role === 'Admin') {
    const { data, error } = await supabase.from('users').select('id, email, role')
    if (error) console.error(error)
    else accounts.value = data
  }
}

// Delete user
const deleteUser = async (user) => {
  if (confirm(`Are you sure you want to delete ${user.email}?`)) {
    const { error } = await supabase.from('users').delete().eq('id', user.id)
    if (error) {
      alert('Failed to delete user: ' + error.message)
    } else {
      accounts.value = accounts.value.filter((u) => u.id !== user.id)
      alert(`${user.email} deleted successfully.`)
    }
  }
}

// Logout
const logout = async () => {
  await supabase.auth.signOut()
  router.push('/')
}

onMounted(fetchUsers)
</script>
