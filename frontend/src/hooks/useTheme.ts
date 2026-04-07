/**
 * 主题管理 Hook — 支持 dark / light / system 三种模式
 * 持久化到 localStorage，监听系统偏好变化
 */
import { useState, useEffect, useCallback } from 'react';

export type ThemeMode = 'dark' | 'light' | 'system';

const STORAGE_KEY = 'drp_theme';

function getSystemTheme(): 'dark' | 'light' {
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function applyTheme(resolved: 'dark' | 'light') {
  document.documentElement.setAttribute('data-theme', resolved);
}

export function useTheme() {
  const [mode, setModeState] = useState<ThemeMode>(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === 'dark' || saved === 'light' || saved === 'system') return saved;
    return 'dark'; // 默认深色
  });

  const resolved: 'dark' | 'light' = mode === 'system' ? getSystemTheme() : mode;

  const setMode = useCallback((m: ThemeMode) => {
    setModeState(m);
    localStorage.setItem(STORAGE_KEY, m);
  }, []);

  // 应用主题到 DOM
  useEffect(() => {
    applyTheme(resolved);
  }, [resolved]);

  // 监听系统偏好变化（仅 system 模式下生效）
  useEffect(() => {
    if (mode !== 'system') return;
    const mql = window.matchMedia('(prefers-color-scheme: dark)');
    const handler = () => applyTheme(getSystemTheme());
    mql.addEventListener('change', handler);
    return () => mql.removeEventListener('change', handler);
  }, [mode]);

  return { mode, resolved, setMode };
}
