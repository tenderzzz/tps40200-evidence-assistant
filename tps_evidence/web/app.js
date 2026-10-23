import {setupRecords} from '/records-ui.js';
import {fieldsHTML,updateModeFields} from '/chip-ui.js';
const $ = (selector, base = document) => base.querySelector(selector);
const $$ = (selector, base = document) => [...base.querySelectorAll(selector)];
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const icon = name => `<svg class="icon" aria-hidden="true"><use href="/icons.svg#${name}"></use></svg>`;
const labels = {answered:'已找到参数',evidence_only:'相关原文',needs_information:'需要补充条件',not_found:'未找到匹配证据',unsupported:'当前资料未覆盖',invalid:'输入需要修改'};
const ruleLabels = {satisfied:'满足该项',violated:'不满足该项',needs_information:'信息不足',invalid:'输入需要修改',estimated:'标称估算'};
const ratingLabels = {absolute_maximum:'绝对最大额定值',recommended:'推荐工作条件',electrical:'电气特性'};
const fieldLabels = {vdd:'输入电压 VDD',tj:'结温 TJ',frequency:'振荡频率 fOSC',resistance:'定时电阻 RRC',capacitance:'定时电容 CRC',ambient_temperature:'环境温度 TA',resistance_tolerance:'电阻容差',capacitance_tolerance:'电容容差'};
const defaultPresets = {voltage:{kind:'query',question:'4.3 V 能正常工作吗？'},reference:{kind:'query',question:'反馈参考电压 VFB 是多少？'},timing:{kind:'check',point:{vdd:'12 V',tj:'25 °C',frequency:'100 kHz',resistance:'200 kΩ',capacitance:'470 pF',resistance_tolerance:'1%',capacitance_tolerance:'5%'}}};
const state = {boot:null,route:'manual',scene:'pdf',detail:'answer',payload:null,request:null,selectedEvidence:null,selectedParameter:null,pickedPin:null,page:5,zoom:1,focusBox:null,loading:false,sequence:0,controller:null,point:{},filter:{},fieldErrors:{},evaluation:null,activeCase:'reference',initial:true,saved:{}};
let recordsUI;
let presets=defaultPresets;
state.chipId='tps40200';state.switchSequence=0;state.switching=false;
state.pinPackage='ndh';
const chipDrafts=new Map();
const scoped=(path,chip=state.chipId)=>`${path}${path.includes('?')?'&':'?'}chip_id=${encodeURIComponent(chip)}`;
const matchLabels={applicable:'✓ 已提供条件符合',not_applicable:'! 条件不符',needs_information:'? 信息不足',not_evaluated:'范围限制／未筛选',invalid:'输入需要修改'};
const number = (value,digits=6) => value == null ? '—' : typeof value === 'number' ? new Intl.NumberFormat('zh-CN',{useGrouping:false,maximumFractionDigits:digits}).format(value) : value;
const result = () => state.payload?.result;
function cacheResult(){if(!state.request)return;const route=state.request.kind==='check'?'check':'manual';state.saved[route]=Object.fromEntries(['payload','request','selectedEvidence','selectedParameter','pickedPin','page','focusBox','scene','detail','activeCase','fieldErrors'].map(k=>[k,state[k]]));}
function restoreResult(route){const saved=state.saved[route];if(!saved)return false;Object.assign(state,saved);return true;}
const evidenceMap = () => new Map([...(state.payload?.evidence || []),...(state.payload?.related_evidence || [])].map(e=>[e.id,e]));
const evidence = () => evidenceMap().get(state.selectedEvidence);
let noticeTimer;

function notify(message, error=false) {
  const el=$('#notice');clearTimeout(noticeTimer);el.textContent=message;el.classList.toggle('error',error);el.hidden=false;
  noticeTimer=setTimeout(()=>{el.hidden=true;},error?7000:3200);
}

async function api(path, data, signal) {
  const response=await fetch(path,{method:data===undefined?'GET':'POST',headers:data===undefined?{}:{'Content-Type':'application/json'},body:data===undefined?undefined:JSON.stringify(data),signal});
  if(!response.ok){const body=await response.json().catch(()=>({error:'本地服务暂时无法响应。'}));throw new Error(body.error || `操作未完成（${response.status}）。`);}
  return response;
}
async function json(path,data,signal){return (await api(path,data,signal)).json();}

function routeData(){const [path,query='']=location.hash.replace(/^#\/?/,'').split('?');return {route:['manual','check','validation','records'].includes(path)?path:'manual',params:new URLSearchParams(query)};}
function updateURL(values,replace=true){const params=new URLSearchParams({chip:state.chipId});for(const [k,v] of Object.entries(values))if(v!=null && v!=='')params.set(k,v);const url=`#/${state.route}${params.size?'?'+params.toString():''}`;history[replace?'replaceState':'pushState'](null,'',url);}
function currentURL(){const p=routeData().params;return Object.fromEntries(p.entries());}
function selectDetail(detail,keepFocus=false){
  state.detail=detail;updateURL({...currentURL(),detail});renderInspector();
  $('#inspector-content').scrollTop=0;
  if(keepFocus)$(`#detail-${detail}`).focus();
}
function selectScene(scene){state.scene=scene;renderScene();updateURL({...currentURL(),view:scene});if(scene==='pdf')requestAnimationFrame(()=>focusRegion(state.focusBox || evidence()?.bbox));}

function updateChrome(){
  $$('.nav-item').forEach(a=>{if(a.dataset.route===state.route)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});
  const fullPage=['validation','records'].includes(state.route);
  $('#validation-page').hidden=state.route!=='validation';$('#records-page').hidden=state.route!=='records';$('#workspace').hidden=fullPage;$('#case-strip').hidden=fullPage;
  $('.app-shell').classList.toggle('validation-mode',fullPage);
  $('#query-form').hidden=state.route==='check';$('#check-heading').hidden=state.route!=='check';
  $('#export-toggle span').textContent=state.route==='validation'?'导出报告':state.route==='records'?'导出对比':'导出记录';
  $('#export-toggle').setAttribute('aria-label',$('#export-toggle span').textContent);
  $('#save-record').hidden=fullPage;
  $$('.case-button').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.case===state.activeCase)));
}
function renderScene(){
  $$('.scene-tabs button').forEach(b=>{const selected=b.dataset.scene===state.scene;b.setAttribute('aria-selected',String(selected));b.tabIndex=selected?0:-1;});
  $('#pdf-scene').hidden=state.scene!=='pdf';$('#pins-scene').hidden=state.scene!=='pins';$('#view-controls').hidden=state.scene!=='pdf';
  $('.source-panel').classList.toggle('linear-pin-view',state.scene==='pins' && state.chipId==='lm2596-adj');
  $('.page-controls').hidden=state.scene!=='pdf';
  if(state.scene==='pins')$('#selected-source-label').textContent=`${pinPackage()?.name ? pinPackage().name+' 顶视图' : state.boot.chip.package} · 引脚功能依据第 ${state.boot.chip.pins_page} 页`;
  else updateSourceStatus();
}

