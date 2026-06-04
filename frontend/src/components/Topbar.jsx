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
  const initials = user?.avatar || getInitials(user?.name);

  return (
    <header className="pro-topbar">
      <div className="pro-topbar-title">
        <h1>{title}</h1>
        <p>{subtitle}</p>
      </div>

      <div className="pro-topbar-actions">
        <button className="pro-icon-button" title="Notificaciones">
          <Bell size={19} />
        </button>

        <div className="pro-user-pill">
          <div className="pro-user-avatar">
            {initials}
          </div>

          <div className="pro-user-info">
            <strong>{user?.name || 'Usuario CyberLab'}</strong>
            <span>
              <GraduationCap size={13} />
              {user?.role === 'teacher' ? 'Docente' : 'Estudiante'}
            </span>
          </div>
        </div>

        <button
          className="pro-logout-button"
          onClick={onLogout}
          title="Cerrar sesión"
        >
          <LogOut size={20} />
        </button>
      </div>
    </header>
  );
}