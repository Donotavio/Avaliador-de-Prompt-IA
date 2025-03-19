import React, { ButtonHTMLAttributes, ReactNode } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  variant?: 'primary' | 'secondary' | 'outline' | 'danger' | 'success';
  size?: 'sm' | 'md' | 'lg';
  icon?: ReactNode;
  isLoading?: boolean;
  isFullWidth?: boolean;
}

const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  icon,
  isLoading = false,
  isFullWidth = false,
  className = '',
  disabled,
  ...props
}) => {
  // Determinar classes baseadas nas props
  const variantClass = `btn-${variant}`;
  const sizeClass = size === 'md' ? '' : `btn-${size}`;
  const widthClass = isFullWidth ? 'w-full' : '';
  const disabledClass = disabled || isLoading ? 'btn-disabled' : '';
  
  // Combinar todas as classes
  const buttonClasses = [
    'btn',
    variantClass,
    sizeClass,
    widthClass,
    disabledClass,
    className
  ].filter(Boolean).join(' ');

  return (
    <button
      className={buttonClasses}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <>
          <span className="spinner spinner-sm mr-2"></span>
          <span>Carregando...</span>
        </>
      ) : (
        <>
          {icon && <span className="mr-2">{icon}</span>}
          {children}
        </>
      )}
    </button>
  );
};

export default Button; 