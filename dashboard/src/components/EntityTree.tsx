/**
 * EntityTree — 左侧实体树，支持风险过滤，与地图联动
 */
import { useState } from 'react';

export type RiskLevel = 'all' | 'none' | 'low' | 'medium' | 'high';

export interface EntityNode {
  id: string;
  name: string;
  type: 'group' | 'region' | 'entity' | 'account';
  risk: 'none' | 'low' | 'medium' | 'high';
  children?: EntityNode[];
  lat?: number;
  lon?: number;
}

interface EntityTreeProps {
  data: EntityNode;
  selectedId: string | null;
  onNodeSelect: (node: EntityNode) => void;
  filter: RiskLevel;
}

const RISK_COLORS = {
  none: 'var(--risk-none)',
  low: 'var(--risk-low)',
  medium: 'var(--risk-medium)',
  high: 'var(--risk-high)',
};

function TreeNode({ node, depth, selectedId, onSelect }: {
  node: EntityNode;
  depth: number;
  selectedId: string | null;
  onSelect: (n: EntityNode) => void;
}) {
  const [expanded, setExpanded] = useState(depth < 2);
  const isSelected = selectedId === node.id;

  const hasChildren = node.children && node.children.length > 0;

  return (
    <div>
      <div
        className={`tree-node${isSelected ? ' selected' : ''}`}
        style={{ paddingLeft: `${depth * 16 + 10}px` }}
        onClick={() => {
          if (hasChildren) setExpanded(e => !e);
          onSelect(node);
        }}
      >
        {/* 展开/折叠图标 */}
        <span style={{ color: 'var(--text-muted)', fontSize: '10px', width: '12px', flexShrink: 0 }}>
          {hasChildren ? (expanded ? '▼' : '▶') : ''}
        </span>

        {/* 风险指示点 */}
        <div
          className={`tree-node-icon${node.risk === 'high' ? ' pulse-high' : ''}`}
          style={{
            background: RISK_COLORS[node.risk],
            boxShadow: `0 0 4px ${RISK_COLORS[node.risk]}`,
          }}
        />

        {/* 标签 */}
        <span className="tree-node-label">{node.name}</span>

        {/* 类型标签 */}
        <span style={{
          fontFamily: 'var(--font-mono)',
          fontSize: '9px',
          color: 'var(--text-muted)',
          background: 'rgba(255,255,255,0.05)',
          padding: '1px 5px',
          borderRadius: '2px',
          flexShrink: 0,
        }}>
          {node.type.toUpperCase()}
        </span>
      </div>

      {/* 子节点 */}
      {hasChildren && expanded && (
        <div>
          {node.children!.map(child => (
            <TreeNode
              key={child.id}
              node={child}
              depth={depth + 1}
              selectedId={selectedId}
              onSelect={onSelect}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default function EntityTree({ data, selectedId, onNodeSelect, filter }: EntityTreeProps) {
  const [search, setSearch] = useState('');

  function filterNode(node: EntityNode): EntityNode | null {
    const matchesFilter = filter === 'all' || node.risk === filter;
    const matchesSearch = !search || node.name.toLowerCase().includes(search.toLowerCase());

    if (!matchesFilter && !matchesSearch) return null;

    const filteredChildren = node.children
      ?.map(c => filterNode(c))
      .filter((c): c is EntityNode => c !== null);

    return {
      ...node,
      children: filteredChildren,
    };
  }

  const filteredData = filterNode(data);

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* 搜索 */}
      <div style={{ padding: '10px' }}>
        <input
          type="text"
          placeholder="搜索实体..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          style={{ width: '100%' }}
        />
      </div>

      {/* 树 */}
      <div style={{ flex: 1, overflowY: 'auto', paddingBottom: '10px' }}>
        {filteredData && (
          <TreeNode
            node={filteredData}
            depth={0}
            selectedId={selectedId}
            onSelect={onNodeSelect}
          />
        )}
      </div>
    </div>
  );
}