async function loadRequest(request,{activeCase=null,preserveScene=false,parameter=null,eid=null}={}){
  if(state.switching)return;request={...request,chip_id:state.chipId};
  const id=++state.sequence;state.controller?.abort();state.controller=new AbortController();state.loading=true;
  $('#inspector-content').setAttribute('aria-busy','true');
  const submit=$('#query-form button');submit.disabled=true;submit.setAttribute('aria-label','正在查找证据…');
  try{
    const payload=await json(request.kind==='check'?'/api/check':'/api/query',request.kind==='check'?{point:request.point,chip_id:state.chipId}:{question:request.question,conditions:request.conditions,chip_id:state.chipId},state.controller.signal);
    if(id!==state.sequence)return;
    state.payload=payload;state.request=structuredClone(request);state.activeCase=activeCase;state.fieldErrors={};
    if(request.kind==='query')state.filter=structuredClone(request.conditions||{});
    if(request.kind==='check')state.point={...state.point,...request.point};
    else $('#question').value=request.question;
    const preferred=eid || (payload.result.checks.some(c=>c.rule==='rc_tolerance_frequency')?'timing':payload.result.checks.some(c=>c.rule==='frequency')?'astable':payload.result.checks.some(c=>c.rule==='pulse_width')?'monostable':payload.result.checks.some(c=>c.rule==='divider_voltage')?'divider':null);
    state.selectedEvidence=preferred && evidenceMap().has(preferred)?preferred:payload.result.evidence_ids[0] || payload.result.hits[0]?.evidence_id || null;
    state.selectedParameter=parameter && payload.row_regions[parameter]?parameter:null;
    const applicable=payload.result.applicability?.filter(m=>m.status==='applicable')||[];
    if(!state.selectedParameter && request.conditions && applicable.length===1)state.selectedParameter=applicable[0].parameter_id;
    if(state.selectedParameter)state.selectedEvidence=payload.result.parameters.find(p=>p.id===state.selectedParameter)?.evidence_ids[0] || state.selectedEvidence;
    if(!preserveScene)state.scene='pdf';
    state.detail=state.route==='check' && payload.result.status==='invalid'?'conditions':'answer';
    if(payload.result.status==='invalid' && request.kind==='check')mapFieldErrors();
    const selected=evidence();state.page=selected?.page || 1;
    state.focusBox=state.selectedParameter?payload.row_regions[state.selectedParameter].bbox:selected?.bbox || null;
    renderInspector();$('#inspector-content').scrollTop=0;renderScene();updateChrome();loadPage(true);
    $('#result-announcement').textContent=`${payload.result.question}。${request.kind==='check'?'条件已逐项检查':labels[payload.result.status]}。`;
    cacheResult();
  }catch(error){if(error.name!=='AbortError'){notify(`操作未完成：${error.message} 当前仍显示上次已完成的结果。`,true);}}
  finally{if(id===state.sequence){state.loading=false;$('#inspector-content').setAttribute('aria-busy','false');submit.disabled=false;submit.setAttribute('aria-label','查找证据');const button=$('#point-submit');if(button){button.disabled=false;button.textContent='检查条件';}}}
}

