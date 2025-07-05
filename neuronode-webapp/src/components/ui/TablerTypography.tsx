'use client'

import { Typography, TypographyProps } from '@mui/material'
import { ReactNode } from 'react'

export interface TablerTypographyProps extends Omit<TypographyProps, 'sx'> {
  variant?: 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6' | 'body1' | 'body2' | 'caption' | 'subtitle1' | 'subtitle2'
  textVariant?: 'default' | 'hero' | 'gradient' | 'section-title' | 'description' | 'muted'
  children: ReactNode
}

const textVariants = {
  default: {},
  hero: {
    fontWeight: 300,
    sx: { 
      background: 'linear-gradient(45deg, #1976d2 30%, #42a5f5 90%)',
      backgroundClip: 'text',
      WebkitBackgroundClip: 'text',
      WebkitTextFillColor: 'transparent',
      mb: 2
    }
  },
  gradient: {
    sx: {
      background: 'linear-gradient(45deg, #1976d2 30%, #42a5f5 90%)',
      backgroundClip: 'text',
      WebkitBackgroundClip: 'text',
      WebkitTextFillColor: 'transparent'
    }
  },
  'section-title': {
    textAlign: 'center',
    gutterBottom: true,
    sx: { mb: 4 }
  },
  description: {
    color: 'text.secondary',
    sx: { maxWidth: 600, mx: 'auto', mb: 4, fontWeight: 300 }
  },
  muted: {
    color: 'text.secondary'
  }
}

export default function TablerTypography({ 
  variant = 'body1',
  textVariant = 'default',
  children, 
  ...props 
}: TablerTypographyProps) {
  const textVariantProps = textVariants[textVariant]
  
  const typographyProps = {
    variant,
    ...textVariantProps,
    ...props
  }

  return (
    <Typography {...typographyProps}>
      {children}
    </Typography>
  )
} 