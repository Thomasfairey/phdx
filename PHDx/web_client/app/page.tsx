'use client'

import { useState, useEffect } from 'react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://phdx-production.up.railway.app'

export default function Home() {
  const [status, setStatus] = useState<'loading' | 'connected' | 'error'>('loading')

  useEffect(() => {
    const checkBackend = async () => {
      try {
        const response = await fetch(`${API_URL}/health`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        })
        if (response.ok) {
          setStatus('connected')
        } else {
          setStatus('error')
        }
      } catch {
        setStatus('error')
      }
    }
    checkBackend()
  }, [])

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <div className="max-w-4xl w-full text-center">
        <h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
          PHDx
        </h1>
        <p className="text-xl text-gray-600 dark:text-gray-300 mb-8">
          PhD Thesis Command Center
        </p>

        <div className="bg-white dark:bg-slate-800 rounded-xl shadow-lg p-8 mb-8">
          <h2 className="text-2xl font-semibold mb-4">Your Intelligent Research Companion</h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Streamline your PhD journey with AI-powered thesis writing, literature management,
            and research organization tools.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
            <div className="p-4 bg-blue-50 dark:bg-slate-700 rounded-lg">
              <h3 className="font-semibold text-blue-700 dark:text-blue-300">Thesis Writing</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
                AI-assisted writing and editing for your thesis chapters
              </p>
            </div>
            <div className="p-4 bg-purple-50 dark:bg-slate-700 rounded-lg">
              <h3 className="font-semibold text-purple-700 dark:text-purple-300">Literature Review</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
                Organize and analyze your research papers with Zotero integration
              </p>
            </div>
            <div className="p-4 bg-green-50 dark:bg-slate-700 rounded-lg">
              <h3 className="font-semibold text-green-700 dark:text-green-300">Knowledge Base</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
                Vector-powered search across all your research materials
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-center gap-2 text-sm">
          <span className={`w-3 h-3 rounded-full ${
            status === 'connected' ? 'bg-green-500' :
            status === 'error' ? 'bg-red-500' : 'bg-yellow-500 animate-pulse'
          }`}></span>
          <span className="text-gray-600 dark:text-gray-400">
            Backend: {status === 'loading' ? 'Connecting...' :
                     status === 'connected' ? 'Connected' : 'Unavailable'}
          </span>
        </div>
      </div>
    </main>
  )
}
