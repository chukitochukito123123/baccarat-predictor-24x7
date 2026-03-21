interface Props {
  stats: { banker: number, player: number, tie: number }
}

export default function StatsGrid({ stats }: Props) {
  const total = stats.banker + stats.player + stats.tie
  const accuracy = total > 0 ? Math.round((stats.banker + stats.player) / total * 100) : 0

  return (
    <div className="bg-white/10 backdrop-blur-xl rounded-3xl p-6 border border-white/20 shadow-2xl">
      <h3 className="text-2xl font-bold mb-6 text-center">📊 Estadísticas</h3>
      <div className="grid grid-cols-3 gap-6 text-center mb-8">
        <div>
          <div className="text-4xl font-black text-red-400 mb-1 drop-shadow-lg">{stats.banker}</div>
          <div className="text-sm opacity-75 uppercase tracking-wider">Banker</div>
        </div>
        <div>
          <div className="text-4xl font-black text-blue-400 mb-1 drop-shadow-lg">{stats.player}</div>
          <div className="text-sm opacity-75 uppercase tracking-wider">Player</div>
        </div>
        <div>
          <div className="text-4xl font-black text-gray-400 mb-1 drop-shadow-lg">{stats.tie}</div>
          <div className="text-sm opacity-75 uppercase tracking-wider">Tie</div>
        </div>
      </div>
      <div className="p-6 bg-gradient-to-r from-emerald-500/20 to-teal-500/20 rounded-2xl border-2 border-emerald-500/50 backdrop-blur-sm">
        <div className="text-4xl font-black text-emerald-400 drop-shadow-lg">{accuracy}%</div>
        <div className="text-lg opacity-90 mt-2">Precisión Total</div>
      </div>
    </div>
  )
}