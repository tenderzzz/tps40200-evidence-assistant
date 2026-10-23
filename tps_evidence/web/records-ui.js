const $ = s=>document.querySelector(s);
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const statuses={applicable:'已提供条件符合',not_applicable:'条件不符',needs_information:'信息不足',not_evaluated:'范围限制／未筛选',invalid:'输入无效',satisfied:'满足该项',violated:'不满足该项',estimated:'估算'};
const value=v=>v==null || v===''?'未提供':v===true?'是':v===false?'否':({astable:'无稳态',monostable:'单稳态',low:'低电平',high:'高电平',test:'手册测试温度 TA = TJ',ambient:'仅环境温度 TA',junction:'仅结温 TJ',unknown:'尚未确认温度类型'}[v]||String(v));
const date=v=>new Intl.DateTimeFormat('zh-CN',{dateStyle:'short',timeStyle:'short'}).format(new Date(v));

export function setupRecords({json,api,download,notify,load,getRequest,sourceHash,getChip,chips}){
  const state={items:[],a:null,b:null,comparison:null,onlyChanges:false,sequence:0,filter:getChip(),activeChip:getChip()};
  const name=chip=>chips.find(c=>c.id===chip)?.name||chip;
  const fieldLabel=(chip,key)=>chips.find(c=>c.id===chip)?.input_labels?.[key]||key;
  const chipOf=r=>r.chip_id||r.snapshot.result.chip_id||'tps40200';
  const visible=()=>state.items.filter(r=>state.filter==='all'||chipOf(r)===state.filter);
  const byId=id=>state.items.find(r=>r.id===id);
  const badge=status=>`<span class="match-badge ${esc(status)}">${esc(statuses[status]||status||'未筛选')}</span>`;
  function evidence(record){
    return `<details class="record-evidence"><summary>${esc(record.name)}：保存时的原文与出处</summary><p class="small">${esc(record.snapshot.source.revision)}<br><span class="hash">SHA-256 ${esc(record.snapshot.source.sha256)}</span></p>${record.snapshot.evidence.map(e=>`<section><h4>${esc(e.title)} · p.${esc(e.printed_page)}</h4><button type="button" class="text-button" data-record-load="${record.id}" data-eid="${esc(e.id)}">载入并定位原文</button><blockquote class="source-block">${esc(e.text)}</blockquote>${e.context?`<details><summary>表头与脚注</summary><blockquote class="source-block">${esc(e.context)}</blockquote></details>`:''}</section>`).join('')}</details>`;
  }
  function comparisonView(){
    const c=state.comparison;
    if(!c)return '<div class="record-empty"><h3>保留调参前后的依据</h3><p>保存两个方案后，选择 A 与 B，比较输入、逐项检查和参数行适用性的变化。</p></div>';
    if(c.same_chip===false)return `<h3>不同型号的原始记录</h3><p class="support-note">${esc(c.notice)}</p><div class="cross-snapshots">${['a','b'].map(side=>{const snap=c['snapshot_'+side],r=snap.result;return `<section><h4>${side.toUpperCase()} · TI ${esc(name(c[side].chip_id))} · ${esc(c[side].name)}</h4><p>${esc(r.answer)}</p><dl>${Object.entries(r.condition_inputs||{}).concat(Object.entries(r.inputs||{})).map(([k,v])=>`<dt>${esc(fieldLabel(c[side].chip_id,k))}</dt><dd>${esc(value(v))}</dd>`).join('')}</dl>${r.parameters.map(p=>`<p><strong>${esc(p.symbol)}</strong> MIN ${esc(p.minimum??'—')} / TYP ${esc(p.typical??'—')} / MAX ${esc(p.maximum??'—')} ${esc(p.unit)}<br>${esc(p.conditions)}</p>`).join('')}${evidence(byId(c[side].id))}</section>`;}).join('')}</div>`;
    const inputs=c.inputs.filter(r=>!state.onlyChanges||r.changed||r.representation_changed);
    const checks=c.checks.filter(r=>!state.onlyChanges||r.changed);
    const parameters=c.parameters.filter(r=>!state.onlyChanges||r.changed);
    const cellCheck=r=>r?`${badge(r.status)}<p>${esc(r.message)}</p>`:'<span class="small">无此项</span>';
    const cellParameter=(p,m)=>p?`${badge(m?.status)}<p class="mono">MIN ${esc(p.minimum??'—')} / TYP ${esc(p.typical??'—')} / MAX ${esc(p.maximum??'—')} ${esc(p.unit)}</p>${m?`<p>${esc(m.reasons.join('；'))}</p>`:''}`:'<span class="small">无此行</span>';
    let html=`<div class="comparison-heading"><h3>${esc(c.a.name)} <span class="small">与</span> ${esc(c.b.name)}</h3><label class="change-toggle"><input type="checkbox" id="only-changes" ${state.onlyChanges?'checked':''}>只看变化</label></div><p class="small">${esc(c.notice)}</p>`;
    if(!c.same_source)html+='<p class="support-note">两条记录的手册哈希不同，请分别核对来源；不会把它们当成同一版本。</p>';
    if(!c.same_kind)html+='<p class="support-note">记录类型不同，下方分别列出各自有的输入与项目，不作整体优劣排序。</p>';
    html+=`<h4>输入条件</h4><div class="report-table-wrap"><table class="diff-table"><thead><tr><th scope="col">项目</th><th scope="col">A</th><th scope="col">B</th><th scope="col">变化</th></tr></thead><tbody>${inputs.map(r=>`<tr class="${r.changed?'changed':''}"><th scope="row">${esc(r.label)}</th><td>${esc(value(r.a))}</td><td>${esc(value(r.b))}</td><td>${r.changed?'已改变':r.representation_changed?'数值相同，写法不同':'相同'}</td></tr>`).join('')||'<tr><td colspan="4">没有符合筛选的输入。</td></tr>'}</tbody></table></div>`;
    if(c.checks.length)html+=`<h4>逐项检查</h4><div class="report-table-wrap"><table class="diff-table result-diff"><thead><tr><th scope="col">检查项目</th><th scope="col">A</th><th scope="col">B</th></tr></thead><tbody>${checks.map(r=>`<tr class="${r.changed?'changed':''}"><th scope="row">${esc(r.title)}${r.changed?'<span class="change-label">有变化</span>':''}</th><td>${cellCheck(r.a)}</td><td>${cellCheck(r.b)}</td></tr>`).join('')||'<tr><td colspan="3">没有变化的检查项。</td></tr>'}</tbody></table></div>`;
    if(c.parameters.length)html+=`<h4>参数行与适用条件</h4><div class="report-table-wrap"><table class="diff-table result-diff"><thead><tr><th scope="col">参数行</th><th scope="col">A</th><th scope="col">B</th></tr></thead><tbody>${parameters.map(r=>`<tr class="${r.changed?'changed':''}"><th scope="row">${esc(r.symbol)}<p class="small">${esc(r.conditions)}</p>${r.changed?'<span class="change-label">有变化</span>':''}</th><td>${cellParameter(r.a,r.match_a)}</td><td>${cellParameter(r.b,r.match_b)}</td></tr>`).join('')||'<tr><td colspan="3">没有变化的参数行。</td></tr>'}</tbody></table></div>`;
    html+=evidence(byId(c.a.id))+evidence(byId(c.b.id));
    return html;
  }
  function render(){
    const items=visible();
    const options=selected=>items.map(r=>`<option value="${r.id}" ${r.id===selected?'selected':''}>${esc(name(chipOf(r)))} · ${esc(r.name)} · ${esc(date(r.created_at))}</option>`).join('');
    $('#records-content').innerHTML=`<div class="records-toolbar"><div class="field"><label for="record-chip-filter">记录芯片</label><select id="record-chip-filter"><option value="all" ${state.filter==='all'?'selected':''}>全部芯片</option>${chips.map(chip=>`<option value="${esc(chip.id)}" ${state.filter===chip.id?'selected':''}>TI ${esc(chip.name)}</option>`).join('')}</select></div><div class="field"><label for="compare-a">方案 A</label><select id="compare-a" ${items.length<2?'disabled':''}>${options(state.a)}</select></div><div class="field"><label for="compare-b">方案 B</label><select id="compare-b" ${items.length<2?'disabled':''}>${options(state.b)}</select></div><button class="button primary" type="button" id="compare-run" ${items.length<2?'disabled':''}>比较方案</button><a class="button" href="/api/records/export" download>备份全部记录</a></div><div class="records-layout"><aside class="record-list" aria-label="已保存的方案"><h3>已保存 ${items.length} 条</h3>${items.map(r=>`<article class="record-item"><h4>${esc(r.name)}</h4><p class="small">TI ${esc(name(chipOf(r)))} · ${esc(date(r.created_at))} · ${r.request.kind==='check'?'条件检查':'参数查询'}</p><p>${esc(r.snapshot.result.question)}</p><button type="button" class="button compact" data-record-load="${r.id}" aria-label="载入 ${esc(r.name)}">载入工作台</button><details><summary>保存时的输入与结论</summary><p>${esc(r.snapshot.result.answer)}</p><dl>${Object.entries(r.request.point||r.request.conditions||{}).map(([k,v])=>`<div><dt>${esc(fieldLabel(chipOf(r),k))}</dt><dd>${esc(value(v))}</dd></div>`).join('')}</dl><p class="small">${esc(r.snapshot.source.revision)}<br><span class="hash">${esc(r.snapshot.source.sha256)}</span></p></details></article>`).join('')||'<p class="small">在查询或检查完成后，点击顶部“保存方案”。记录保存在本机应用数据目录，关闭网页或换端口后仍可读取。</p>'}</aside><section class="comparison-content" aria-label="方案对比">${comparisonView()}</section></div>`;
  }
  async function compareNow(){
    const items=visible();if(items.length<2)return;
    const id=++state.sequence;
    const button=$('#compare-run');if(button){button.disabled=true;button.textContent='正在比较…';}
    try{const c=await json('/api/records/compare',{a:state.a,b:state.b});if(id===state.sequence){state.comparison=c;render();}}
    catch(e){notify(e.message,true);if(button){button.disabled=false;button.textContent='比较方案';}}
  }
  async function show(){
    const sequence=++state.sequence;
    if(state.activeChip!==getChip()){state.filter=getChip();state.activeChip=getChip();}
    $('#records-content').innerHTML='<p role="status">正在读取本机记录…</p>';
    try{
      const {records}=await json('/api/records');if(sequence!==state.sequence)return;state.items=records;const items=visible();
      state.a=items.some(r=>r.id===state.a)?state.a:(items[1]||items[0])?.id;
      state.b=items.some(r=>r.id===state.b)?state.b:items[0]?.id;
      state.comparison=null;render();if(items.length>=2)await compareNow();
    }catch(e){$('#records-content').innerHTML=`<p role="alert">${esc(e.message)}</p><button type="button" class="button" id="records-retry">重新读取</button>`;}
  }
  async function exportComparison(format){
    if(!state.comparison){notify('请先保存并选择两个方案进行比较。',true);return;}
    if(format==='md')await download(await api('/api/records/compare',{a:state.a,b:state.b,format:'md'}),'tps40200-comparison.md');
    else await download(new Response(JSON.stringify(state.comparison,null,2),{headers:{'Content-Type':'application/json'}}),'tps40200-comparison.json');
    notify('对比文件已开始导出，保留两份快照、条件与原文出处。');
  }
  function openSave(){
    const request=getRequest();if(!request){notify('请先完成一次查询或检查。',true);return;}
    const p=request.point||request.conditions||{};
    $('#record-name').value=(request.kind==='check'?(p.resistance||p.capacitance?`RC ${p.resistance||''} ${p.capacitance||''} ${p.resistance_tolerance||''}/${p.capacitance_tolerance||''}`:`条件检查 ${p.vdd||''} ${p.tj||''}`):`${request.question}${p.temperature?' · '+p.temperature:''}`).trim().slice(0,45);
    $('#record-name').value=(name(request.chip_id||'tps40200')+' · '+$('#record-name').value).slice(0,60);
    $('#record-save-error').textContent='';$('#record-save-dialog').showModal();$('#record-name').focus();$('#record-name').select();
  }
  $('#record-save-form').addEventListener('submit',async e=>{
    e.preventDefault();const button=$('#record-save-submit');button.disabled=true;button.textContent='正在保存…';
    try{
      const record=await json('/api/records',{name:$('#record-name').value,request:getRequest()});
      $('#record-save-dialog').close();notify(`已保存“${record.name}”。可在方案记录中载入和比较。`);
    }catch(error){$('#record-save-error').textContent=error.message;$('#record-name').focus();}
    finally{button.disabled=false;button.textContent='保存到本机';}
  });
  $('#record-save-close').addEventListener('click',()=>$('#record-save-dialog').close());
  $('#records-refresh').addEventListener('click',show);
  $('#records-content').addEventListener('click',async e=>{
    const b=e.target.closest('[data-record-load]');if(b){await load(byId(b.dataset.recordLoad),b.dataset.eid);return;}
    if(e.target.closest('#compare-run'))await compareNow();
    if(e.target.closest('#records-retry'))await show();
  });
  $('#records-content').addEventListener('change',e=>{
    if(e.target.id==='record-chip-filter'){state.filter=e.target.value;const items=visible();state.a=(items[1]||items[0])?.id;state.b=items[0]?.id;state.comparison=null;render();compareNow();return;}
    if(e.target.id==='compare-a')state.a=e.target.value;
    if(e.target.id==='compare-b')state.b=e.target.value;
    if(['compare-a','compare-b'].includes(e.target.id)){state.comparison=null;compareNow();}
    if(e.target.id==='only-changes'){state.onlyChanges=e.target.checked;$('.comparison-content').innerHTML=comparisonView();$('#only-changes').focus();}
  });
  return {show,openSave,exportComparison};
}
