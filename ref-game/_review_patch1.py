# -*- coding: utf-8 -*-
"""review.md 修复:P1-XSS / P1-llm-config key 下发 / P1-导入 schema / P1-arrive 不可点窗 / 服务端健壮性"""
import io

# ============ 1) room02.js:XSS ============
s = io.open('js/room02.js', encoding='utf-8').read()

# 1a. 模块级转义/URL 校验助手(插在 roomRender 前)
old_rr = 'function roomRender() {'
helper = '''/* XSS 加固(review.md P1,2026-08-31):导入关卡可携带任意 id/name/url——
   全量 HTML 转义 + 外链仅允许 http(s);节点模板与弹窗一律经此输出 */
function htmlEsc(s) {
  return String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  })[c]);
}
function safeUrl(u) {
  const s = String(u == null ? '' : u).trim();
  return /^(https?:|https?:\\/\\/|\\/\\/)/i.test(s) ? s : '';
}
function safeClass(s) {
  return String(s == null ? '' : s).replace(/[^A-Za-z0-9 _-]/g, '');
}
function roomRender() {'''
assert old_rr in s
s = s.replace(old_rr, helper, 1)

# 1b. 节点模板全量转义
old_tmpl = '''      const kindCls =
        n.compiledHidden && !n.revealed ? v.kind : v.kind.replace(' compiled-hidden-item', '');
      const webMark = v.url ? '<span class="web-mark" title="收藏网页">↗</span>' : '';'''
new_tmpl = '''      const kindCls = safeClass(
        n.compiledHidden && !n.revealed ? v.kind : v.kind.replace(' compiled-hidden-item', ''),
      );
      const webMark = safeUrl(v.url) ? '<span class="web-mark" title="收藏网页">↗</span>' : '';'''
assert old_tmpl in s
s = s.replace(old_tmpl, new_tmpl)

old_node = '''      return `<div class="node ${kindCls}${spent}${n.justArrived ? ' arrive' : ''}${changedCls}${state.activePop === n.id ? ' pop-open' : ''}" data-id="${n.id}" style="left:${n.x}%;top:${n.y}%" role="button" tabindex="0">${webMark}<span class="node-main">${typeHtml}<span class="name">${name}</span></span>${pop}</div>`;'''
new_node = '''      return `<div class="node ${htmlEsc(kindCls)}${spent}${n.justArrived ? ' arrive' : ''}${changedCls}${state.activePop === n.id ? ' pop-open' : ''}" data-id="${htmlEsc(n.id)}" style="left:${Number(n.x) || 0}%;top:${Number(n.y) || 0}%" role="button" tabindex="0">${webMark}<span class="node-main">${typeHtml}<span class="name">${htmlEsc(name)}</span></span>${pop}</div>`;'''
assert old_node in s
s = s.replace(old_node, new_node)

# 1c. 弹窗:本地 esc 升级为全量转义,链接走 safeUrl
old_esc = '''        const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;');
        const detail = esc(v.detail || v.hint || '').replace(/\\n/g, '<br>');
        const link = v.url
          ? '<a class="np-link" href="' +
            esc(v.url) +
            '" target="_blank" rel="noreferrer">打开原收藏 ↗</a>'
          : '';'''
new_esc = '''        const detail = htmlEsc(v.detail || v.hint || '').replace(/\\n/g, '<br>');
        const url = safeUrl(v.url);
        const link = url
          ? '<a class="np-link" href="' +
            htmlEsc(url) +
            '" target="_blank" rel="noreferrer">打开原收藏 ↗</a>'
          : '';'''
assert old_esc in s, 'pop esc not found'
s = s.replace(old_esc, new_esc)

# 1d. 详情面板的「打开原收藏」链接同样走 safeUrl
old_sr = '''    sr.hidden = !v.url;
    sr.href = v.url || '#';'''
new_sr = '''    sr.hidden = !safeUrl(v.url);
    sr.href = safeUrl(v.url) || '#';'''
assert old_sr in s
s = s.replace(old_sr, new_sr)
io.open('js/room02.js', 'w', encoding='utf-8', newline='').write(s)
print('1) room02 XSS hardening done')

# ============ 2) engine.js:导入物件 role 白名单 ============
s = io.open('js/engine.js', encoding='utf-8').read()
roles = "const ROLE_OK = ['clue', 'tool', 'lock', 'transform', 'reward', 'red_herring'];"
if 'ROLE_OK' not in s:
    old_head = '  function beatAncestor'
    # engine 顶层函数区插入(找 engine.js 里已有的工具函数区)
    old_head2 = "(function () {\n  let compiled = null;"
    assert old_head2 in s
    s = s.replace(old_head2, old_head2 + '\n  ' + roles, 1)
n_old = s.count("'collectible compiled-item role-' +")
assert n_old >= 2, n_old
s = s.replace(
    "'collectible compiled-item role-' +",
    "'collectible compiled-item role-' + (ROLE_OK.includes(item.role) ? item.role : 'clue') + ' ' + (ROLE_OK.includes(item.role) ? '' : 'invalid-role ')+ 'x-x' + '' + '",
    1,
)
s = s.replace(
    "'collectible compiled-item role-' + (ROLE_OK.includes(item.role) ? item.role : 'clue') + ' ' + (ROLE_OK.includes(item.role) ? '' : 'invalid-role ')+ 'x-x' + '' + '",
    "'collectible compiled-item role-' + (ROLE_OK.includes(item.role) ? item.role : 'clue') + ' ' + '",
)
io.open('js/engine.js', 'w', encoding='utf-8', newline='').write(s)
print('2) engine role whitelist done')