function citationButtons(ids, selected=true){return ids.map(id=>{const e=evidenceMap().get(id);if(!e)return '';return `<button type="button" class="citation-button" data-evidence="${esc(id)}" aria-pressed="${selected && state.selectedEvidence===id}"><span class="citation-page">p.${e.printed_page}</span><span class="citation-title">${esc(e.title)}</span></button>`;}).join('');}
function parameterCards(parameters,conditionsOnly=false){return parameters.map(p=>{
  const match=result().applicability?.find(m=>m.parameter_id===p.id);
  return `<button type="button" class="parameter-card ${match?'match-'+match.status:''}" data-parameter="${esc(p.id)}" aria-pressed="${state.selectedParameter===p.id}" aria-label="定位 ${esc(p.symbol)}，${esc(p.conditions)} 的原文行"><div class="parameter-name"><strong translate="no">${esc(p.symbol)}</strong><span>${esc(ratingLabels[p.rating])}</span></div>${match?`<span class="match-badge ${esc(match.status)}">${esc(matchLabels[match.status])}</span>`:''}<p class="parameter-condition">${esc(p.conditions)}</p><dl class="parameter-values">${[['MIN',p.minimum],['TYP',p.typical],['MAX',p.maximum]].map(([label,value])=>`<div><dt>${label}</dt><dd${value==null?' aria-label="未给出"':''}>${esc(number(value))}${value==null?'':` ${esc(p.unit)}`}</dd></div>`).join('')}</dl>${match?`<ul class="match-reasons">${match.reasons.map(reason=>`<li>${esc(reason)}</li>`).join('')}</ul>`:''}<p class="small">${esc(p.name)}</p></button>`;
}).join('');}
function matchingCards(conditionsOnly=false){
  const matches=result().applicability||[],parameters=result().parameters;
  if(!matches.length)return parameterCards(parameters,conditionsOnly);
  const priority={applicable:0,invalid:1,needs_information:2,not_evaluated:3,not_applicable:4};
  const status=id=>matches.find(m=>m.parameter_id===id)?.status||'not_evaluated';
  const sorted=[...parameters].sort((a,b)=>priority[status(a.id)]-priority[status(b.id)]);
  const others=sorted.filter(p=>status(p.id)==='not_applicable'),visible=sorted.filter(p=>status(p.id)!=='not_applicable');
  return parameterCards(visible,conditionsOnly)+(others.length?`<details class="excluded-rows" ${!visible.length||others.some(p=>p.id===state.selectedParameter)?'open':''}><summary>条件不符的原始行（${others.length}）</summary>${parameterCards(others,conditionsOnly)}</details>`:'');
}
function filterSummary(){
  const matches=result().applicability||[];
  if(!matches.length)return '<p class="support-note">可按供电、温度和其他测试条件匹配参数行。</p><button class="button compact" type="button" data-open-filter>按条件筛选</button>';
  const counts={};for(const m of matches)counts[m.status]=(counts[m.status]||0)+1;
  return `<div class="filter-summary" role="status">${Object.entries(counts).map(([s,n])=>`<span class="match-badge ${esc(s)}">${esc(matchLabels[s])} ${n} 行</span>`).join('')}<p class="small">多个符合行分别保留，尚未确认的条件不会默认为满足。</p></div>`;
}
function filterForm(){
  if(state.chipId!=='tps40200')return `<form id="filter-form" class="filter-form"><h3>匹配当前型号的测试条件</h3><p class="form-caption">逐行核对原表条件；未提供的值或测试设置不会默认满足。TA 是环境温度，TJ 是结温。</p><div class="point-grid">${fieldsHTML(state.boot.capabilities.condition_fields,result().condition_errors||{},'filter')}</div><div class="filter-actions"><button type="submit" class="button primary">匹配条件</button><button type="button" class="button" data-filter-defaults>填入示例条件</button><button type="button" class="text-button" data-filter-clear>清除筛选</button></div></form>`;
  const errors=result().condition_errors||{};
  const input=(key,label,hint,wide=false)=>`<div class="field ${wide?'wide':''}"><label for="filter-${key}">${label}</label><input type="text" id="filter-${key}" name="${key}" placeholder="${hint}" autocomplete="off" spellcheck="false" aria-describedby="filter-error-${key}" ${errors[key]?'aria-invalid="true"':''}><span class="field-error" id="filter-error-${key}">${esc(errors[key]||'')}</span></div>`;
  const boolean=(key,label,yes,no)=>`<div class="field wide"><label for="filter-${key}">${label}</label><select id="filter-${key}" name="${key}"><option value="">尚未确认</option><option value="true">${yes}</option><option value="false">${no}</option></select></div>`;
  const advanced=['resistance','capacitance','load_capacitance','vfb','comp','comp_equals_fb','driver_switching'].some(k=>state.filter[k]!=null&&state.filter[k]!=='');
  return `<form id="filter-form" class="filter-form"><h3>匹配参数行的测试条件</h3><p class="form-caption">输入温度时明确它的含义。TA = TJ 是手册测试设置，不会把环境温度自动换成结温。</p><div class="point-grid">${input('vdd','输入电压 VDD','例如 12 V')}${input('temperature','温度','例如 25 °C')}<div class="field wide"><label for="filter-temperature-kind">温度类型</label><select id="filter-temperature-kind" name="temperature_kind"><option value="unknown">尚未确认温度类型</option><option value="test">手册测试温度（TA = TJ）</option><option value="ambient">仅环境温度 TA</option><option value="junction">仅结温 TJ</option></select></div>${input('frequency','振荡频率 fOSC','例如 100 kHz',true)}</div><details ${advanced?'open':''}><summary>更多测试条件</summary><div class="point-grid">${input('resistance','定时电阻 RRC','例如 200 kΩ')}${input('capacitance','定时电容 CRC','例如 470 pF')}${input('load_capacitance','负载电容 CL（不是 CRC）','例如 470 pF',true)}${input('vfb','VFB 测试电压','例如 0.6 V')}${input('comp','COMP 测试电压','例如 1 V')}${boolean('comp_equals_fb','COMP 与 FB 是否相连？','已确认相连','已确认未相连')}${boolean('driver_switching','驱动是否切换？','切换','不切换')}</div></details><div class="filter-actions"><button type="submit" class="button primary">匹配条件</button><button type="button" class="button" data-filter-defaults>填入示例条件</button><button type="button" class="text-button" data-filter-clear>清除筛选</button></div></form>`;
}
function toleranceSummary(){
  const c=result().checks.find(c=>c.rule==='rc_tolerance_frequency'&&c.status==='estimated');
  if(!c)return '';
  const nominal=result().checks.find(c=>c.rule==='rc_frequency')?.value;
  return `<section class="interval-summary"><h3>RC 元件容差区间</h3><dl><div><dt>估算下界</dt><dd>${esc(number(c.minimum,3))}<small> kHz</small></dd></div><div><dt>标称值</dt><dd>${esc(number(nominal,3))}<small> kHz</small></dd></div><div><dt>估算上界</dt><dd>${esc(number(c.maximum,3))}<small> kHz</small></dd></div></dl><p>${esc(c.message)}</p><button type="button" class="text-button" data-evidence="timing">核对公式原文</button></section>`;
}
function neTimingSummary(){
  if(state.chipId!=='ne555')return '';
  const rows=new Map(result().checks.map(c=>[c.rule,c]));
  const keys=rows.has('frequency')?['frequency','duty','period']:rows.has('pulse_width')?['pulse_width']:[];
  if(!keys.length)return '';
  return `<section class="interval-summary"><h3>${keys.length===3?'无稳态：频率与输出占空比':'单稳态：标称脉宽'}</h3><dl>${keys.map(key=>{const row=rows.get(key);return `<div><dt>${esc(row.title)}</dt><dd>${esc(number(row.value,3))}<small> ${esc(row.unit)}</small></dd></div>`;}).join('')}</dl>${keys.map(key=>{const range=rows.get('tolerance_'+key);return range?`<p>${esc(range.title)}：${esc(number(range.minimum,4))}–${esc(number(range.maximum,4))} ${esc(range.unit)}</p>`:'';}).join('')}<p>标称公式与元件容差端点估算，未包含器件自身误差。占空比指输出高电平所占比例。</p><button type="button" class="text-button" data-evidence="${keys.length===3?'astable':'monostable'}">核对公式与接线原文</button></section>`;
}
function ruleCards(checks){return checks.map(c=>`<section class="rule-card ${esc(c.status)}"><div class="rule-heading"><strong>${esc(c.title)}</strong><span>${c.status==='satisfied'?'✓ ':['invalid','violated'].includes(c.status)?'! ':''}${esc(ruleLabels[c.status])}</span></div><p>${esc(c.message)}</p>${c.evidence_ids[0]?`<button type="button" class="rule-evidence" data-evidence="${esc(c.evidence_ids[0])}">核对原文</button>`:''}</section>`).join('');}
function renderInspector(){
  const r=result();if(!r)return;
  $$('.inspector-tabs button').forEach(b=>{const selected=b.dataset.detail===state.detail;b.setAttribute('aria-selected',String(selected));b.tabIndex=selected?0:-1;});
  $('#inspector-content').setAttribute('aria-labelledby',`detail-${state.detail}`);
  let html='';
  if(state.pickedPin){const p=state.pickedPin;html+=`<section class="pin-note"><strong>${p.number} / <span translate="no">${esc(p.name)}</span></strong>${esc(p.description)}<div class="small">引脚说明依据手册第 ${state.boot.chip.pins_page} 页。</div><button class="text-button" type="button" data-followup="${esc(p.followup)}">继续查 ${esc(p.followup)}</button></section>`;}
  if(state.detail==='answer'){
    const isCheck=state.request?.kind==='check' || r.checks.length;
    html+=`<p class="result-question">${esc(r.question)}</p><div class="result-status">${icon(isCheck?'sliders':'check-file')}${isCheck?'逐项核对':esc(labels[r.status])}</div>`;
    if(isCheck){
      html+=`<p class="small">每项结论只针对该项限制；完整电路仍需进一步验证。</p>`;
      html+=toleranceSummary()+neTimingSummary();
      const visibleChecks=r.checks.filter(c=>c.status!=='needs_information' && !(c.rule==='rc_tolerance_frequency'&&c.status==='estimated'));
      if(state.chipId==='ne555' && r.checks.some(c=>['frequency','pulse_width'].includes(c.rule))){
        html+=ruleCards(visibleChecks.filter(c=>c.status!=='estimated'));
        html+=`<details><summary>时间、占空比与容差明细</summary>${ruleCards(visibleChecks.filter(c=>c.status==='estimated'))}</details>`;
      }else html+=ruleCards(visibleChecks);
      const missing=r.checks.filter(c=>c.status==='needs_information');
      if(missing.length)html+=`<details ${r.checks.every(c=>c.status==='needs_information')?'open':''}><summary>待补充信息（${missing.length} 项）</summary>${ruleCards(missing)}</details>`;
      html+=`<button type="button" class="button" data-edit-conditions>填写或修改条件</button>`;
      for(const note of r.notices)html+=`<p class="support-note">${esc(note)}</p>`;
    }else{
      html+=`<p class="answer-title">${esc(r.answer)}</p>`;
      if(r.parameters.length)html+=`${filterSummary()}<div class="section-title"><span>按测试条件逐行核对</span><small>点击可定位原文</small></div>${matchingCards()}`;
      for(const note of r.notices)html+=`<p class="support-note">${esc(note)}</p>`;
    }
    if(r.evidence_ids.length)html+=`<div class="section-title"><span>本次引用</span></div>${citationButtons(r.evidence_ids)}`;
    if(!r.evidence_ids.length)html+=`<p class="support-note">试试明确的参数符号，如 VFB、VUVLO(on)，或选择下方案例。</p>`;
  }else if(state.detail==='conditions'){
    if(state.route==='check')html+=pointForm();
    else{
      html+=`<h3>这些数值在什么条件下成立？</h3>`;
      if(r.parameters.length){html+=filterForm()+filterSummary()+matchingCards(true);const notes=[...new Set(r.parameters.flatMap(p=>p.notes))];html+=notes.map(n=>`<p class="support-note">${esc(n)}</p>`).join('');}
      else if(r.checks.length)html+=ruleCards(r.checks);
      else html+=`<p class="support-note">${esc(r.answer)}</p>`;
      html+=`<button type="button" class="button" data-edit-conditions>进入工作条件检查 ${icon('arrow-right')}</button>`;
    }
  }else{
    html+=`<h3>原文与出处</h3><p class="small">TI ${esc(r.source_revision)}。中文说明与英文原文分开展示。</p>${citationButtons(r.evidence_ids)}`;
    const e=evidence();
    if(e){html+=`<div class="section-title"><span>${esc(e.title)}</span></div><p class="small">PDF 物理页 ${e.page} / 印刷页 ${esc(e.printed_page)}</p>`;
      html+=`<div class="context-buttons"><button class="button compact" type="button" data-evidence="${esc(e.id)}">定位原文</button>${e.context_bboxes.map((_,i)=>`<button type="button" class="button compact" data-context="${i}">表头／脚注 ${i+1}</button>`).join('')}</div><blockquote class="source-block">${esc(e.text)}</blockquote>`;
      if(e.context)html+=`<details><summary>表头与脚注原文</summary><blockquote class="source-block">${esc(e.context)}</blockquote></details>`;
    }
    const extra=state.payload.related_evidence || [];
    if(extra.length)html+=`<details><summary>其他检索结果</summary><p class="small">检索得分只用于排序，不表示结论可信度。</p>${citationButtons(extra.map(e=>e.id),false)}</details>`;
    html+=`<a class="button" href="${scoped('/api/source.pdf')}" download>下载完整手册 ${icon('download')}</a>`;
  }
  $('#inspector-content').innerHTML=html;
  if(state.detail==='conditions' && state.route==='check'){
    for(const [field,value] of Object.entries(state.point)){const input=$(`[name="${field}"]`,$('#point-form'));if(input)input.value=value || '';}
    updateModeFields();
    const firstInvalid=$('[aria-invalid="true"]',$('#point-form'));if(firstInvalid)requestAnimationFrame(()=>firstInvalid.focus());
  }
  if($('#filter-form')){
    for(const [key,value] of Object.entries(state.filter)){const input=$(`[name="${key}"]`,$('#filter-form'));if(input)input.value=value==null?'':String(value);}
    const invalid=$('[aria-invalid="true"]',$('#filter-form'));if(invalid)requestAnimationFrame(()=>invalid.focus());
  }
}

