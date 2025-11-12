import React from 'react';

export default function SharedButton({
  children,
  variant = 'primary',
  className = '',
  ...props
}) {
  const base =
    'inline-flex items-center justify-center px-3 py-1.5 rounded-lg text-xs font-semibold transition border';

  const variants = {
    primary:
      'bg-primary-500 hover:bg-primary-600 border-primary-500 text-white',
    ghost:
      'bg-slate-800 hover:bg-slate-700 border-slate-600 text-slate-100',
    danger:
      'bg-red-600 hover:bg-red-700 border-red-600 text-white',
    outline:
      'bg-transparent hover:bg-slate-800 border-slate-600 text-slate-100'
  };

  return (
    <button
      className={`${base} ${variants[variant] || variants.primary} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
