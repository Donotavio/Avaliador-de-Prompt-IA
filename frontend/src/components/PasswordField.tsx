import React, { useState } from 'react';
import { EyeIcon, EyeOffIcon, InfoIcon } from './Icons';

interface PasswordFieldProps {
  id: string;
  name: string;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  required?: boolean;
  minLength?: number;
  label?: string;
  placeholder?: string;
  showHint?: boolean;
  hintText?: string;
  className?: string;
}

const PasswordField: React.FC<PasswordFieldProps> = ({
  id,
  name,
  value,
  onChange,
  required = false,
  minLength,
  label,
  placeholder,
  showHint = false,
  hintText = 'Mínimo de 8 caracteres',
  className = '',
}) => {
  const [showPassword, setShowPassword] = useState(false);

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  return (
    <div className={`password-field-container ${className}`}>
      {label && <label htmlFor={id}>{label}{required && '*'}</label>}
      
      <div className="password-input-wrapper">
        <input
          type={showPassword ? 'text' : 'password'}
          id={id}
          name={name}
          value={value}
          onChange={onChange}
          required={required}
          minLength={minLength}
          placeholder={placeholder}
          className="password-input"
        />
        
        <button
          type="button"
          onClick={togglePasswordVisibility}
          className="password-toggle-button"
          tabIndex={-1}
          aria-label={showPassword ? 'Ocultar senha' : 'Mostrar senha'}
        >
          {showPassword ? (
            <EyeOffIcon size={20} />
          ) : (
            <EyeIcon size={20} />
          )}
        </button>
      </div>
      
      {showHint && (
        <div className="password-hint">
          <InfoIcon size={14} />
          <span>{hintText}</span>
        </div>
      )}
    </div>
  );
};

export default PasswordField; 