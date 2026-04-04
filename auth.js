// ============================================================
// auth.js — JWT 认证模块
// 管理 localStorage 中的 access_token，解析 JWT payload
// 提供 getToken() 供 api_client.js 注入 Authorization 头
//
// 安全说明：前端 JWT payload 解析（base64 解码）仅用于 UI 展示，
// 不验证签名。所有安全决策（权限、租户隔离）由后端 JWT 签名验证保证。
// ============================================================

var BASE_URL = 'http://localhost:8000';

var Auth = (function () {
  var TOKEN_KEY = 'drp_access_token';
  var TENANT_KEY = 'drp_tenant_id';

  /**
   * base64url 解码（处理 JWT 中的 URL-safe base64）
   * 将 - 替换为 +，_ 替换为 /，补齐 = 填充后调用 atob
   */
  function _base64UrlDecode(str) {
    var base64 = str.replace(/-/g, '+').replace(/_/g, '/');
    // 补齐 = 填充
    var pad = base64.length % 4;
    if (pad) {
      base64 += '='.repeat(4 - pad);
    }
    return atob(base64);
  }

  /**
   * 解析 JWT 的 payload 部分（第二段）
   * 返回解析后的 JSON 对象，解析失败返回 null
   */
  function _parseJwtPayload(token) {
    try {
      var parts = token.split('.');
      if (parts.length !== 3) return null;
      var decoded = _base64UrlDecode(parts[1]);
      return JSON.parse(decoded);
    } catch (e) {
      return null;
    }
  }

  return {
    TOKEN_KEY: TOKEN_KEY,
    TENANT_KEY: TENANT_KEY,

    /**
     * 检查是否有有效 token
     * 无 token 或 token 已过期返回 false
     */
    checkAuth: function () {
      var token = localStorage.getItem(TOKEN_KEY);
      if (!token) return false;
      if (this.isTokenExpired()) {
        this.logout();
        return false;
      }
      return true;
    },

    /**
     * 调用 POST /auth/login 登录
     * 成功后存储 access_token 到 localStorage，解析 JWT payload 存储 tenant_id
     * 失败时抛出包含 status 和 detail 的错误对象
     */
    login: async function (email, password) {
      var url = BASE_URL + '/auth/login';
      var response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email, password: password }),
      });

      if (!response.ok) {
        var errorDetail = '登录失败';
        try {
          var errBody = await response.json();
          errorDetail = errBody.detail || errorDetail;
        } catch (e) {
          // 忽略 JSON 解析失败
        }
        throw { status: response.status, detail: errorDetail };
      }

      var data = await response.json();
      localStorage.setItem(TOKEN_KEY, data.access_token);

      // 解析 JWT payload 提取 tenant_id
      var payload = _parseJwtPayload(data.access_token);
      if (payload && payload.tenant_id) {
        localStorage.setItem(TENANT_KEY, payload.tenant_id);
      }
    },

    /**
     * 退出登录：清除 localStorage 中的 token 和 tenant_id
     */
    logout: function () {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(TENANT_KEY);
    },

    /**
     * 从 localStorage 获取当前 token
     */
    getToken: function () {
      return localStorage.getItem(TOKEN_KEY);
    },

    /**
     * 从 localStorage 获取 tenant_id
     */
    getTenantId: function () {
      return localStorage.getItem(TENANT_KEY);
    },

    /**
     * 检查 token 是否已过期
     * 解析 JWT payload 中的 exp 字段，与当前时间（秒级时间戳）比较
     * 无 token 或解析失败视为已过期
     */
    isTokenExpired: function () {
      var token = localStorage.getItem(TOKEN_KEY);
      if (!token) return true;
      var payload = _parseJwtPayload(token);
      if (!payload || typeof payload.exp !== 'number') return true;
      var nowInSeconds = Math.floor(Date.now() / 1000);
      return payload.exp < nowInSeconds;
    },
  };
})();