function pointForm(){
  if(state.chipId!=='tps40200')return `<form class="point-form" id="point-form"><p class="form-caption">${esc(state.boot.capabilities.check_caption)} 请明确填写单位，空白表示尚未提供。</p><div class="point-grid">${fieldsHTML(state.boot.capabilities.check_fields,state.fieldErrors)}</div><button type="submit" class="button primary" id="point-submit">检查条件</button></form>`;
  const fields=[['vdd','12 V'],['tj','25 °C'],['frequency','100 kHz'],['resistance','200 kΩ'],['capacitance','470 pF']];
  const field=(key,placeholder,wide=false)=>`<div class="field ${wide?'wide':''}"><label for="point-${key}">${esc(fieldLabels[key])}</label><input id="point-${key}" name="${key}" type="text" placeholder="例如 ${placeholder}…" autocomplete="off" spellcheck="false" aria-describedby="error-${key}" ${state.fieldErrors[key]?'aria-invalid="true"':''}><span id="error-${key}" class="field-error" ${state.fieldErrors[key]?'role="alert"':''}>${esc(state.fieldErrors[key] || '')}</span></div>`;
  return `<form class="point-form" id="point-form"><p class="form-caption">请明确填写单位；空白表示尚未提供。环境温度不会自动转换成结温。</p><div class="point-grid">${fields.map(([key,hint])=>field(key,hint,key==='frequency')).join('')}</div><fieldset class="tolerance-fields"><legend>RC 容差分析（可选）</legend><div class="point-grid">${field('resistance_tolerance','1%')}${field('capacitance_tolerance','5%')}</div><p class="small">容差为 0% 至小于 100%；空白不会当作 0%。电流最不利值使用填写的固定 VDD，只考虑电阻、电容容差。</p></fieldset><details ${state.point.ambient_temperature?'open':''}><summary>只有环境温度？</summary>${field('ambient_temperature','25 °C')}</details><button type="submit" class="button primary" id="point-submit">检查条件</button></form>`;
}
function mapFieldErrors(){
  for(const c of result().checks.filter(c=>c.status==='invalid')){
    if(c.fields?.length){for(const field of c.fields)state.fieldErrors[field]=c.message;}
    else if(['vdd','tj','frequency'].includes(c.rule))state.fieldErrors[c.rule]=c.message;
    else if(c.message.includes('电阻'))state.fieldErrors.resistance=c.message;
    else if(c.message.includes('电容'))state.fieldErrors.capacitance=c.message;
    else for(const field of c.rule==='rc_current'?['vdd','resistance']:['resistance','capacitance'])if(state.point[field])state.fieldErrors[field]=c.message;
  }
}

function selectedRegion(){return state.selectedParameter ? state.payload?.row_regions[state.selectedParameter] : null;}
function drawRegions(){
  const e=evidence(),selected=selectedRegion();let markup='';
  const rect=(b,kind)=>`<rect class="${kind}" x="${b[0]}" y="${b[1]}" width="${b[2]-b[0]}" height="${b[3]-b[1]}"></rect>`;
  if(e && e.page===state.page){markup+=rect(e.bbox,'evidence-region');markup+=e.context_bboxes.map(b=>rect(b,'context-region')).join('');}
  if(selected && selected.page===state.page)markup+=rect(selected.bbox,'selected-region');
  $('#page-regions').innerHTML=markup;
}
function updateSourceStatus(){
  if(state.scene==='pins')return;
  const p=result()?.parameters.find(p=>p.id===state.selectedParameter),e=evidence();
  const text=p?`${p.symbol} · ${p.conditions}`:e?.page===state.page?e.title:`浏览手册第 ${state.page} 页${e?`（本次引用第 ${e.page} 页）`:''}`;
  $('#selected-source-label').textContent=text;$('#selected-source-label').setAttribute('title',text);$('#page-number').value=state.page;
  $('#page-prev').disabled=state.page<=1;$('#page-next').disabled=state.page>=state.boot.source.pages;
}
function pageSize(){return state.boot.page_sizes[state.page-1] || {width:612,height:792};}
function applyZoom(){const size=pageSize();$('#paper').style.width=`${size.width*state.zoom}px`;$('#paper').style.height=`${size.height*state.zoom}px`;$('#document-world').style.width=`${size.width*state.zoom+72}px`;$('#document-world').style.height=`${size.height*state.zoom+64}px`;$('#zoom-value').textContent=`${Math.round(state.zoom*100)}%`;}
function focusRegion(box){
  if(!box || state.scene!=='pdf')return;
  const viewport=$('#document-viewport');
  state.focusBox=box;state.zoom=Math.max(viewport.clientWidth<600?1.2:.55,Math.min(2.4,(viewport.clientWidth-68)/(box[2]-box[0])));applyZoom();
  viewport.scrollLeft=Math.max(0,36+(box[0]+box[2])/2*state.zoom-viewport.clientWidth/2);
  viewport.scrollTop=Math.max(0,32+(box[1]+box[3])/2*state.zoom-viewport.clientHeight/2);
}
function loadPage(focus=false){
  const image=$('#page-image'),size=pageSize();$('#page-regions').setAttribute('viewBox',`0 0 ${size.width} ${size.height}`);image.width=Math.round(size.width*2);image.height=Math.round(size.height*2);image.alt=`TI ${state.boot.chip.name} 手册第 ${state.page} 页原始页面，框线标明当前引用及相关上下文。`;
  const pageChip=state.chipId;const src=scoped(`/api/pages/${state.page}.png?v=${state.boot.source.sha256.slice(0,12)}`);
  const ready=()=>{if(state.chipId!==pageChip||image.getAttribute('src')!==src)return;drawRegions();updateSourceStatus();$('#document-loading').hidden=true;if(focus && evidence()?.page===state.page)focusRegion(state.focusBox || evidence().bbox);else applyZoom();};
  if(image.getAttribute('src')!==src){$('#document-loading').hidden=false;image.onload=ready;image.onerror=()=>{$('#document-loading').hidden=true;notify('原文页面载入失败。请核对资料版本，或重新启动工作台。',true);};image.src=src;}
  else requestAnimationFrame(ready);
}
function selectEvidence(id,parameter=null,box=null){
  const e=evidenceMap().get(id);if(!e)return;
  capturePoint();state.selectedEvidence=id;state.selectedParameter=parameter;state.page=e.page;state.focusBox=box || state.payload.row_regions[parameter]?.bbox || e.bbox;state.scene='pdf';
  updateURL({...currentURL(),e:id,row:parameter,view:'pdf'});renderInspector();renderScene();loadPage(true);
  const selected=parameter?$(`[data-parameter="${CSS.escape(parameter)}"]`):$(`[data-evidence="${CSS.escape(id)}"]`);selected?.focus({preventScroll:true});
}
function changePage(page){if(!Number.isInteger(page) || page<1 || page>state.boot.source.pages){notify(`页码应为 1–${state.boot.source.pages}。`,true);$('#page-number').value=state.page;return;}state.page=page;state.selectedParameter=null;state.focusBox=null;loadPage(false);const vp=$('#document-viewport');vp.scrollTop=0;vp.scrollLeft=0;}
function zoomBy(factor){const viewport=$('#document-viewport'),cx=(viewport.scrollLeft+viewport.clientWidth/2-36)/state.zoom,cy=(viewport.scrollTop+viewport.clientHeight/2-32)/state.zoom;state.zoom=Math.max(.5,Math.min(2.8,state.zoom*factor));applyZoom();viewport.scrollLeft=Math.max(0,36+cx*state.zoom-viewport.clientWidth/2);viewport.scrollTop=Math.max(0,32+cy*state.zoom-viewport.clientHeight/2);}
function fitPage(){const vp=$('#document-viewport');state.zoom=Math.max(.5,Math.min(2.4,(vp.clientWidth-72)/pageSize().width));applyZoom();vp.scrollTop=0;vp.scrollLeft=0;}

