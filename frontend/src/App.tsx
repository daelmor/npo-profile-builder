import { NavLink, Route, Routes } from 'react-router-dom'
import UploadPage from './pages/UploadPage'
import ProfileReviewPage from './pages/ProfileReviewPage'
import ChatPage from './pages/ChatPage'
import SearchPage from './pages/SearchPage'

const NAV = [
  { to: '/', label: 'Upload', end: true },
  { to: '/search', label: 'Search', end: false },
]

export default function App() {
  return (
    <div className="flex min-h-full flex-col">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-5xl items-center gap-8 px-6 py-4">
          <span className="font-semibold tracking-tight text-slate-900">
            Nonprofit Profile Builder
          </span>
          <nav className="flex gap-5 text-sm">
            {NAV.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  isActive
                    ? 'font-medium text-slate-900'
                    : 'text-slate-500 hover:text-slate-900'
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>

      <main className="mx-auto w-full max-w-5xl flex-1 px-6 py-8">
        <Routes>
          <Route path="/" element={<UploadPage />} />
          <Route path="/profiles/:profileId" element={<ProfileReviewPage />} />
          <Route path="/chat/:profileId" element={<ChatPage />} />
          <Route path="/search" element={<SearchPage />} />
        </Routes>
      </main>
    </div>
  )
}
