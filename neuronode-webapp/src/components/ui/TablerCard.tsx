'use client'

import { Card, CardContent, CardProps } from '@mui/material'
import { ReactNode } from 'react'

export interface TablerCardProps extends Omit<CardProps, 'sx'> {
  variant?: 'default' | 'feature' | 'info' | 'status' | 'metric'
  children: ReactNode
  clickable?: boolean
  hover?: boolean
}

const cardVariants = {
  default: {
    elevation: 2,
  },
  feature: {
    elevation: 2,
    sx: { 
      height: '100%',
      cursor: 'pointer',
      transition: 'all 0.3s ease-in-out',
      '&:hover': {
        elevation: 8,
        transform: 'translateY(-4px)',
      }
    }
  },
  info: {
    elevation: 2,
    sx: {
      p: 4,
      textAlign: 'center',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      color: 'white'
    }
  },
  status: {
    elevation: 1,
    sx: {
      mb: 4
    }
  },
  metric: {
    elevation: 1,
    sx: {
      height: '100%'
    }
  }
}

export default function TablerCard({ 
  variant = 'default', 
  children, 
  clickable = false,
  hover = false,
  ...props 
}: TablerCardProps) {
  const variantProps = cardVariants[variant]
  
  const cardProps = {
    ...variantProps,
    ...props,
    sx: {
      ...variantProps.sx,
      ...(clickable && { cursor: 'pointer' }),
      ...(hover && { 
        transition: 'all 0.3s ease-in-out',
        '&:hover': {
          elevation: 8,
          transform: 'translateY(-2px)',
        }
      })
    }
  }

  return (
    <Card {...cardProps}>
      {children}
    </Card>
  )
}

export interface TablerCardContentProps {
  variant?: 'default' | 'feature' | 'centered' | 'compact'
  children: ReactNode
}

const contentVariants = {
  default: {},
  feature: {
    sx: { textAlign: 'center', p: 3 }
  },
  centered: {
    sx: { textAlign: 'center' }
  },
  compact: {
    sx: { p: 2 }
  }
}

export function TablerCardContent({ 
  variant = 'default', 
  children 
}: TablerCardContentProps) {
  const variantProps = contentVariants[variant]
  
  return (
    <CardContent {...variantProps}>
      {children}
    </CardContent>
  )
} 