function pinPackage(){return state.boot.chip.packages?.find(p=>p.id===state.pinPackage) || state.boot.chip.packages?.[0];}
function renderLinearPackage(){
  const chip=state.boot.chip,pkg=pinPackage(),throughHole=pkg.id==='ndh';
  const pins=state.boot.pins.map(p=>{
    const x=150+(p.number-1)*50,selected=state.pickedPin?.number===p.number;
    return `<g class="package-lead ${selected?'selected':''}"><rect x="${x-8}" y="200" width="16" height="44" rx="2"/><text x="${x}" y="266" text-anchor="middle">${p.number}</text></g>`;
  }).join('');
  const metal=throughHole?'<rect class="package-metal" x="148" y="18" width="204" height="86" rx="5"/><circle class="package-hole" cx="250" cy="54" r="15"/>':'<path class="package-metal" d="M148 36H352V105H148Z"/>';
  return `<div class="package-picker" role="group" aria-label="封装类型"><span>封装</span>${chip.packages.map(p=>`<button type="button" data-pin-package="${esc(p.id)}" aria-pressed="${p.id===pkg.id}">${esc(p.name)}</button>`).join('')}</div>
    <div class="linear-package-figure"><svg class="package-drawing" viewBox="0 0 500 278" role="img" aria-label="${esc(chip.name)} ${esc(pkg.name)} 五引脚顶视图示意，1至5号从左向右，金属散热片或焊盘连接GND"><title>${esc(pkg.name)} 顶视图 · 引脚1在左</title>${metal}${pins}<rect class="package-body" x="132" y="91" width="236" height="112" rx="${throughHole?10:5}"/><circle class="package-index" cx="146" cy="188" r="4"/><text class="package-model" x="250" y="141" text-anchor="middle">${esc(chip.name)}</text><text class="package-name" x="250" y="172" text-anchor="middle">${esc(pkg.name)}</text></svg>
    <p class="package-orientation">顶视图 · 引脚 1 在左 · 金属散热片／焊盘接 GND</p></div>
    <div class="linear-pin-buttons">${state.boot.pins.map(p=>`<button class="package-pin" type="button" data-pin="${p.number}" aria-label="查看 ${p.number} 号 ${esc(p.name)} 引脚的功能与证据" aria-pressed="${state.pickedPin?.number===p.number}"><span>${p.number}</span><strong translate="no" title="${esc(p.name)}">${esc(p.name==='Feedback'?'FB':p.name)}</strong></button>`).join('')}</div>
    <div class="package-source"><p>功能示意，未按机械尺寸绘制；引脚方向与编号依据手册第 ${chip.pins_page} 页。</p><button class="text-button" type="button" data-pin-source>核对原文封装图</button></div>`;
}
function renderPins(){
  const chip=state.boot.chip;
  $('.diagram-heading p').textContent=chip.id==='lm2596-adj'?'五引脚封装功能示意 · 选择引脚查看对应参数':chip.package+' · 功能示意';
  $('.rc-diagram').hidden=chip.id!=='tps40200';
  $('#pin-package').classList.toggle('linear-pins',chip.id==='lm2596-adj');
  if(chip.id==='lm2596-adj'){$('#pin-package').innerHTML=renderLinearPackage();return;}
  const core=`<div class="chip-core"><span class="chip-notch" aria-hidden="true"></span><span class="chip-index" aria-hidden="true"></span><strong translate="no">${esc(chip.name)}</strong><span>${esc(chip.category)}</span></div>`;
  $('#pin-package').innerHTML=core+state.boot.pins.map(p=>`<button type="button" class="pin-button ${p.side}" data-pin="${p.number}" aria-label="查看 ${p.number} 号 ${esc(p.name)} 引脚的功能与证据" aria-pressed="${state.pickedPin?.number===p.number}">${p.side==='right'?'<span class="pin-wire" aria-hidden="true"></span>':''}<span class="pin-label">${p.number} / ${esc(p.name)}</span>${p.side==='left'?'<span class="pin-wire" aria-hidden="true"></span>':''}</button>`).join('');
}
async function choosePin(number){const pin=state.boot.pins.find(p=>p.number===number);if(!pin)return;state.pickedPin=pin;state.route='manual';state.scene='pins';updateURL({q:pin.question,view:'pins'});renderPins();$(`#pin-package [data-pin="${number}"]`).focus({preventScroll:true});updateChrome();await loadRequest({kind:'query',question:pin.question},{preserveScene:true});}

