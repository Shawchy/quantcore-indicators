"use client"

import { createToaster } from "@chakra-ui/react"

export const toaster = createToaster({
  placement: "bottom-end",
  max: 5,
})

export function Toaster() {
  return <Toaster />
}
