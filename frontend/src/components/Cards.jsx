import { Award, CheckCircle2, Flame, Star } from 'lucide-react';
export function Kpi({ icon: Icon = Star, label, value }) { return <div className="card kpi"><div className="kpi-icon"><Icon size={22}/></div><div><strong>{value}</strong><span className="muted">{label}</span></div></div>; }
export const kpiIcons = { Award, CheckCircle2, Flame, Star };
export function ProgressBar({ value = 0 }) { return <div className="progress" title={`${value}%`}><span style={{width:`${Math.min(100, Math.max(0, value))}%`}} /></div>; }
