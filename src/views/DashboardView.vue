<template>
  <v-app>
    <v-main>
      <v-container class="pa-4">
        <!-- Header -->
        <div class="d-flex justify-space-between align-center mb-4">
          <h2 class="font-weight-bold">Dashboard</h2>
          <v-btn icon @click="profileDialog = true">
            <v-icon>mdi-account-circle</v-icon>
          </v-btn>
        </div>

        <!-- Stats Cards -->
        <v-row dense>
          <v-col cols="6">
            <v-card class="pa-4 text-center">
              <v-icon size="32" color="primary">mdi-file-document</v-icon>
              <h3 class="font-weight-bold">{{ totalDocs }}</h3>
              <p class="text-subtitle-2">Total Documents</p>
            </v-card>
          </v-col>
          <v-col cols="6">
            <v-card class="pa-4 text-center">
              <v-icon size="32" color="success">mdi-check-circle</v-icon>
              <h3 class="font-weight-bold">{{ verifiedDocs }}</h3>
              <p class="text-subtitle-2">Verified</p>
            </v-card>
          </v-col>
        </v-row>

        <!-- Buttons -->
        <v-row class="my-4" dense>
          <v-col cols="6">
            <v-btn color="primary" block @click="$router.push('/upload')">
              <v-icon left>mdi-upload</v-icon>
              Upload Document
            </v-btn>
          </v-col>
          <v-col cols="6">
            <v-btn color="grey-lighten-2" block @click="$router.push('/history')">
              <v-icon left>mdi-history</v-icon>
              View History
            </v-btn>
          </v-col>
        </v-row>

        <!-- Recent Activity -->
        <h3 class="mb-2">Recent Activity</h3>
        <v-list>
          <v-list-item v-for="(item, i) in activities" :key="i" class="rounded-lg mb-2">
            <v-avatar class="mr-3" size="36">
              <v-icon>mdi-file-pdf-box</v-icon>
            </v-avatar>

            <v-list-item-title>{{ item.name }}</v-list-item-title>
            <v-list-item-subtitle>
              <v-icon size="16" :color="statusColor(item.status)" class="mr-1"> mdi-circle </v-icon>
              {{ item.status }} • {{ formatTime(item.created_at) }}
            </v-list-item-subtitle>
          </v-list-item>

          <v-list-item v-if="activities.length === 0">
            <v-list-item-title class="text-grey">No recent activity</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-container>

      <!-- Bottom Navigation -->
      <v-bottom-navigation v-model="nav" color="primary" grow>
        <v-btn value="home">
          <v-icon>mdi-home</v-icon>
          Home
        </v-btn>
        <v-btn value="upload">
          <v-icon>mdi-upload</v-icon>
          Upload
        </v-btn>
        <v-btn value="history">
          <v-icon>mdi-history</v-icon>
          History
        </v-btn>
        <v-btn value="settings">
          <v-icon>mdi-cog</v-icon>
          Settings
        </v-btn>
      </v-bottom-navigation>

      <!-- Profile Dialog -->
      <v-dialog v-model="profileDialog" max-width="400">
        <v-card class="pa-4 rounded-xl">
          <v-card-title class="text-h6 font-weight-bold">
            <v-icon left class="mr-2">mdi-account</v-icon>
            Profile
          </v-card-title>
          <v-divider></v-divider>
          <v-card-text>
            <p><strong>First Name:</strong> {{ user.firstname }}</p>
            <p><strong>Last Name:</strong> {{ user.lastname }}</p>
            <p><strong>Email:</strong> {{ user.email }}</p>
          </v-card-text>
          <v-card-actions>
            <v-btn color="error" @click="logout" block>Logout</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
    </v-main>
  </v-app>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { supabase } from '@/utils/supabase'
import { useRouter } from 'vue-router'

const router = useRouter()

// Stats
const totalDocs = ref(0)
const verifiedDocs = ref(0)
const activities = ref([])

const nav = ref('home')
const profileDialog = ref(false)
const user = ref({ firstname: '', lastname: '', email: '' })

// Fetch logged-in user + documents
onMounted(async () => {
  const { data: authData, error } = await supabase.auth.getUser()
  if (error || !authData?.user) {
    router.push('/') // redirect to login
  } else {
    const metadata = authData.user.user_metadata
    user.value = {
      firstname: metadata.firstname,
      lastname: metadata.lastname,
      email: authData.user.email,
    }

    // Fetch documents for this user
    const { data: docs, error: docsError } = await supabase
      .from('documents')
      .select('*')
      .eq('user_id', authData.user.id)
      .order('created_at', { ascending: false })

    if (!docsError && docs) {
      totalDocs.value = docs.length
      verifiedDocs.value = docs.filter((d) => d.status === 'Verified').length
      activities.value = docs.slice(0, 5) // show last 5
    }
  }
})

const statusColor = (status) => {
  switch (status) {
    case 'Verified':
      return 'success'
    case 'Pending':
      return 'warning'
    case 'Rejected':
      return 'error'
    default:
      return 'grey'
  }
}

const formatTime = (date) => {
  return new Date(date).toLocaleString()
}

const logout = async () => {
  await supabase.auth.signOut()
  router.push('/')
}
</script>
