/**
 * 表单类型定义（已完成）
 */

/** 步骤1：基本信息 */
export interface BasicInfo {
  name: string
  phone: string
  email: string
}

/** 步骤2：工作信息 */
export interface WorkInfo {
  department: string
  position: string
  startDate: string
}

/** 完整表单数据 */
export interface FormData {
  basic: BasicInfo
  work: WorkInfo
}

/** 可选部门列表 */
export const DEPARTMENTS = [
  '技术部',
  '产品部',
  '设计部',
  '运营部',
  '人事部',
] as const

/** 表单步骤 */
export type StepNumber = 1 | 2 | 3

/** 验证错误 */
export type ValidationErrors = Record<string, string>
