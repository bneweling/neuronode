'use client'

import { Container, ContainerProps } from '@mui/material'
import { ReactNode } from 'react'

export interface TablerContainerProps extends Omit<ContainerProps, 'sx'> {
  variant?: 'default' | 'page' | 'section' | 'narrow' | 'wide'
  spacing?: 'none' | 'small' | 'medium' | 'large'
  children: ReactNode
}

const containerVariants = {
  default: {
    maxWidth: 'lg'
  },
  page: {
    maxWidth: 'lg',
    sx: { py: 4 }
  },
  section: {
    maxWidth: 'lg',
    sx: { py: 6 }
  },
  narrow: {
    maxWidth: 'md'
  },
  wide: {
    maxWidth: 'xl'
  }
}

const spacingVariants = {
  none: {},
  small: { sx: { py: 2 } },
  medium: { sx: { py: 4 } },
  large: { sx: { py: 6 } }
}

export default function TablerContainer({ 
  variant = 'default',
  spacing,
  children, 
  ...props 
}: TablerContainerProps) {
  const variantProps = containerVariants[variant]
  const spacingProps = spacing ? spacingVariants[spacing] : {}
  
  const containerProps = {
    ...variantProps,
    ...spacingProps,
    ...props,
    sx: {
      ...variantProps.sx,
      ...spacingProps.sx,
      ...props.sx
    }
  }

  return (
    <Container {...containerProps}>
      {children}
    </Container>
  )
} 