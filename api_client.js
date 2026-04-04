// ============================================================
// api_client.js — API 客户端模块
// 封装 fetch API，统一添加 Authorization: Bearer <token> 头
// 处理 HTTP 错误、网络超时、401 重定向
//
// 依赖：auth.js（全局变量 Auth、BASE_URL）
// 确保 auth.js 在 api_client.js 之前加载
// ============================================================

var ApiClient = (function () {
  var TIMEOUT = 15000; // 15 秒超时

  /**
   * 通用请求方法，自动注入 Bearer token
   * @param {string} method - HTTP 方法（GET/POST/PUT/DELETE 等）
   * @param {string} path - 请求路径（如 '/org/tree'）
   * @param {object} [options] - 可选配置
   * @param {object} [options.body] - 请求体（POST/PUT 时使用）
   * @param {object} [options.params] - URL 查询参数
   * @param {object} [options.headers] - 额外请求头
   * @returns {Promise<any>} resolve 时返回 JSON 数据，reject 时返回错误对象
   */
  function request(method, path, options) {
    options = options || {};
    var url = BASE_URL + path;

    // 拼接查询参数
    if (options.params) {
      var queryParts = [];
      var params = options.params;
      for (var key in params) {
        if (params.hasOwnProperty(key) && params[key] != null) {
          queryParts.push(
            encodeURIComponent(key) + '=' + encodeURIComponent(params[key])
          );
        }
      }
      if (queryParts.length > 0) {
        url += '?' + queryParts.join('&');
      }
    }

    // 构建请求头
    var headers = Object.assign({}, options.headers || {});
    var token = Auth.getToken();
    if (token) {
      headers['Authorization'] = 'Bearer ' + token;
    }

    // 构建 fetch 配置
    var fetchOptions = {
      method: method,
      headers: headers,
    };

    // POST/PUT 等方法附加请求体
    if (options.body !== undefined) {
      headers['Content-Type'] = 'application/json';
      fetchOptions.headers = headers;
      fetchOptions.body = JSON.stringify(options.body);
    }

    // 使用 AbortController 实现超时
    var controller = new AbortController();
    fetchOptions.signal = controller.signal;
    var timeoutId = setTimeout(function () {
      controller.abort();
    }, TIMEOUT);

    return fetch(url, fetchOptions)
      .then(function (response) {
        clearTimeout(timeoutId);

        // HTTP 401 → 调用 Auth.logout() 重定向
        if (response.status === 401) {
          var error401 = {
            status: 401,
            detail: '令牌无效或已过期',
            url: url,
          };
          console.error(
            '[DRP API Error] ' + method + ' ' + url + ' → 401: ' + error401.detail
          );
          Auth.logout();
          return Promise.reject(error401);
        }

        // HTTP 4xx/5xx → 结构化错误对象
        if (!response.ok) {
          return response
            .json()
            .catch(function () {
              return { detail: 'HTTP ' + response.status };
            })
            .then(function (errBody) {
              var detail = errBody.detail || 'HTTP ' + response.status;
              var errorObj = {
                status: response.status,
                detail: detail,
                url: url,
              };
              console.error(
                '[DRP API Error] ' +
                  method +
                  ' ' +
                  url +
                  ' → ' +
                  response.status +
                  ': ' +
                  detail
              );
              return Promise.reject(errorObj);
            });
        }

        // 成功响应 → 返回 JSON
        return response.json();
      })
      .catch(function (err) {
        clearTimeout(timeoutId);

        // 已经是结构化错误对象（来自上面的 reject），直接传递
        if (err && typeof err === 'object' && err.status !== undefined) {
          return Promise.reject(err);
        }

        // 网络超时（AbortError）或网络不可达（TypeError）
        var detail;
        if (err && err.name === 'AbortError') {
          detail = '请求超时（' + TIMEOUT / 1000 + '秒）';
        } else {
          detail = err ? err.message || '网络不可达' : '网络不可达';
        }

        var networkError = {
          status: 'network_error',
          detail: detail,
          url: url,
        };
        console.error(
          '[DRP API Error] ' +
            method +
            ' ' +
            url +
            ' → network_error: ' +
            detail
        );
        return Promise.reject(networkError);
      });
  }

  /**
   * GET 快捷方法
   * @param {string} path - 请求路径
   * @param {object} [params] - URL 查询参数对象
   * @returns {Promise<any>}
   */
  function get(path, params) {
    return request('GET', path, { params: params });
  }

  /**
   * POST 快捷方法
   * @param {string} path - 请求路径
   * @param {object} body - 请求体
   * @returns {Promise<any>}
   */
  function post(path, body) {
    return request('POST', path, { body: body });
  }

  /**
   * 文件下载（返回 Blob）
   * @param {string} path - 下载路径
   * @returns {Promise<Blob>}
   */
  function download(path) {
    var url = BASE_URL + path;

    var headers = {};
    var token = Auth.getToken();
    if (token) {
      headers['Authorization'] = 'Bearer ' + token;
    }

    var controller = new AbortController();
    var timeoutId = setTimeout(function () {
      controller.abort();
    }, TIMEOUT);

    return fetch(url, {
      method: 'GET',
      headers: headers,
      signal: controller.signal,
    })
      .then(function (response) {
        clearTimeout(timeoutId);

        if (response.status === 401) {
          var error401 = {
            status: 401,
            detail: '令牌无效或已过期',
            url: url,
          };
          console.error(
            '[DRP API Error] GET ' + url + ' → 401: ' + error401.detail
          );
          Auth.logout();
          return Promise.reject(error401);
        }

        if (!response.ok) {
          return response
            .json()
            .catch(function () {
              return { detail: 'HTTP ' + response.status };
            })
            .then(function (errBody) {
              var detail = errBody.detail || 'HTTP ' + response.status;
              var errorObj = {
                status: response.status,
                detail: detail,
                url: url,
              };
              console.error(
                '[DRP API Error] GET ' +
                  url +
                  ' → ' +
                  response.status +
                  ': ' +
                  detail
              );
              return Promise.reject(errorObj);
            });
        }

        return response.blob();
      })
      .catch(function (err) {
        clearTimeout(timeoutId);

        if (err && typeof err === 'object' && err.status !== undefined) {
          return Promise.reject(err);
        }

        var detail;
        if (err && err.name === 'AbortError') {
          detail = '请求超时（' + TIMEOUT / 1000 + '秒）';
        } else {
          detail = err ? err.message || '网络不可达' : '网络不可达';
        }

        var networkError = {
          status: 'network_error',
          detail: detail,
          url: url,
        };
        console.error(
          '[DRP API Error] GET ' + url + ' → network_error: ' + detail
        );
        return Promise.reject(networkError);
      });
  }

  return {
    TIMEOUT: TIMEOUT,
    request: request,
    get: get,
    post: post,
    download: download,
  };
})();
