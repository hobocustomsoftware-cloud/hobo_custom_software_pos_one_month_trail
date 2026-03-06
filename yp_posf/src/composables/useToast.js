/**
 * Simple toast notifications — no extra dependency.
 * Usage: const toast = useToast(); toast.error('Message'); toast.success('Done');
 */
const toasts = []
let container = null

function getContainer() {
  if (typeof document === 'undefined') return null
  if (!container) {
    container = document.createElement('div')
    container.id = 'toast-container'
    container.setAttribute('aria-live', 'polite')
    Object.assign(container.style, {
      position: 'fixed',
      bottom: '80px',
      left: '50%',
      transform: 'translateX(-50%)',
      zIndex: 99999,
      display: 'flex',
      flexDirection: 'column',
      gap: '8px',
      pointerEvents: 'none',
      maxWidth: 'min(90vw, 360px)',
    })
    document.body.appendChild(container)
  }
  return container
}

/** Call on app mount so toast container exists and toasts always show. */
export function initToastContainer() {
  getContainer()
}

function show(message, type = 'info') {
  const el = document.createElement('div')
  const isError = type === 'error'
  const isInfo = type === 'info'
  const isWarning = type === 'warning'
  el.className = 'toast-message'
  Object.assign(el.style, {
    padding: '12px 16px',
    borderRadius: '12px',
    fontSize: '14px',
    fontWeight: '600',
    color: isError ? '#fef2f2' : isWarning ? '#1c1917' : isInfo ? '#e0f2fe' : '#f0fdf4',
    background: isError ? 'rgba(185, 28, 28, 0.95)' : isWarning ? 'rgba(245, 158, 11, 0.95)' : isInfo ? 'rgba(2, 132, 199, 0.95)' : 'rgba(22, 101, 52, 0.95)',
    boxShadow: '0 4px 12px rgba(0,0,0,0.25)',
    pointerEvents: 'auto',
    animation: 'toast-in 0.25s ease-out',
  })
  el.textContent = typeof message === 'string' ? message : (message?.message || 'Error')
  const c = getContainer()
  if (c) {
    c.appendChild(el)
    toasts.push(el)
    setTimeout(() => {
      el.style.animation = 'toast-out 0.2s ease-in forwards'
      setTimeout(() => {
        if (el.parentNode) el.parentNode.removeChild(el)
        const i = toasts.indexOf(el)
        if (i > -1) toasts.splice(i, 1)
      }, 200)
    }, 3500)
  } else {
    alert(typeof message === 'string' ? message : message?.message || 'Error')
  }
}

export function useToast() {
  return {
    success: (msg) => show(msg, 'success'),
    error: (msg) => show(msg, 'error'),
    info: (msg) => show(msg, 'info'),
    warning: (msg) => show(msg, 'warning'),
  }
}
