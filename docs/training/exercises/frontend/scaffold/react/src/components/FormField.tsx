/**
 * 通用表单字段组件（已完成）
 *
 * 提供统一的表单字段渲染，包含标签、输入框、错误提示。
 */
import React from 'react'

interface FormFieldProps {
  label: string
  name: string
  type?: 'text' | 'email' | 'tel' | 'date' | 'select'
  value: string
  onChange: (name: string, value: string) => void
  error?: string
  required?: boolean
  placeholder?: string
  options?: readonly string[]
}

const FormField: React.FC<FormFieldProps> = ({
  label,
  name,
  type = 'text',
  value,
  onChange,
  error,
  required = false,
  placeholder,
  options,
}) => {
  return (
    <div className={`form-field ${error ? 'form-field--error' : ''}`}>
      <label className="form-field__label" htmlFor={name}>
        {label} {required && <span className="form-field__required">*</span>}
      </label>

      {type === 'select' && options ? (
        <select
          id={name}
          className="form-field__input"
          value={value}
          onChange={(e) => onChange(name, e.target.value)}
        >
          <option value="">请选择</option>
          {options.map((opt) => (
            <option key={opt} value={opt}>
              {opt}
            </option>
          ))}
        </select>
      ) : (
        <input
          id={name}
          className="form-field__input"
          type={type}
          value={value}
          onChange={(e) => onChange(name, e.target.value)}
          placeholder={placeholder}
        />
      )}

      {error && <span className="form-field__error">{error}</span>}
    </div>
  )
}

export default FormField
