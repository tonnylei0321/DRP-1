/**
 * CTIO 指标 API
 * 获取106项FIBO标注指标的当前值
 */
import { request } from './client';
import type { CtioDomainCode } from '../data/indicators';

export interface CtioIndicatorResponse {
  code: string;           // IND-BA-001
  name: string;           // 指标名称
  businessDomain: CtioDomainCode; // 所属域
  currentValue: number;   // 当前值
  targetValue: number;    // 目标值
  warnThreshold: number; // 预警阈值
  redLine: number;        // 红线阈值
  unit: string;           // 单位
  isInverse: boolean;     // 是否反向指标
}

/** 获取全部指标 */
export async function fetchIndicators(): Promise<CtioIndicatorResponse[]> {
  return request<CtioIndicatorResponse[]>('GET', '/indicators');
}

/** 按域获取指标 */
export async function fetchIndicatorsByDomain(domain: CtioDomainCode): Promise<CtioIndicatorResponse[]> {
  const all = await fetchIndicators();
  return all.filter(ind => ind.businessDomain === domain);
}

/** 获取单个指标 */
export async function fetchIndicator(code: string): Promise<CtioIndicatorResponse> {
  return request<CtioIndicatorResponse>('GET', `/indicators/${code}`);
}

/** 按实体获取指标（穿透钻取） */
export async function fetchIndicatorsByEntity(entityId: string): Promise<CtioIndicatorResponse[]> {
  return request<CtioIndicatorResponse[]>('GET', `/indicators?entity_id=${entityId}`);
}
