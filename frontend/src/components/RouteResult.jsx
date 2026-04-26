import React from 'react';
import { Navigation, Clock, ShieldAlert, CheckCircle2, ChevronRight } from 'lucide-react';

export const RouteForm = ({ hour, setHour, typeUrgence, setTypeUrgence, onCalculate, loading }) => {
    return (
        <div className="glass-panel rounded-xl p-6 flex flex-col gap-6 shadow-2xl">
            <div>
                <label className="block text-sm font-medium text-slate-400 mb-2">Heure de l'urgence ({hour}h:00)</label>
                <input
                    type="range" min="0" max="23" value={hour}
                    onChange={(e) => setHour(parseInt(e.target.value))}
                    className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-primary"
                />
                <div className="flex justify-between text-[10px] text-slate-500 mt-1 uppercase">
                    <span>00h</span><span>06h</span><span>12h</span><span>18h</span><span>23h</span>
                </div>
            </div>

            <div>
                <label className="block text-sm font-medium text-slate-400 mb-2">Type d'urgence</label>
                <select
                    value={typeUrgence}
                    onChange={(e) => setTypeUrgence(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2.5 text-sm focus:ring-primary focus:border-primary outline-none text-white"
                >
                    <option value="general">Général / Ambulance classique</option>
                    <option value="trauma">Traumatologie / Accident</option>
                    <option value="cardio">Cardiologie / AVC</option>
                    <option value="pediatrie">Pédiatrie</option>
                </select>
            </div>

            <button
                onClick={onCalculate}
                disabled={loading}
                className="w-full bg-primary hover:bg-red-600 text-white font-bold py-3 px-4 rounded-xl shadow-lg shadow-red-500/20 transition-all flex items-center justify-center gap-2 group disabled:opacity-50"
            >
                {loading ? "Calcul en cours..." : (
                    <>
                        Calculer route d'urgence
                        <Navigation size={18} className="group-hover:translate-x-1 transition-transform" />
                    </>
                )}
            </button>
        </div>
    );
};

export const RouteResult = ({ result }) => {
    if (!result) return null;
    const stats = result.traffic_stats || {};
    const confidence = stats.confiance_globale ?? 1.0;
    const uncertainty = Math.round((1 - confidence) * 5); // up to 5 min uncertainty

    return (
        <div className="flex flex-col gap-4 mt-4 animate-in fade-in slide-in-from-top duration-300">
            {/* Freshness Indicator (Twist 02) */}
            <div className={`px-4 py-2 rounded-full border text-[10px] font-black uppercase tracking-[0.2em] flex items-center gap-2 w-fit
                ${confidence > 0.8
                    ? 'bg-green-500/10 border-green-500/30 text-green-400'
                    : confidence > 0.5
                        ? 'bg-yellow-500/10 border-yellow-500/30 text-yellow-400'
                        : 'bg-red-500/10 border-red-500/30 text-red-400 animate-pulse'}`}>
                <div className={`w-1.5 h-1.5 rounded-full ${confidence > 0.8 ? 'bg-green-400' : confidence > 0.5 ? 'bg-yellow-400' : 'bg-red-400'}`} />
                {confidence > 0.8 ? 'Données Fraîches' : confidence > 0.5 ? 'Données Dégradées' : 'Données Suspectes'}
                <span className="opacity-50">• {stats.age_moyen_secondes}s</span>
            </div>

            <div className="bg-green-500/10 border border-green-500/20 rounded-xl p-5 flex flex-col gap-2">
                <div className="flex items-center gap-2 text-green-400 font-bold">
                    <CheckCircle2 size={20} /> Meilleur itinéraire trouvé
                </div>
                <div className="text-2xl font-black">{result.hospital.name}</div>

                <div className="flex items-center gap-6 mt-4">
                    <div className="flex flex-col">
                        <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">ETA Estimé</span>
                        <span className="text-xl font-bold flex items-baseline gap-1">
                            <Clock size={16} className="text-primary mr-1" />
                            {result.eta.toFixed(0)}
                            <span className="text-xs font-medium text-slate-400">min</span>
                            {uncertainty > 0 && (
                                <span className="text-xs text-slate-500 ml-1 font-medium">± {uncertainty}m</span>
                            )}
                        </span>
                    </div>
                </div>
                {uncertainty > 0 && (
                    <div className="w-full h-1 bg-slate-800 rounded-full mt-2 overflow-hidden">
                        <div className="h-full bg-yellow-500/30" style={{ width: `${(uncertainty / 10) * 100}%` }} />
                    </div>
                )}
            </div>
        </div>
    );
};

export const AuditPanel = ({ audit }) => {
    if (!audit) return null;
    return (
        <div className="glass-panel rounded-xl p-5 mt-4 flex flex-col gap-1 border-l-4 border-l-accent">
            <h3 className="text-sm font-bold flex items-center gap-2 mb-4 text-accent uppercase tracking-widest">
                <ShieldAlert size={16} /> Rapport d'Audit & Recalculs
            </h3>

            {/* Timeline de recalculs (Twist 02) */}
            <div className="mb-6 flex flex-col gap-3 relative pl-4 border-l border-slate-700">
                <div className="text-[11px] flex gap-3 items-start">
                    <div className="absolute -left-[5px] w-2 h-2 rounded-full bg-accent" />
                    <span className="text-slate-500 font-mono">INITIAL</span>
                    <span className="text-slate-200">Calcul initial → {audit.hopital_choisi_name || "Lieu optimal"}</span>
                </div>
                {audit.recalculs && audit.recalculs.map((r, i) => (
                    <div key={i} className="text-[11px] flex gap-3 items-start">
                        <div className="absolute -left-[5px] w-2 h-2 rounded-full bg-primary" />
                        <span className="text-slate-500 font-mono">{r.at_time}</span>
                        <span className="text-slate-300">
                            {r.raison} → {r.nouvel_hopital}
                            {r.destination_changee && <span className="text-accent ml-2">⚠️ CHANGEMENT</span>}
                        </span>
                    </div>
                ))}
            </div>

            <p className="text-xs text-slate-300 italic mb-4">"{audit.raison_choix}"</p>

            <div className="text-[10px] text-slate-400 mb-3 flex items-center gap-1 uppercase tracking-wide">
                <Navigation size={10} className="text-primary" /> Départ: <span className="text-slate-200 font-bold">{audit.depart_nom || "Position inconnue"}</span>
            </div>

            <div className="mt-4 flex justify-between text-[10px] text-slate-500 border-t border-slate-800 pt-4">
                <span>Nœuds explorés: {audit.nb_noeuds_explores}</span>
                <span>Calcul: {audit.temps_calcul_ms}ms</span>
            </div>
        </div>
    );
};