function captureFilter(){const form=$('#filter-form');if(!form)return;const values=Object.fromEntries(new FormData(form));for(const key of state.chipId==='tps40200'?['comp_equals_fb','driver_switching']:state.boot.capabilities.condition_fields.filter(f=>f.kind==='boolean').map(f=>f.name))values[key]=values[key]===''?null:values[key]==='true';state.filter=values;}
function capturePoint(){captureFilter();const form=$('#point-form');if(form){for(const [k,v] of new FormData(form).entries())state.point[k]=v;}}
async function applyFilter(clear=false){
  captureFilter();const question=state.request?.question||$('#question').value;
  const request={kind:'query',question};if(!clear)request.conditions=structuredClone(state.filter);else state.filter={};
  updateURL({q:question,detail:'conditions'},false);await loadRequest(request);selectDetail(Object.keys(result().condition_errors||{}).length?'conditions':'answer');
}
async function loadSaved(record,eid=null,replace=false){
  if(!record)return;
  const recordChip=record.chip_id||record.snapshot.result.chip_id||'tps40200';
  if(recordChip!==state.chipId)await activateChip(recordChip,{route:false});
  if(recordChip!==state.chipId)return;
  if(record.snapshot.source.sha256!==state.boot.source.sha256){notify('保存时的手册版本与当前不同。请在对比页查看旧快照，不能直接用当前手册重算。',true);return;}
  capturePoint();cacheResult();state.route=record.request.kind==='check'?'check':'manual';state.pickedPin=null;
  if(record.request.kind==='check')state.point=structuredClone(record.request.point);
  updateURL({record:record.id,e:eid},replace);updateChrome();await loadRequest(structuredClone(record.request),{eid});
  if(!replace)notify('已载入保存的输入并按当前规则重算，原记录快照保持不变。');
}
async function chooseCase(key){
  if(!presets[key]||state.switching)return;capturePoint();cacheResult();state.pickedPin=null;
  const request=structuredClone(presets[key]);state.route=request.kind==='check'?'check':'manual';
  if(request.kind==='check')state.point={...request.point};state.detail='answer';state.scene='pdf';
  updateURL({case:key},false);updateChrome();await loadRequest(request,{activeCase:key});
}
async function syncRoute(){
  if(!state.boot||state.switching)return;
  const requested=routeData().params.get('chip');if(requested&&requested!==state.chipId){await activateChip(requested,{preserveURL:true});return;}
  state.sequence++;state.controller?.abort();state.loading=false;$('#query-form button').disabled=false;$('#query-form button').setAttribute('aria-label','查找证据');$('#inspector-content').setAttribute('aria-busy','false');capturePoint();cacheResult();const {route,params}=routeData();state.route=route;if(!params.has('chip'))updateURL(Object.fromEntries(params.entries()),true);state.pickedPin=null;state.scene=params.get('view')==='pins'?'pins':'pdf';updateChrome();
  if(route==='validation'){await loadEvaluation();return;}
  if(route==='records'){await recordsUI.show();return;}
  if(params.get('record')){
    try{await loadSaved(await json(`/api/records/${encodeURIComponent(params.get('record'))}`),params.get('e'),true);}
    catch(e){notify(e.message,true);}
    if(['answer','conditions','source'].includes(params.get('detail')))selectDetail(params.get('detail'));
    return;
  }
  const key=params.get('case');
  if(key && presets[key]){await loadRequest(structuredClone(presets[key]),{activeCase:key,preserveScene:true,parameter:params.get('row'),eid:params.get('e') || (key==='timing'&&state.chipId==='tps40200'?'timing':null)});}
  else if(route==='check'){
    if(!restoreResult('check'))await loadRequest({kind:'check',point:{}},{preserveScene:true});
    state.detail='conditions';state.activeCase=null;renderInspector();renderScene();updateChrome();loadPage(true);
  }else{
    const q=params.get('q');
    if(q)await loadRequest({kind:'query',question:q},{preserveScene:true,parameter:params.get('row'),eid:params.get('e')});
    else{restoreResult('manual');if(params.has('view'))state.scene=params.get('view')==='pins'?'pins':'pdf';state.detail='answer';$('#question').value=state.request.question || '';renderInspector();renderScene();renderPins();updateChrome();loadPage(true);}
  }
  if(['answer','conditions','source'].includes(params.get('detail'))){state.detail=params.get('detail');renderInspector();}
}

function percent(value){return value==null?'—':new Intl.NumberFormat('zh-CN',{style:'percent',maximumFractionDigits:1}).format(value);}
async function loadEvaluation(){
  $('#validation-content').innerHTML='<p role="status">正在读取固定验证记录…</p>';
  try{const chip=state.chipId;const data=await json(scoped('/api/evaluation',chip));if(chip!==state.chipId)return;state.evaluation=data.report;renderEvaluation(data.report,data.boundaries);}catch(e){$('#validation-content').innerHTML=`<p class="support-note" role="alert">${esc(e.message)}</p>`;}
}
function renderEvaluation(report,boundaries=[]){
  if(!report){$('#validation-content').innerHTML='<p class="support-note">尚无验证记录，点击“重新运行验证”建立。</p>';return;}
  const m=report.metrics;
  let html=`<p class="report-summary">${m.passed} / ${m.cases} 个固定案例通过</p><p class="validation-note">自建固定验证集，开发组与留出组各 30 题。题目、参数整理和实现出自同一开发过程，尚非独立盲测。</p>`;
  html+=`<div class="report-table-wrap"><table class="report-table"><thead><tr><th scope="col">分组</th><th scope="col">案例通过</th><th scope="col">证据前三命中</th><th scope="col">原文基线</th><th scope="col">参数事实正确</th><th scope="col">参数回答覆盖</th></tr></thead><tbody>${Object.entries(report.splits).map(([group,x])=>`<tr><th scope="row">${group==='dev'?'开发组':'留出组'}</th><td>${x.passed}/${x.cases}</td><td>${percent(x.top3_recall)}</td><td>${percent(x.plain_top3_recall)}</td><td>${percent(x.fact_accuracy)}</td><td>${percent(x.fact_coverage)}</td></tr>`).join('')}</tbody></table></div>`;
  html+='<p class="validation-note">证据命中只统计有预标注证据的查询题；参数正确率与回答覆盖率同时报告。增强检索额外包含人工别名、结构化条件和中文说明，不能把差异单独归因于分块。</p>';
  html+=`<div class="baseline-section">${Object.entries(report.splits).map(([group,x])=>`<section><h3>${group==='dev'?'开发组':'留出组'} · 证据命中</h3>${[['增强检索',x.top3_recall,false],['原文 BM25',x.plain_top3_recall,true]].map(([label,value,baseline])=>`<div class="comparison-label"><span>${label}</span><span class="mono">${Math.round((value||0)*x.query_retrieval_cases)}/${x.query_retrieval_cases} · ${percent(value)}</span></div><progress class="comparison-meter ${baseline?'baseline':''}" max="100" value="${Math.max(0,Math.min(100,(value||0)*100))}" aria-label="${label} ${percent(value)}"></progress>`).join('')}</section>`).join('')}</div>`;
  html+='<h3>能力边界</h3><ul class="boundary-list"><li>无别名的中文表述可能只返回相关原文或无结果。</li><li>不同温度和供电条件分别列出，不自动合并为一个无条件保证值。</li><li>曲线读数与完整电路性能判断未纳入首版；RC 结果为标称估算。</li></ul>';
  if(boundaries.length)html+=`<details><summary>实际边界案例响应</summary><ul class="boundary-list">${boundaries.map(b=>`<li><strong>${esc(b.question)}</strong><p>${esc(b.answer)}</p></li>`).join('')}</ul></details>`;
  const failures=report.cases.filter(c=>!c.passed);
  html+=`<details><summary>查看全部 ${m.cases} 个案例${failures.length?`（${failures.length} 个未通过）`:''}</summary><div class="case-list"><table class="report-table"><thead><tr><th>编号</th><th>问题</th><th>结果</th></tr></thead><tbody>${report.cases.map(c=>`<tr><td>${esc(c.id)}</td><td>${esc(c.question)}</td><td>${c.passed?'通过':esc(c.errors.join('；'))}</td></tr>`).join('')}</tbody></table></div></details>`;
  if(report.benchmark_corrections?.length)html+=`<details><summary>首轮记录与验证数据修正</summary>${report.benchmark_corrections.map(c=>`<p class="validation-note">${esc(c.reason)}</p>`).join('')}</details>`;
  html+=`<a class="button report-download" href="/api/evaluation.md" download>下载完整报告 ${icon('download')}</a>`;
  $('#validation-content').innerHTML=html;
}

