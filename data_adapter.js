// ============================================================
// data_adapter.js — 数据格式适配层
// 将后端 API 响应转换为前端现有渲染函数期望的数据结构
// 对缺失字段提供合理默认值，实现指标状态计算逻辑
//
// 依赖：prototype_app.js 中的 DOMAINS 全局变量（7大领域定义）
// 确保 prototype_app.js 在 data_adapter.js 之前加载
// ============================================================

var DataAdapter = (function () {

  // 合法的关系类型集合
  var VALID_REL_TYPES = {
    hasSubsidiary: true,
    fundFlow: true,
    guarantee: true,
    borrowing: true,
    fxExposure: true,
  };

  /**
   * 计算单个指标的红黄绿状态
   *
   * direction='up'（越高越好）:
   *   红: value < threshold[0]
   *   黄: threshold[0] <= value < threshold[0]*1.1
   *   绿: value >= threshold[0]*1.1
   *
   * direction='down'（越低越好）:
   *   红: value > threshold[1]
   *   黄: threshold[1]*0.9 <= value <= threshold[1]
   *   绿: value < threshold[1]*0.9
   *
   * direction='mid'（区间内好）:
   *   红: value < threshold[0] 或 value > threshold[1]
   *   黄: 在区间内但接近边界
   *   绿: 在区间内且远离边界
   *
   * threshold 为 null 时返回 'normal'
   * value 非数值时返回 'normal'
   *
   * @param {*} value - 指标值
   * @param {Array} threshold - [下限, 上限]
   * @param {string} direction - 'up'/'down'/'mid'
   * @returns {'danger'|'warn'|'normal'}
   */
  function computeStatus(value, threshold, direction) {
    // value 非数值时返回 'normal'
    if (typeof value !== 'number' || isNaN(value)) return 'normal';

    // threshold 为 null/undefined 或非数组时返回 'normal'
    if (!threshold || !Array.isArray(threshold)) return 'normal';

    if (direction === 'up') {
      var th = threshold[0];
      // threshold[0] 为 null 时无法判断，返回 'normal'
      if (th === null || th === undefined) return 'normal';
      if (th === 0) {
        // 阈值为 0 时：value < 0 为 danger，否则 normal
        if (value < 0) return 'danger';
        return 'normal';
      }
      if (value < th) return 'danger';
      if (value < th * 1.1) return 'warn';
      return 'normal';
    }

    if (direction === 'down') {
      var th = threshold[1];
      // threshold[1] 为 null 时无法判断，返回 'normal'
      if (th === null || th === undefined) return 'normal';
      if (th === 0) {
        // 阈值为 0 时（如"超限额担保笔数应为0"）：value > 0 为 danger
        if (value > 0) return 'danger';
        return 'normal';
      }
      if (value > th) return 'danger';
      if (value >= th * 0.9) return 'warn';
      return 'normal';
    }

    if (direction === 'mid') {
      var lo = threshold[0];
      var hi = threshold[1];
      // 两端都为 null 时无法判断
      if ((lo === null || lo === undefined) && (hi === null || hi === undefined)) return 'normal';
      var loVal = (lo !== null && lo !== undefined) ? lo : 0;
      var hiVal = (hi !== null && hi !== undefined) ? hi : 100;
      // 超出区间 → danger
      if (value < loVal || value > hiVal) return 'danger';
      // 接近边界 → warn（区间内但在边界 10% 范围内）
      var range = hiVal - loVal;
      var margin = range * 0.1;
      if (value < loVal + margin || value > hiVal - margin) return 'warn';
      return 'normal';
    }

    // 未知 direction，返回 'normal'
    return 'normal';
  }

  /**
   * 递归转换后端组织架构数据为前端 ORG 树格式
   * 补充缺失字段默认值，递归处理 children 数组
   *
   * @param {object} backendData - 后端返回的组织架构 JSON
   * @returns {object} 前端 ORG 兼容的树节点
   */
  function adaptOrgTree(backendData) {
    if (!backendData || typeof backendData !== 'object') {
      return {
        id: '', name: '', level: 0, type: '未知', city: '',
        cash: 0, debt: 0, asset: 0, guarantee: 0,
        compliance: 0, risk: 'lo', has_children: false, children: [],
      };
    }

    var node = {
      id: backendData.id || '',
      name: backendData.name || '',
      level: typeof backendData.level === 'number' ? backendData.level : 0,
      type: backendData.type || '未知',
      city: backendData.city || '',
      cash: typeof backendData.cash === 'number' ? backendData.cash : 0,
      debt: typeof backendData.debt === 'number' ? backendData.debt : 0,
      asset: typeof backendData.asset === 'number' ? backendData.asset : 0,
      guarantee: typeof backendData.guarantee === 'number' ? backendData.guarantee : 0,
      compliance: typeof backendData.compliance === 'number' ? backendData.compliance : 0,
      risk: backendData.risk || 'lo',
      has_children: !!backendData.has_children,
      children: [],
    };

    // 递归处理 children
    if (Array.isArray(backendData.children)) {
      node.children = backendData.children.map(function (child) {
        return adaptOrgTree(child);
      });
      // 如果有 children 数据，同步更新 has_children
      if (node.children.length > 0) {
        node.has_children = true;
      }
    }

    return node;
  }

  /**
   * 按7大领域分组后端指标数据，计算每个指标的 status
   * 返回格式与 generateIndicators() 返回值一致
   *
   * @param {Array} backendIndicators - 后端返回的指标数组
   *   每个元素: {id, name, domain, unit, value, threshold, direction}
   * @param {Array} domainsDef - 前端 DOMAINS 数组（7大领域定义）
   * @returns {object} 按领域 ID 分组的指标数据
   */
  function adaptIndicators(backendIndicators, domainsDef) {
    var result = {};

    // 初始化所有领域
    domainsDef.forEach(function (dom) {
      result[dom.id] = {
        score: 0,
        alertCount: 0,
        indicators: [],
      };
    });

    // 按 domain 分组指标
    if (Array.isArray(backendIndicators)) {
      backendIndicators.forEach(function (ind) {
        var domainId = ind.domain;
        if (!result[domainId]) return; // 跳过未知领域

        var status = computeStatus(ind.value, ind.threshold, ind.direction);

        if (status === 'danger') {
          result[domainId].alertCount++;
        }

        result[domainId].indicators.push({
          id: ind.id || '',
          name: ind.name || '',
          unit: ind.unit || '',
          value: typeof ind.value === 'number'
            ? Math.round(ind.value * 100) / 100
            : (ind.value || ''),
          status: status,
          threshold: ind.threshold || [null, null],
          direction: ind.direction || 'up',
        });
      });
    }

    // 计算每个领域的 score（正常指标占比 * 100）
    Object.keys(result).forEach(function (domId) {
      var domData = result[domId];
      var total = domData.indicators.length;
      if (total === 0) {
        domData.score = 0;
        return;
      }
      var ok = domData.indicators.filter(function (x) { return x.status === 'normal'; }).length;
      var warn = domData.indicators.filter(function (x) { return x.status === 'warn'; }).length;
      domData.score = Math.round((ok * 100 + warn * 60) / total);
    });

    return result;
  }

  /**
   * 映射后端关系数据到前端 graphEdges 数组
   * 确保 source/target 为非空字符串，type 为合法值
   * 过滤掉不合法的关系
   *
   * @param {Array} backendRelations - 后端返回的关系数组
   *   每个元素: {source, target, type}
   * @returns {Array} 过滤后的 graphEdges 数组
   */
  function adaptRelations(backendRelations) {
    if (!Array.isArray(backendRelations)) return [];

    return backendRelations.filter(function (rel) {
      // source/target 必须为非空字符串
      if (!rel.source || typeof rel.source !== 'string') return false;
      if (!rel.target || typeof rel.target !== 'string') return false;
      // type 必须是合法值之一
      if (!VALID_REL_TYPES[rel.type]) return false;
      return true;
    }).map(function (rel) {
      return {
        source: rel.source,
        target: rel.target,
        type: rel.type,
      };
    });
  }

  /**
   * 从后端穿透路径数据提取前端节点 ID
   * 从 node_iri 中提取最后一个分隔符（: / #）之后的子串作为前端节点 ID
   *
   * @param {Array} backendPath - 后端返回的穿透路径数组
   *   每个元素: {step, node_iri, node_type, node_label}
   * @returns {Array} [{step, nodeId, nodeType, nodeLabel}]
   */
  function adaptDrillPath(backendPath) {
    if (!Array.isArray(backendPath)) return [];

    return backendPath.map(function (item) {
      var nodeIri = item.node_iri || '';
      var nodeId = nodeIri;

      // 从 node_iri 提取最后一段（支持 : / # 三种分隔符）
      if (nodeIri) {
        // 找到最后一个分隔符的位置
        var lastColon = nodeIri.lastIndexOf(':');
        var lastSlash = nodeIri.lastIndexOf('/');
        var lastHash = nodeIri.lastIndexOf('#');
        var lastSep = Math.max(lastColon, lastSlash, lastHash);
        if (lastSep >= 0 && lastSep < nodeIri.length - 1) {
          nodeId = nodeIri.substring(lastSep + 1);
        }
      }

      return {
        step: typeof item.step === 'number' ? item.step : 0,
        nodeId: nodeId,
        nodeType: item.node_type || '',
        nodeLabel: item.node_label || '',
      };
    });
  }

  // 公开接口
  return {
    computeStatus: computeStatus,
    adaptOrgTree: adaptOrgTree,
    adaptIndicators: adaptIndicators,
    adaptRelations: adaptRelations,
    adaptDrillPath: adaptDrillPath,
  };

})();
