'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useAuth } from '@/lib/auth'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Building2, FileText, Search, Settings, Play, LogOut, User, Menu, X } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useState } from 'react'

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: Building2 },
  { name: 'Sources', href: '/sources', icon: FileText },
  { name: 'Knowledge', href: '/knowledge', icon: Search },
  { name: 'Skills', href: '/skills', icon: Settings },
  { name: 'Runs', href: '/runs', icon: Play },
]

export function Navbar() {
  const { user, logout, loading } = useAuth()
  const pathname = usePathname()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const navigationWithActive = navigation.map((item) => ({
    ...item,
    isActive: pathname === item.href || (item.href !== '/dashboard' && pathname.startsWith(item.href)),
  }))

  if (loading) {
    return (
      <header className="border-b bg-card/50 backdrop-blur sticky top-0 z-50">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <div className="text-xl font-bold">Company Brain</div>
        </div>
      </header>
    )
  }

  if (!user) return null

  return (
    <>
      <header className="border-b bg-card/50 backdrop-blur sticky top-0 z-50">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <Link href="/dashboard" className="text-xl font-bold">
            Company Brain
          </Link>

          <nav className="hidden md:flex items-center gap-1">
            {navigationWithActive.map((item) => (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  'px-3 py-2 rounded-md text-sm font-medium transition-colors',
                  item.isActive
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:text-foreground hover:bg-accent'
                )}
              >
                <item.icon className="h-4 w-4 inline mr-2" />
                {item.name}
              </Link>
            ))}
          </nav>

          <div className="flex items-center gap-4">
            <div className="hidden md:flex items-center gap-3 text-sm">
              <div className="flex items-center gap-2">
                <User className="h-4 w-4 text-muted-foreground" />
                <span className="font-medium">{user.full_name || user.email}</span>
                <Badge variant="secondary">{user.role.replace('_', ' ')}</Badge>
              </div>
              <Badge variant="outline" className="text-xs">
                {user.org_name}
              </Badge>
            </div>

            <Button variant="ghost" size="sm" onClick={logout}>
              <LogOut className="h-4 w-4" />
            </Button>

            <button
              className="md:hidden p-2"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </button>
          </div>
        </div>
      </header>

      {/* Mobile menu */}
      {mobileMenuOpen && (
        <div className="md:hidden border-b bg-card">
          <nav className="container mx-auto px-4 py-4 space-y-2">
            {navigationWithActive.map((item) => (
              <Link
                key={item.name}
                href={item.href}
                onClick={() => setMobileMenuOpen(false)}
                className={cn(
                  'flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                  item.isActive
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:text-foreground hover:bg-accent'
                )}
              >
                <item.icon className="h-4 w-4" />
                {item.name}
              </Link>
            ))}
          </nav>
        </div>
      )}
    </>
  )
}