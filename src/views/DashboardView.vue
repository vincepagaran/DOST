<template>
  <v-app>
    <v-main>
      <v-container class="pa-4">
        <!-- Header -->
        <div class="d-flex justify-space-between align-center mb-4">
          <h2 class="font-weight-bold">Dashboard</h2>
          <v-btn icon>
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
              <v-icon size="16" :color="item.statusColor" class="mr-1"> mdi-circle </v-icon>
              {{ item.status }} • {{ item.time }}
            </v-list-item-subtitle>
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
    </v-main>
  </v-app>
</template>

<script setup>
import { ref } from 'vue'

const totalDocs = ref(156)
const verifiedDocs = ref(124)

const activities = ref([
  { name: 'Passport Scan.pdf', status: 'Verified', statusColor: 'success', time: '2h ago' },
  { name: 'ID Card.pdf', status: 'Pending', statusColor: 'warning', time: '3h ago' },
  { name: 'Driver License.pdf', status: 'Rejected', statusColor: 'error', time: '5h ago' },
])

const nav = ref('home')
</script>
