export function getLevelAndAncestors(params: Api.SystemManage.OrgUnits) {
  // 确保参数有效性
  if (!params || typeof params.level !== 'number' || !params.ancestors || !params.id) {
    console.error('[getLevelAndAncestors] Invalid params:', params);
    return { level: 1, ancestors: '0' };
  }

  const level = params.level + 1;
  const ancestors = `${params.ancestors},${params.id}`;

  console.log('[getLevelAndAncestors] Input:', {
    parentLevel: params.level,
    parentAncestors: params.ancestors,
    parentId: params.id
  });
  console.log('[getLevelAndAncestors] Output:', { level, ancestors });

  return { level, ancestors };
}
