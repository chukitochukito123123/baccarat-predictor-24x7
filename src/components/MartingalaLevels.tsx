interface Props { 
  level: number 
}

export default function MartingalaLevels({ level }: Props) {
  const levels = [1, 2, 4, 8, 16, 32, 64]
  return (
    <div className="bg-white/10 backdrop-blur-xl rounded-3xl p-6 border border-white/20 shadow-2xl">
      <h3 className="text-2xl font-bold mb-6 text-center">🎯 Martingala</h3>
      <div className="grid grid-cols-4 md:grid-cols-7 gap-3">
        {levels.map(l => (
          <div key={l} className={`p-4 rounded-xl text-center font-bold text-lg cursor-pointer transition-all hover:shadow-xl ${
            level === l 
              ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-black shadow-xl scale-110 ring-4 ring-yellow-400/50' 
              : 'bg-white/20 hover:bg-white/40 hover:scale-105'
          }`}>
            {l}x
          </div>
        ))}
      </div>
    </div>
  )
}