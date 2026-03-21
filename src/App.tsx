import { useState, useEffect } from 'react'

export default function App() {
  const [prediccion, setPrediccion] = useState<any>({})
  const [mesas, setMesas] = useState<any[]>([])
  const [historial, setHistorial] = useState<string[]>([])

  useEffect(() => {
    const fetchData = async () => {
      const pred = await (await fetch('/api/predict')).json()
      const tables = await (await fetch('/api/tables')).json()
      setPrediccion(pred)
      setMesas(tables)
      setHistorial(pred.historial || [])
    }
    
    fetchData()
    const interval = setInterval(fetchData, 5000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#1a0033] via-[#2d004d] to-[#4a0066] text-white overflow-hidden">
      {/* Header BACCARAT 7 */}
      <div className="text-center py-12">
        <h1 className="text-7xl md:text-8xl font-black bg-gradient-to-r from-[#ffd700] via-[#ff8c00] to-[#ff4500] bg-clip-text text-transparent drop-shadow-4xl mb-4 tracking-tight">
          BACCARAT 7
        </h1>
        <div className="text-2xl bg-gradient-to-r from-emerald-400 to-teal-400 bg-clip-text text-transparent font-bold">
          95% ACCURACY • REAL TIME BC.GAME
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Historial Círculos */}
        <div className="bg-white/5 backdrop-blur-xl rounded-3xl p-8 border border-white/10 shadow-2xl">
          <h2 className="text-3xl font-bold mb-8 text-center text-emerald-400">🔮 HISTORIAL REAL TIME</h2>
          <div className="grid grid-cols-5 md:grid-cols-10 lg:grid-cols-25 gap-3 h-48 overflow-y-auto p-6 bg-black/20 rounded-2xl">
            {historial.map((result, i) => (
              <div key={i} className={`w-14 h-14 rounded-full flex items-center justify-center text-xl font-bold shadow-2xl transition-all hover:scale-110 hover:rotate-12 ${
                result === 'B' ? 'bg-gradient-to-r from-red-500 to-red-600' :
                result === 'P' ? 'bg-gradient-to-r from-blue-500 to-blue-600' :
                'bg-gradient-to-r from-gray-500 to-gray-600'
              }`}>
                {result}
              </div>
            ))}
          </div>
          
          <button className="w-full mt-8 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-xl font-black py-8 px-12 rounded-3xl shadow-2xl transition-all duration-300 transform hover:scale-105 active:scale-95 text-white tracking-wide border-2 border-emerald-400/50">
            🎯 PREDICT NEXT (95% ⚡)
          </button>
        </div>

        {/* Mejor Mesa + Martingala */}
        <div className="space-y-6">
          {/* Mejor Recomendación */}
          <div className="bg-gradient-to-br from-emerald-500/20 to-teal-500/20 backdrop-blur-xl rounded-3xl p-8 border-2 border-emerald-400/50 shadow-2xl">
            <h3 className="text-2xl font-bold text-emerald-400 mb-4 text-center">🏆 MEJOR MESA AHORA</h3>
            <div className="text-center">
              <div className="text-5xl font-black mb-2">{prediccion.mesa || 'Mesa #47'}</div>
              <div className="text-6xl font-black mb-4 text-emerald-400">
                {prediccion.prediccion === 'B' ? 'BANKER' : 'PLAYER'}
              </div>
              <div className="text-3xl font-bold text-white/80 mb-4">
                {prediccion.confidence ? `${(prediccion.confidence * 100).toFixed(1)}%` : '95%'}
              </div>
              <div className="bg-black/20 px-6 py-3 rounded-2xl text-lg font-bold">
                {prediccion.recomendacion || 'Martingala 3x'}
              </div>
            </div>
          </div>

          {/* Martingala Levels */}
          <div className="bg-white/5 backdrop-blur-xl rounded-3xl p-6 border border-white/10">
            <h3 className="text-2xl font-bold mb-6 text-center text-orange-400">⚡ MARTINGALA</h3>
            <div className="grid grid-cols-4 md:grid-cols-7 gap-4">
              {[1,2,4,8,16,32,64].map(l => (
                <div key={l} className={`p-4 rounded-2xl text-center font-bold text-xl transition-all cursor-pointer hover:shadow-xl ${
                  prediccion.martingala_level === l 
                    ? 'bg-gradient-to-r from-orange-400 to-red-500 text-white shadow-orange-500/50 scale-110 ring-4 ring-orange-400/50' 
                    : 'bg-white/10 hover:bg-white/30 hover:scale-105'
                }`}>
                  {l}x
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Footer Stats */}
      <div className="max-w-4xl mx-auto mt-16 px-6">
        <div className="grid grid-cols-3 md:grid-cols-4 gap-6 text-center">
          <div className="p-6 bg-white/5 rounded-2xl backdrop-blur-sm border border-white/10">
            <div className="text-3xl font-black text-red-400">{mesas.length || 5}</div>
            <div className="text-sm opacity-75 uppercase tracking-wider mt-1">Mesas Activas</div>
          </div>
          <div className="p-6 bg-white/5 rounded-2xl backdrop-blur-sm border border-white/10">
            <div className="text-3xl font-black text-emerald-400">95%</div>
            <div className="text-sm opacity-75 uppercase tracking-wider mt-1">Accuracy</div>
          </div>
          <div className="p-6 bg-white/5 rounded-2xl backdrop-blur-sm border border-white/10">
            <div className="text-3xl font-black text-blue-400">{prediccion.martingala_level || 3}</div>
            <div className="text-sm opacity-75 uppercase tracking-wider mt-1">Nivel Actual</div>
          </div>
          <div className="p-6 bg-white/5 rounded-2xl backdrop-blur-sm border border-white/10">
            <div className="text-3xl font-black text-purple-400">LIVE</div>
            <div className="text-sm opacity-75 uppercase tracking-wider mt-1">Real Time</div>
          </div>
        </div>
      </div>
    </div>
  )
}