"use client"

import { extendTheme } from "@chakra-ui/react"

export const theme = extendTheme({
  colors: {
    brand: {
      50: "#f8f5f2",   // Background cream
      100: "#f0e9e2",  // Light variant
      200: "#e2d9d0",  // Border color
      300: "#d8c5b4",  // Lighter accent
      400: "#c97d60",  // Main accent
      500: "#c97d60",  // Main accent (same as 400)
      600: "#b86b4d",  // Darker accent
      700: "#a85a3a",  // Even darker
      800: "#8a4a2f",  // Dark variant
      900: "#2d2a27",  // Main text color
    },
    gray: {
      50: "#f8f5f2",
      100: "#f0e9e2", 
      200: "#e2d9d0",
      300: "#d0c4b8",
      400: "#a89888",
      500: "#8a8580",
      600: "#5c5853",
      700: "#4a453f",
      800: "#2d2a27",
      900: "#1a1816",
    }
  },
  fonts: {
    heading: "ui-serif, Georgia, serif", // Match the font-serif from landing page
    body: "ui-sans-serif, system-ui, sans-serif",
  },
  styles: {
    global: {
      body: {
        bg: "#f8f5f2",
        color: "#2d2a27",
      },
    },
  },
  components: {
    Button: {
      baseStyle: {
        borderRadius: "full", // Rounded buttons like landing page
        fontWeight: "medium",
      },
      variants: {
        solid: {
          bg: "#2d2a27",
          color: "#f8f5f2",
          _hover: {
            bg: "#5c5853",
          },
        },
        outline: {
          borderColor: "#c97d60",
          color: "#2d2a27",
          _hover: {
            bg: "#f0e9e2",
          },
        },
      },
    },
    Card: {
      baseStyle: {
        container: {
          bg: "white",
          borderRadius: "2xl", // Rounded corners like landing page
          border: "1px solid",
          borderColor: "#e2d9d0",
          boxShadow: "sm",
        },
      },
    },
  },
  config: {
    initialColorMode: "light",
    useSystemColorMode: false,
  },
})