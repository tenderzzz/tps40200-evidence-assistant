const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export function fieldsHTML(fields,errors={},prefix='point'){
  return fields.map(f=>{
    const id=`${prefix}-${f.name}`,error=errors[f.name];let control;
    if(f.kind==='boolean')control=`<select id="${id}" name="${f.name}"><option value="">尚未确认</option><option value="true">已确认：是</option><option value="false">已确认：否</option></select>`;
    else if(f.choices)control=`<select id="${id}" name="${f.name}" ${error?'aria-invalid="true"':''}><option value="">请选择</option>${f.choices.map(c=>`<option value="${esc(c.value)}">${esc(c.label)}</option>`).join('')}</select>`;
    else control=`<input type="text" id="${id}" name="${f.name}" placeholder="例如 ${esc(f.hint)}" autocomplete="off" spellcheck="false" aria-describedby="${id}-error" ${error?'aria-invalid="true"':''}>`;
    return `<div class="field ${f.choices||f.kind==='boolean'?'wide':''}" data-field="${f.name}"><label for="${id}">${esc(f.label)}</label>${control}<span id="${id}-error" class="field-error">${esc(error||'')}</span></div>`;
  }).join('');
}
export function updateModeFields(){
  const form=document.querySelector('#point-form');if(!form?.querySelector('[name="mode"]'))return;
  const mono=form.elements.mode.value==='monostable';
  for(const key of ['rb','rb_tolerance']){const f=form.querySelector(`[data-field="${key}"]`);if(f){f.hidden=mono;f.querySelector('input').disabled=mono;}}
}
