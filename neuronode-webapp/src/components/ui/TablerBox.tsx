'use client'

import { Box, BoxProps } from '@mui/material'
import { ReactNode } from 'react'

export interface TablerBoxProps extends Omit<BoxProps, 'sx'> {
  variant?: 'flex-center' | 'flex-between' | 'flex-start' | 'flex-end' | 'section' | 'hero' | 'container'
  spacing?: 'none' | 'small' | 'medium' | 'large'
  children: ReactNode
}

const boxVariants = {
  'flex-center': {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center'
  },
  'flex-between': {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center'
  },
  'flex-start': {
    display: 'flex',
    alignItems: 'center'
  },
  'flex-end': {
    display: 'flex',
    justifyContent: 'flex-end',
    alignItems: 'center'
  },
  'section': {
    component: 'section'
  },
  'hero': {
    component: 'section',
    textAlign: 'center'
  },
  'container': {
    maxWidth: 'lg'
  }
}

const spacingVariants = {
  none: {},
  small: { gap: 1 },
  medium: { gap: 2 },
  large: { gap: 3 }
}

export default function TablerBox({ 
  variant = 'flex-start', 
  spacing = 'none',
  children, 
  ...props 
}: TablerBoxProps) {
  const variantProps = boxVariants[variant]
  const spacingProps = spacingVariants[spacing]
  
  const boxProps = {
    ...variantProps,
    ...spacingProps,
    ...props
  }

  return (
    <Box {...boxProps}>
      {children}
    </Box>
  )
} 