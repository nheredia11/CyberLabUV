import {
  Bell,
  LogOut,
  GraduationCap,
} from 'lucide-react';

function getInitials(name = '') {
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join('')
    .toUpperCase() || 'CL';
}

export default function Topbar({ title, subtitle, user, onLogout }) {
  const avatar = user?.avatar || getInitials(user?.name);

  return (
    <header className="topbar topbar-modern clean">
      <div className="topbar-center-info clean">
        <h1>{title}</h1>
        <p>{subtitle}</p>
      </div>

      <div className="topbar-actions">
        <button className="topbar-icon-btn" title="Notificaciones">
          <Bell size={19} />
        </button>

        <div className="topbar-user-card">
          {user?.picture ? (
            <img src={user.picture} alt={user.name} />
          ) : (
            <span className="topbar-avatar-fallback">{avatar}</span>
          )}

          <div>
            <strong>{user?.name}</strong>
            <small>
              <GraduationCap size={13} />
              {user?.role === 'teacher' ? 'Docente' : 'Estudiante'}
            </small>
          </div>
        </div>

        <button
          className="topbar-logout-btn"
          onClick={onLogout}
          title="Cerrar sesión"
        >
          <LogOut size={20} />
        </button>
      </div>
    </header>
  );
}