async function downloadResponse(response,fallback){const blob=await response.blob();const href=URL.createObjectURL(blob),a=document.createElement('a');a.href=href;a.download=fallback;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(href),1000);}
async function exportRecord(format){
  $('#export-menu').hidden=true;$('#export-toggle').setAttribute('aria-expanded','false');
  try{
    if(state.route==='records'){
      await recordsUI.exportComparison(format);return;
    }else if(state.route==='validation'){
      if(format==='md')await downloadResponse(await api(scoped('/api/evaluation.md')),`${state.chipId}-validation.md`);
      else{const data=await json(scoped('/api/evaluation'));const blob=new Blob([JSON.stringify(data.report,null,2)],{type:'application/json'});await downloadResponse(new Response(blob),`${state.chipId}-validation.json`);}
    }else{
      if(!state.request)throw new Error('请先完成一次查询或检查。');
      await downloadResponse(await api('/api/export',{...state.request,format}),`${state.chipId}-evidence.${format}`);
    }
    notify('导出已开始，记录中保留输入条件、原文出处与版本。');
  }catch(e){notify(e.message,true);}
}

function bindEvents(){
  $('#chip-select').addEventListener('change',event=>activateChip(event.target.value));
  $('#inspector-content').addEventListener('change',event=>{if(event.target.name==='mode'){capturePoint();updateModeFields();}});
  $('#query-form').addEventListener('submit',async event=>{event.preventDefault();state.pickedPin=null;state.route='manual';const q=$('#question').value;updateURL({q},false);await loadRequest({kind:'query',question:q});});
  $$('.case-button').forEach(b=>b.addEventListener('click',()=>chooseCase(b.dataset.case)));
  $$('.scene-tabs button').forEach(b=>b.addEventListener('click',()=>selectScene(b.dataset.scene)));
  $$('.inspector-tabs button').forEach(b=>b.addEventListener('click',()=>{capturePoint();selectDetail(b.dataset.detail);}));
  for(const selector of ['.scene-tabs','.inspector-tabs'])$(selector).addEventListener('keydown',event=>{if(!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;const tabs=$$('button',event.currentTarget),index=tabs.indexOf(document.activeElement);if(index<0)return;event.preventDefault();const i=event.key==='Home'?0:event.key==='End'?tabs.length-1:(index+(event.key==='ArrowRight'?1:-1)+tabs.length)%tabs.length;tabs[i].focus();tabs[i].click();});
  $('#inspector-content').addEventListener('click',async event=>{
    if(event.target.closest('[data-open-filter]')){captureFilter();selectDetail('conditions');return;}
    if(event.target.closest('[data-filter-defaults]')){captureFilter();state.filter=state.chipId==='tps40200'?{...state.filter,vdd:'12 V',temperature:'25 °C',temperature_kind:'test',frequency:'100 kHz'}:{...state.filter,...state.boot.capabilities.filter_example};renderInspector();notify('已填入示例条件，点击“匹配条件”查看适用行。');return;}
    if(event.target.closest('[data-filter-clear]')){await applyFilter(true);return;}
    const p=event.target.closest('[data-parameter]');if(p){const parameter=result().parameters.find(x=>x.id===p.dataset.parameter);selectEvidence(parameter.evidence_ids[0],parameter.id);return;}
    const e=event.target.closest('[data-evidence]');if(e){selectEvidence(e.dataset.evidence);return;}
    const c=event.target.closest('[data-context]');if(c){const box=evidence()?.context_bboxes[Number(c.dataset.context)];if(box)selectEvidence(state.selectedEvidence,null,box);return;}
    const edit=event.target.closest('[data-edit-conditions]');if(edit){capturePoint();cacheResult();state.route='check';state.point={...state.point,...result().inputs};state.pickedPin=null;updateURL({},false);updateChrome();await loadRequest({kind:'check',point:{...state.point}});selectDetail('conditions');return;}
    const f=event.target.closest('[data-followup]');if(f){state.pickedPin=null;state.route='manual';updateURL({q:f.dataset.followup});loadRequest({kind:'query',question:f.dataset.followup});}
  });
  $('#inspector-content').addEventListener('submit',async event=>{if(event.target.id==='filter-form'){event.preventDefault();await applyFilter();return;}if(event.target.id!=='point-form')return;event.preventDefault();capturePoint();updateURL({},false);$('#point-submit').disabled=true;$('#point-submit').textContent='正在检查…';await loadRequest({kind:'check',point:{...state.point}});updateURL({detail:state.detail});});
  $('#save-record').addEventListener('click',()=>recordsUI.openSave());
  $('#pin-package').addEventListener('click',event=>{
    const pkg=event.target.closest('[data-pin-package]');if(pkg){state.pinPackage=pkg.dataset.pinPackage;renderPins();renderScene();$(`[data-pin-package="${CSS.escape(state.pinPackage)}"]`).focus();return;}
    if(event.target.closest('[data-pin-source]')){state.pickedPin=null;state.route='manual';updateURL({q:'引脚功能'});loadRequest({kind:'query',question:'引脚功能'});return;}
    const b=event.target.closest('[data-pin]');if(b)choosePin(Number(b.dataset.pin));
  });
  $('#diagram-check').addEventListener('click',()=>chooseCase('timing'));
  $('#zoom-in').addEventListener('click',()=>zoomBy(1.2));$('#zoom-out').addEventListener('click',()=>zoomBy(1/1.2));$('#fit-page').addEventListener('click',fitPage);$('#locate-evidence').addEventListener('click',()=>{if(evidence()){state.page=evidence().page;loadPage(true);}else fitPage();});
  $('#page-prev').addEventListener('click',()=>changePage(state.page-1));$('#page-next').addEventListener('click',()=>changePage(state.page+1));$('#page-number').addEventListener('change',event=>changePage(Number(event.target.value)));
  const viewport=$('#document-viewport');let drag=null;
  viewport.addEventListener('pointerdown',event=>{if(event.button!==0 || event.pointerType!=='mouse')return;drag={x:event.clientX,y:event.clientY,left:viewport.scrollLeft,top:viewport.scrollTop};viewport.setPointerCapture(event.pointerId);viewport.classList.add('dragging');});
  viewport.addEventListener('pointermove',event=>{if(!drag)return;viewport.scrollLeft=drag.left-(event.clientX-drag.x);viewport.scrollTop=drag.top-(event.clientY-drag.y);});
  const stopDrag=()=>{drag=null;viewport.classList.remove('dragging');};viewport.addEventListener('pointerup',stopDrag);viewport.addEventListener('pointercancel',stopDrag);
  viewport.addEventListener('keydown',event=>{if(event.ctrlKey || event.metaKey || event.altKey)return;if(['+','='].includes(event.key)){event.preventDefault();zoomBy(1.2);}else if(event.key==='-'){event.preventDefault();zoomBy(1/1.2);}else if(event.key==='0'){event.preventDefault();focusRegion(state.focusBox || evidence()?.bbox);}});
  let resize;window.addEventListener('resize',()=>{clearTimeout(resize);resize=setTimeout(()=>{if(state.scene==='pdf')focusRegion(state.focusBox || evidence()?.bbox);},150);});
  $('#export-toggle').addEventListener('click',()=>{const menu=$('#export-menu');menu.hidden=!menu.hidden;$('#export-toggle').setAttribute('aria-expanded',String(!menu.hidden));if(!menu.hidden)$('button',menu).focus();});
  $$('#export-menu button').forEach(b=>b.addEventListener('click',()=>exportRecord(b.dataset.export)));
  document.addEventListener('click',e=>{if(!e.target.closest('.export-wrap')){$('#export-menu').hidden=true;$('#export-toggle').setAttribute('aria-expanded','false');}});
  document.addEventListener('keydown',e=>{if(e.key==='Escape' && !$('#export-menu').hidden){$('#export-menu').hidden=true;$('#export-toggle').setAttribute('aria-expanded','false');$('#export-toggle').focus();}});
  $('#about-open').addEventListener('click',()=>$('#source-dialog').showModal());$('#about-close').addEventListener('click',()=>$('#source-dialog').close());$('#source-dialog').addEventListener('click',e=>{if(e.target===$('#source-dialog'))$('#source-dialog').close();});
  $('#run-evaluation').addEventListener('click',async()=>{const b=$('#run-evaluation');b.disabled=true;b.textContent='正在运行验证…';try{const chip=state.chipId;const data=await json('/api/evaluate',{chip_id:chip});if(chip!==state.chipId)return;state.evaluation=data.report;renderEvaluation(data.report);notify(`验证完成：${data.report.metrics.passed}/${data.report.metrics.cases} 个固定案例通过。`);}catch(e){notify(e.message,true);}finally{b.disabled=false;b.textContent='重新运行验证';}});
  window.addEventListener('hashchange',syncRoute);
}

function configureChip(){
  const b=state.boot,m=b.source,chip=b.chip;
  $$('.nav-item').forEach(link=>link.href=`#/${link.dataset.route}?chip=${encodeURIComponent(chip.id)}`);
  document.title=`${chip.name} · 芯片手册证据工作台`;
  $('#chip-select').innerHTML=b.chips.map(c=>`<option value="${esc(c.id)}" ${c.id===chip.id?'selected':''}>TI ${esc(c.name)}</option>`).join('');
  $('#chip-revision').textContent=m.revision;$('.local-label .revision').textContent='/ '+m.revision;
  $('#app-version').textContent=`v${b.version}`;$('#page-number').max=m.pages;$('#page-total').textContent=`/ ${m.pages} 页`;
  $('#question').placeholder=`例如 ${b.initial.result.question}`;
  presets=chip.id==='tps40200'?defaultPresets:Object.fromEntries(b.capabilities.cases.map(c=>[c.id,c.request]));
  const cases=b.capabilities.cases;
  if(!state.defaultCaseLabels)state.defaultCaseLabels=$$('.case-button').map(button=>[button.querySelector('strong').textContent,button.querySelector('small').textContent]);
  $$('.case-button').forEach((button,i)=>{button.querySelector('strong').textContent=cases?cases[i].title:state.defaultCaseLabels[i][0];button.querySelector('small').textContent=cases?cases[i].subtitle:state.defaultCaseLabels[i][1];});
  const downloaded=new Intl.DateTimeFormat('zh-CN',{dateStyle:'medium',timeStyle:'short'}).format(new Date(m.downloaded_at));
  $('#source-dialog-body').innerHTML=`<p><strong>TI ${esc(chip.name)}</strong></p><dl><dt>手册版本</dt><dd>${esc(m.revision)} · ${esc(m.revision_date)}</dd><dt>固定文件</dt><dd>${m.pages} 页；${b.parameter_rows} 行参数；${b.reviewed_evidence_groups} 组整理证据</dd><dt>下载时间</dt><dd>${esc(downloaded)}</dd><dt>SHA-256</dt><dd class="hash">${esc(m.sha256)}</dd></dl><p>查询、计算和导出均在本机完成。参数由 Codex 对照固定原图整理，尚无独立第三方复核。更换手册后需重新复核。</p><p>只有明确适用于当前型号的参数进入答案；其他型号专属行不转用。尚未明确的测试设置需要对照原文。</p><a class="button" href="${scoped('/api/source.pdf')}" download>下载固定手册 ${icon('download')}</a>`;
  renderPins();
}
async function activateChip(chip,{route=true,preserveURL=false}={}){
  const token=++state.switchSequence;state.sequence++;state.controller?.abort();state.chipController?.abort();state.chipController=new AbortController();
  if(state.boot){capturePoint();cacheResult();chipDrafts.set(state.chipId,structuredClone(Object.fromEntries(['payload','request','point','filter','saved','scene','detail','activeCase','selectedEvidence','selectedParameter','page','focusBox','zoom','fieldErrors'].map(k=>[k,state[k]]))));chipDrafts.get(state.chipId).questionDraft=$('#question').value;}
  state.switching=true;$('#workspace').inert=true;$('#save-record').disabled=true;
  try{
    const next=await json(scoped('/api/bootstrap',chip),undefined,state.chipController.signal);if(token!==state.switchSequence)return;
    state.chipId=chip;state.boot=next;state.pickedPin=null;state.evaluation=null;
    const cached=chipDrafts.get(chip);
    Object.assign(state,cached||{payload:next.initial,request:{kind:'query',question:next.initial.result.question,chip_id:chip},point:{},filter:{},saved:{},scene:'pdf',detail:'answer',activeCase:'reference',selectedParameter:null,fieldErrors:{},zoom:1});
    state.selectedEvidence=state.payload.result.evidence_ids[0]||state.payload.result.hits[0]?.evidence_id||null;
    const e=evidence();state.page=e?.page||1;state.focusBox=e?.bbox||null;
    $('#question').value=cached?.questionDraft??state.request.question??'';
    $('#inspector-content').innerHTML='';configureChip();state.switching=false;$('#workspace').inert=false;$('#save-record').disabled=false;
    const requestedRoute=routeData().route;state.route=requestedRoute;if(!preserveURL)updateURL({},true);renderInspector();renderScene();updateChrome();loadPage(true);
    if(route)await syncRoute();
    if(cached?.questionDraft!=null&&state.route==='manual')$('#question').value=cached.questionDraft;
    notify(`已切换到 TI ${next.chip.name}，使用 ${next.source.revision}。`);
  }catch(error){if(error.name!=='AbortError'){notify(error.message,true);$('#chip-select').value=state.chipId;}}
  finally{if(token===state.switchSequence){state.switching=false;$('#workspace').inert=false;$('#save-record').disabled=false;}}
}
async function boot(){
  try{
    const chip=routeData().params.get('chip')||'tps40200';state.chipId=chip;
    state.boot=await json(scoped('/api/bootstrap',chip));state.payload=state.boot.initial;state.request={kind:'query',question:state.payload.result.question,chip_id:chip};
    state.selectedEvidence=state.payload.result.evidence_ids[0];state.page=evidence().page;state.focusBox=evidence().bbox;
    $('#question').value=result().question;configureChip();
    recordsUI=setupRecords({json,api,download:downloadResponse,notify,load:loadSaved,getRequest:()=>state.request,sourceHash:()=>state.boot.source.sha256,getChip:()=>state.chipId,chips:state.boot.chips});
    $('#startup-message').hidden=true;$('#workspace').hidden=false;bindEvents();await syncRoute();
  }catch(e){$('#startup-message').classList.add('error');$('#startup-message').innerHTML=`<h2>本地资料暂不可用</h2><p>${esc(e.message)}</p><p>请重新启动工作台；如手册已替换，需要恢复固定版本或重新复核导入。</p><button type="button" class="button" id="retry-startup">重新读取</button>`;$('#retry-startup').addEventListener('click',()=>location.reload());}
}
boot();
