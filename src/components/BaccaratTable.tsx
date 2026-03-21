interface Props {
  history: string[]
  onPredict: () => void
}

export default function BaccaratTable({ history, onPredict }: Props) {
  return (
    <div className="bg-white/10 backdrop-blur-xl rounded-3xl p-8 border border-white/20 shadow-2xl">
      <h2 className="text-3xl font-bold mb-8 text-center">🔮 Historial (50 últimos)</h2>
      <div className="grid grid-cols-10 md:grid-cols-25 gap-3 mb-8 h-40 md:h-48 overflow-hidden p-4 bg-black/30 rounded-2xl">
        {history.map((result, i) => (
          <div
            key={i}
            className={`w-10 h-10 md:w-12 md:h-12 rounded-full flex items-center justify-center text-lg font-bold shadow-lg transition-all hover:scale-110 ${
              result === 'B' ? 'bg-red-500 hover:bg-red-400' : 
              result === 'P' ? 'bg-blue-500 hover:bg-blue-400' : 'bg-gray-500'
            }`}
          >
            {result}
          </div>
        ))}
      </div>
      <button
        onClick={onPredict}
        className="w-full bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-xl font-bold py-6 px-8 rounded-2xl shadow-2xl transition-all duration-300 transform hover:scale-[1.02] active:scale-100"
      >
        🎯 PREDICT NEXT (95% ⚡)
      </button>
    </div>
  )
}