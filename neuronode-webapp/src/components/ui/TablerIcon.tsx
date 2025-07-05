'use client'

import { SvgIconProps } from '@mui/material'
import { ReactElement, cloneElement } from 'react'

export interface TablerIconProps {
  icon: ReactElement
  size?: 'small' | 'medium' | 'large' | 'xlarge'
  color?: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info' | 'inherit' | 'muted'
  variant?: 'default' | 'contained' | 'outlined'
}

const iconSizes = {
  small: 16,
  medium: 24,
  large: 32,
  xlarge: 48
}

const iconColors = {
  primary: 'primary.main',
  secondary: 'secondary.main',
  success: 'success.main',
  warning: 'warning.main',
  error: 'error.main',
  info: 'info.main',
  inherit: 'inherit',
  muted: 'text.secondary'
}

const iconVariants = {
  default: {},
  contained: {
    sx: {
      p: 1,
      borderRadius: 1,
      backgroundColor: 'rgba(25, 118, 210, 0.08)'
    }
  },
  outlined: {
    sx: {
      p: 1,
      borderRadius: 1,
      border: '1px solid',
      borderColor: 'divider'
    }
  }
}

export default function TablerIcon({ 
  icon, 
  size = 'medium', 
  color = 'inherit',
  variant = 'default'
}: TablerIconProps) {
  const iconSize = iconSizes[size]
  const iconColor = iconColors[color]
  const variantProps = iconVariants[variant]

  const iconProps: SvgIconProps = {
    sx: {
      fontSize: iconSize,
      color: iconColor,
      ...variantProps.sx
    }
  }

  return cloneElement(icon, iconProps)
}

// Vordefinierte Icon-Größen für häufige Anwendungsfälle
export const TablerIconSizes = {
  BUTTON: 'small' as const,
  CARD: 'large' as const,
  HERO: 'xlarge' as const,
  LIST: 'medium' as const,
  AVATAR: 'medium' as const
} 