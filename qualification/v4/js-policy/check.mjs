// Parse data only. Passing this narrow reducer policy never authorizes execution.
import { parse } from 'acorn';
import fs from 'node:fs';

export function check(source) {
  if (typeof source !== 'string' || Buffer.byteLength(source) > 8192) return false;
  let tree;
  try { tree = parse(source, { ecmaVersion: 2022, sourceType: 'script' }); }
  catch { return false; }
  const statement = tree.body[0];
  const assignment = statement?.expression;
  if (tree.body.length !== 1 || statement.type !== 'ExpressionStatement' ||
      assignment?.type !== 'AssignmentExpression' || assignment.operator !== '=' ||
      assignment.left.type !== 'MemberExpression' || assignment.left.computed ||
      assignment.left.object.name !== 'module' || assignment.left.property.name !== 'exports') return false;
  const fn = assignment.right;
  if (!['ArrowFunctionExpression', 'FunctionExpression'].includes(fn.type) || fn.async || fn.generator ||
      fn.params.length !== 2 || fn.params.some(p => p.type !== 'Identifier')) return false;
  const forbidden = new Set(['process','global','globalThis','require','eval','Function','constructor',
    '__proto__','prototype','module','exports','this','arguments']);
  const allowed = new Set(['BlockStatement','ReturnStatement','IfStatement','SwitchStatement','SwitchCase',
    'BreakStatement','VariableDeclaration','VariableDeclarator','Identifier','Literal','ObjectExpression',
    'Property','SpreadElement','MemberExpression','BinaryExpression','LogicalExpression','UnaryExpression',
    'ConditionalExpression','ObjectPattern','EmptyStatement']);
  const locals = new Set(fn.params.map(p => p.name));
  function bindings(node) {
    if (node?.type === 'Identifier') locals.add(node.name);
    else if (node?.type === 'ObjectPattern') for (const p of node.properties) {
      if (p.type !== 'Property' || p.computed || p.value.type !== 'Identifier') throw Error('binding');
      locals.add(p.value.name);
    } else throw Error('binding');
  }
  function collect(node) {
    if (!node || typeof node !== 'object') return;
    if (node.type === 'VariableDeclarator') bindings(node.id);
    for (const [key,value] of Object.entries(node)) if (key !== 'start' && key !== 'end') {
      if (Array.isArray(value)) value.forEach(collect); else if (value && typeof value === 'object') collect(value);
    }
  }
  try { collect(fn.body); } catch { return false; }
  if ([...locals].some(n => forbidden.has(n))) return false;
  function visit(node, parent, key) {
    if (!node || typeof node !== 'object') return true;
    if (!allowed.has(node.type)) return false;
    if (node.type === 'MemberExpression' && (node.computed || node.optional)) return false;
    if (node.type === 'Property' && (node.computed || node.method || node.kind !== 'init')) return false;
    if (node.type === 'UnaryExpression' && !['!','typeof','+','-','~'].includes(node.operator)) return false;
    if (node.type === 'Literal' && node.regex) return false;
    if (node.type === 'Identifier') {
      if (forbidden.has(node.name)) return false;
      const property = parent?.type === 'MemberExpression' && key === 'property' || parent?.type === 'Property' && key === 'key';
      if (!property && !locals.has(node.name) && node.name !== 'undefined') return false;
    }
    for (const [childKey,value] of Object.entries(node)) {
      if (Array.isArray(value) && !value.every(v => visit(v,node,childKey))) return false;
      if (value && typeof value === 'object' && !Array.isArray(value) && !visit(value,node,childKey)) return false;
    }
    return true;
  }
  return visit(fn.body,null,'body');
}

if (process.argv[1] === new URL(import.meta.url).pathname) {
  const input = fs.readFileSync(0,'utf8');
  if (Buffer.byteLength(input)>10000) throw Error('input bound');
  console.log(JSON.stringify({version:'reducer-ast/4.0.0',allowed:check(JSON.parse(input)),execution_authority:false}));
}
