// vite.config.ts
// This is the configuration file for Vite (our build tool)
// We're telling Vite to use Tailwind CSS as a plugin

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [
    react(),        // enables React (JSX support)
    tailwindcss(),  // enables Tailwind CSS classes
  ],
})