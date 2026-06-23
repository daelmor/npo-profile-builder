import { FileUp, LayoutGrid, Search as SearchIcon } from 'lucide-react'
import { NavLink, Route, Routes } from 'react-router-dom'
import BackendStatus from '@/components/BackendStatus'
import { cn } from '@/lib/utils'
import ChatPage from '@/pages/ChatPage'
import ProfileReviewPage from '@/pages/ProfileReviewPage'
import ProfilesPage from '@/pages/ProfilesPage'
import SearchPage from '@/pages/SearchPage'
import UploadPage from '@/pages/UploadPage'

const NAV = [
  { to: '/', label: 'New profile', icon: FileUp, end: true },
  { to: '/profiles', label: 'Profiles', icon: LayoutGrid, end: false },
  { to: '/search', label: 'Search', icon: SearchIcon, end: false },
]

function Brand() {
  return (
    <div className="flex items-center gap-2">
      <div className="flex size-7 items-center justify-center rounded-md bg-primary text-xs font-bold text-primary-foreground">
        NP
      </div>
      <span className="text-sm font-semibold tracking-tight">Profile Builder</span>
    </div>
  )
}

export default function App() {
  return (
    <div className="flex min-h-full">
      <aside className="hidden w-60 shrink-0 flex-col border-r bg-card md:flex">
        <div className="flex h-14 items-center border-b px-5">
          <Brand />
        </div>
        <nav className="flex-1 space-y-1 p-3">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-secondary text-secondary-foreground'
                    : 'text-muted-foreground hover:bg-secondary/60 hover:text-foreground',
                )
              }
            >
              <item.icon className="size-4" />
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t p-4">
          <BackendStatus />
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 items-center gap-5 border-b bg-card px-4 md:hidden">
          <Brand />
          <nav className="flex gap-4 text-sm">
            {NAV.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  isActive ? 'font-medium text-foreground' : 'text-muted-foreground'
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </header>

        <main className="mx-auto w-full max-w-5xl flex-1 px-6 py-8">
          <Routes>
            <Route path="/" element={<UploadPage />} />
            <Route path="/profiles" element={<ProfilesPage />} />
            <Route path="/profiles/:profileId" element={<ProfileReviewPage />} />
            <Route path="/chat/:profileId" element={<ChatPage />} />
            <Route path="/search" element={<SearchPage />} />
          </Routes>
        </main>
      </div>
    </div>
  )
}
