/**
 * RiskTicker — 底部状态栏（原型风格）
 */
import { useState, useEffect } from 'react';

export default function RiskTicker() {
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const id = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <footer>
      <span>SYSTEM_TIME: {time.toISOString().replace('T', ' ').slice(0, 19)} UTC</span>
      <span style={{ marginLeft: '20px' }}>ENGINE: Ontotext GraphDB 10.5</span>
      <span style={{ marginLeft: '20px' }}>FIBO ONTOLOGY: v2.4.1</span>
      <span style={{ marginLeft: 'auto' }}>PROPRIETARY DATA: CONFIDENTIAL</span>
    </footer>
  );
}
