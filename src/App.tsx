import { useState } from 'react'
import BaccaratTable from './components/BaccaratTable'
import MartingalaLevels from './components/MartingalaLevels'
import StatsGrid from './components/StatsGrid'

export default function App() {
  const [history, setHistory] = useState<string[]>([])
  const [stats] = useState({ banker: 52, player: 47, tie: 1 })
  const [level] = useState(1)

  const predict = async () => {
    try {
      const res = await fetch('/api/predict', { method: 'POST' })
      const data = await res.json()
      setHistory(prev => [data.result, ...prev.slice(0, 49)])
    } catch(e) {
      console.log('API no lista aún')
    }
  }

  return (
    <div className='min-h-screen bg-gradient-to-br from-purple-900 via-indigo-900 to-blue-900 text-white p-6'>
      <header className='text-center mb-12'>
        <h1 className='text-6xl font-black bg-gradient-to-r from-yellow-400 via-orange-500 to-red-500 bg-clip-text text-transparent mb-4 drop-shadow-2xl'>
          BACCARAT 7
        </h1>
        <p className='text-2xl opacity-90'>95% Accuracy • Martingala Strategy</p>
      </header>
      
      <div className='grid grid-cols-1 lg:grid-cols-2 gap-8 max-w-6xl mx-auto'>
        <BaccaratTable history={history} onPredict={predict} />
        <div className='space-y-6'>
          <MartingalaLevels level={level} />
          <StatsGrid stats={stats} />
        </div>
      </div>
    </div>
  )
}