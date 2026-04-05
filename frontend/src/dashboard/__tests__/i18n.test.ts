import { describe, it, expect } from 'vitest';
import { t, STRINGS } from '../i18n';

describe('i18n — t() 翻译函数', () => {
  it('t("zh", key) 返回中文翻译', () => {
    expect(t('zh', 'title')).toBe(STRINGS.zh.title);
    expect(t('zh', 'connected')).toBe('已连接');
    expect(t('zh', 'noData')).toBe('暂无数据');
  });

  it('t("en", key) 返回英文翻译', () => {
    expect(t('en', 'title')).toBe(STRINGS.en.title);
    expect(t('en', 'connected')).toBe('Connected');
    expect(t('en', 'noData')).toBe('No Data');
  });

  it('t(lang, unknownKey) 返回 key 本身', () => {
    expect(t('zh', 'nonExistentKey')).toBe('nonExistentKey');
    expect(t('en', 'anotherMissingKey')).toBe('anotherMissingKey');
  });
});


// ─── 属性测试 — Property 5-7: i18n ──────────────────────────────────────────

import * as fc from 'fast-check';

describe('属性测试 — Property 5: i18n 翻译查找', () => {
  it('Feature: admin-portal-testing, Property 5: 已知 key 返回正确翻译', () => {
    const zhKeys = Object.keys(STRINGS.zh);
    const enKeys = Object.keys(STRINGS.en);

    fc.assert(
      fc.property(
        fc.constantFrom(...zhKeys),
        (key) => {
          expect(t('zh', key)).toBe(STRINGS.zh[key]);
        }
      ),
      { numRuns: Math.min(100, zhKeys.length * 10) }
    );

    fc.assert(
      fc.property(
        fc.constantFrom(...enKeys),
        (key) => {
          expect(t('en', key)).toBe(STRINGS.en[key]);
        }
      ),
      { numRuns: Math.min(100, enKeys.length * 10) }
    );
  });
});

describe('属性测试 — Property 6: i18n 未知 key fallback', () => {
  it('Feature: admin-portal-testing, Property 6: 未知 key 返回 key 本身', () => {
    const allKeys = new Set([...Object.keys(STRINGS.zh), ...Object.keys(STRINGS.en)]);

    fc.assert(
      fc.property(
        fc.string({ minLength: 1 }).filter(s => !allKeys.has(s)),
        (key) => {
          expect(t('zh', key)).toBe(key);
          expect(t('en', key)).toBe(key);
        }
      ),
      { numRuns: 100 }
    );
  });
});

describe('属性测试 — Property 7: i18n 中英文键完整性', () => {
  it('Feature: admin-portal-testing, Property 7: zh 和 en 的 key 集合完全相同', () => {
    const zhKeys = new Set(Object.keys(STRINGS.zh));
    const enKeys = new Set(Object.keys(STRINGS.en));

    for (const key of zhKeys) {
      expect(enKeys.has(key)).toBe(true);
    }
    for (const key of enKeys) {
      expect(zhKeys.has(key)).toBe(true);
    }
    expect(zhKeys.size).toBe(enKeys.size);
  });
});
