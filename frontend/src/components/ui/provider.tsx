"use client"

import { ChakraProvider } from "@chakra-ui/react"
import { ColorModeProvider } from "./color-mode"
import { system } from "../../theme"

interface ProviderProps {
  children: React.ReactNode
}

export function Provider({ children }: ProviderProps) {
  return (
    <ChakraProvider value={system}>
      <ColorModeProvider />
      {children}
    </ChakraProvider>
  )
}
