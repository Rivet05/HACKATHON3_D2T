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
    return (
        <div className="bg-green-500/10 border border-green-500/20 rounded-xl p-5 mt-4 flex flex-col gap-2 animate-in fade-in slide-in-from-top duration-300">
            <div className="flex items-center gap-2 text-green-400 font-bold">
                <CheckCircle2 size={20} /> Meilleur itinéraire trouvé
            </div>
            <div className="text-2xl font-black">{result.hopital.name}</div>
            <div className="flex items-center gap-6 mt-2">
                <div className="flex flex-col">
                    <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">ETA Estimé</span>
                    <span className="text-xl font-bold flex items-center gap-1">
                        <Clock size={16} className="text-primary" /> {result.eta_minutes.toFixed(0)} min
                    </span>
                </div>
                <div className="flex flex-col">
                    <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Distance relative</span>
                    <span className="text-xl font-bold flex items-center gap-1">
                        {result.total_cost.toFixed(1)} <span className="text-xs text-slate-500">pts</span>
                    </span>
                </div>
            </div>
        </div>
    );
};

export const AuditPanel = ({ audit }) => {
    if (!audit) return null;
    return (
        <div className="glass-panel rounded-xl p-5 mt-4 flex flex-col gap-1 border-l-4 border-l-accent">
            <h3 className="text-sm font-bold flex items-center gap-2 mb-2 text-accent uppercase tracking-widest">
                <ShieldAlert size={16} /> Rapport d'Audit
            </h3>
            <p className="text-xs text-slate-300 italic mb-1">"{audit.raison_choix}"</p>
            <div className="text-[10px] text-slate-400 mb-3 flex items-center gap-1 uppercase tracking-wide">
                <Navigation size={10} className="text-primary" /> Départ: <span className="text-slate-200 font-bold">{audit.depart_nom || "Position inconnue"}</span>
            </div>

            <div className="flex flex-col gap-2">
                {audit.hopitaux_consideres.map((h, i) => (
                    <div key={i} className="flex items-center justify-between text-[11px] border-b border-slate-700/50 pb-1">
                        <span className={h.eligible ? "text-slate-200" : "text-slate-500"}>{h.name}</span>
                        <span className={h.eligible ? "text-green-500" : "text-red-500/70"}>
                            {h.eligible ? "Eligible" : h.reason}
                        </span>
                    </div>
                ))}
            </div>

            <div className="mt-4 flex justify-between text-[10px] text-slate-500">
                <span>Nœuds explorés: {audit.nb_noeuds_explores}</span>
                <span>Calcul: {audit.temps_calcul_ms}ms</span>
            </div>
        </div>
    );
};
