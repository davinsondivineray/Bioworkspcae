function jsonForm(form) {
  const data = new FormData(form);
  const result = {};
  for (const [key, value] of data.entries()) {
    if (key.endsWith('_ids')) {
      result[key] ||= [];
      result[key].push(Number(value));
    } else if (key === 'answer_index') result[key] = Number(value);
    else if (key === 'options_text') result.options = String(value).split('\n').map(x => x.trim()).filter(Boolean);
    else result[key] = value;
  }
  if ('options' in result && result.answer_index) result.answer_index -= 1;
  return result;
}

function showMessage(form, message, isError = false) {
  const node = form.querySelector('.form-message');
  if (node) {
    node.textContent = message;
    node.style.color = isError ? '#a53931' : '#16745b';
  }
}

document.querySelectorAll('form[data-api]').forEach(form => {
  form.addEventListener('submit', async event => {
    event.preventDefault();
    const button = form.querySelector('button[type="submit"]') || form.querySelector('button');
    if (button) button.disabled = true;
    try {
      const isUpload = form.hasAttribute('data-upload');
      let body;
      if (isUpload) {
        body = new FormData(form);
        const extra = form.dataset.extra;
        if (extra) {
          const [key, value] = extra.split(':');
          body.set(key, value);
        }
      } else if (form.hasAttribute('data-conversation-create')) {
        body = jsonForm(form);
        body.kind = 'study';
      } else if (form.hasAttribute('data-ai-lab')) {
        body = {kind:'lab', case_id:Number(form.dataset.aiLab)};
      } else if (form.querySelector('[name="interests"]')) {
        body = jsonForm(form);
        body.interests = [...form.querySelectorAll('[name="interests"]:checked')].map(x => x.value);
      } else {
        body = jsonForm(form);
        if (body.options_text !== undefined) delete body.options_text;
        if ('observed_at' in body && !body.observed_at) body.observed_at = null;
      }
      const response = await fetch(form.dataset.api, {
        method: form.dataset.method || 'POST',
        headers: isUpload ? {} : {'Content-Type': 'application/json'},
        body: isUpload ? body : JSON.stringify(body),
      });
      const data = response.status === 204 ? {} : await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || 'The request could not be completed.');
      showMessage(form, data.status ? `Saved. Status: ${data.status}` : 'Saved successfully.');
      if (data.next) location.href = data.next;
      else if (data.id && form.hasAttribute('data-conversation-create')) {
        form.closest('.panel').querySelector('#chat').hidden = false;
        form.closest('.panel').querySelector('#chat-form').dataset.conversationId = data.id;
      } else if (data.id && form.hasAttribute('data-ai-lab')) {
        const box = form.parentElement.querySelector('.chat-box');
        box.hidden = false;
        box.querySelector('.lab-chat-form').dataset.conversationId = data.id;
      } else if (form.hasAttribute('data-import-case')) {
        showMessage(form, 'File uploaded. Extracting text for your review…');
        await pollImport(form, data.id);
      } else if (form.hasAttribute('data-refresh')) setTimeout(() => location.reload(), 600);
      else if (!isUpload) form.reset();
    } catch (error) {
      showMessage(form, error.message, true);
    } finally {
      if (button) button.disabled = false;
    }
  });
});

document.querySelectorAll('input[list="common-tests"]').forEach(input => {
  input.addEventListener('change', () => {
    const option = [...document.querySelectorAll('#common-tests option')].find(item => item.value.toLowerCase() === input.value.toLowerCase());
    const unit = input.closest('form')?.querySelector('[name="unit"]');
    if (option?.dataset.unit && unit && !unit.value) unit.value = option.dataset.unit;
  });
});

function fieldSelect(headers, name, required = false) {
  const label = document.createElement('label');
  label.textContent = name.replace('_', ' ');
  const select = document.createElement('select');
  select.dataset.field = name;
  if (required) select.required = true;
  const empty = document.createElement('option'); empty.value=''; empty.textContent='Choose a column'; select.appendChild(empty);
  for (const header of headers) {
    const option = document.createElement('option'); option.value=header; option.textContent=header;
    if (header.toLowerCase().replace(/[^a-z]/g,'').includes(name.replace('_','').toLowerCase())) option.selected=true;
    if (name === 'test_name' && ['test','analyte','assay'].includes(header.toLowerCase())) option.selected=true;
    if (name === 'value' && ['result','value','resultvalue'].includes(header.toLowerCase().replace(/[^a-z]/g,''))) option.selected=true;
    select.appendChild(option);
  }
  label.appendChild(select);
  return label;
}

async function pollImport(form, uploadId) {
  const caseId = form.dataset.importCase;
  const preview = form.querySelector('.import-preview');
  let data;
  for (let attempt=0; attempt<30; attempt++) {
    await new Promise(resolve => setTimeout(resolve, 1000));
    const response = await fetch(`/api/cases/${caseId}/import-preview?upload_id=${uploadId}`);
    data = await response.json();
    if (response.status === 202) continue;
    if (!response.ok) throw new Error(data.detail || 'Could not extract this file.');
    break;
  }
  if (!data || data.status !== 'review') return showMessage(form, 'Processing is taking longer than expected. Reload this page later to retry.', true);
  preview.hidden = false;
  preview.replaceChildren();
  const heading = document.createElement('h4'); heading.textContent='Review extracted results'; preview.appendChild(heading);
  const resultFields = ['test_name','value','unit','reference_range','status','observed_at','notes'];
  const resultRows = [];
  if (Array.isArray(data.rows) && data.rows.length) {
    const headers = Object.keys(data.rows[0]);
    const mapping = document.createElement('div'); mapping.className='form-grid import-mapping';
    for (const name of resultFields) mapping.appendChild(fieldSelect(headers, name, ['test_name','value'].includes(name)));
    preview.appendChild(mapping);
    const table = document.createElement('div'); table.className='table-wrap';
    const tableNode=document.createElement('table'), head=document.createElement('thead'), tr=document.createElement('tr');
    for (const header of headers) { const th=document.createElement('th'); th.textContent=header; tr.appendChild(th); }
    head.appendChild(tr); tableNode.appendChild(head);
    const body=document.createElement('tbody');
    data.rows.slice(0,100).forEach(row=>{ const rowNode=document.createElement('tr'); for(const header of headers){const td=document.createElement('td');td.textContent=String(row[header] ?? '');rowNode.appendChild(td)} body.appendChild(rowNode); });
    tableNode.appendChild(body); table.appendChild(tableNode); preview.appendChild(table);
    const confirm=document.createElement('button');confirm.type='button';confirm.className='button primary';confirm.textContent='Confirm selected rows';
    confirm.addEventListener('click',async()=>{
      const map={}; mapping.querySelectorAll('select').forEach(select=>map[select.dataset.field]=select.value);
      if(!map.test_name||!map.value){return showMessage(form,'Map both a test name and a result value.',true)}
      for(const row of data.rows.slice(0,500)){
        if(row[map.test_name] == null || row[map.value] == null) continue;
        resultRows.push({test_name:String(row[map.test_name]),value:String(row[map.value]),unit:String(row[map.unit]||''),reference_range:String(row[map.reference_range]||''),status:String(row[map.status]||''),observed_at:row[map.observed_at]||null,notes:String(row[map.notes]||'')});
      }
      await confirmImport(form, uploadId, resultRows);
    }); preview.appendChild(confirm);
  } else {
    const text=document.createElement('pre');text.className='extracted-text';text.textContent=data.extracted_text || 'No text was extracted.';preview.appendChild(text);
    const rowForm=document.createElement('div');rowForm.className='form-grid';
    const inputs={}; for(const name of resultFields){const label=document.createElement('label');label.textContent=name.replace('_',' ');const input=document.createElement(name==='notes'?'textarea':'input');input.dataset.field=name;label.appendChild(input);rowForm.appendChild(label);inputs[name]=input;}
    preview.appendChild(rowForm);
    const confirm=document.createElement('button');confirm.type='button';confirm.className='button primary';confirm.textContent='Confirm this result';confirm.addEventListener('click',()=>{const item={};for(const name of resultFields)item[name]=inputs[name].value||null;if(!item.test_name||!item.value)return showMessage(form,'Enter at least a test name and result value.',true);confirmImport(form,uploadId,[item]);});preview.appendChild(confirm);
  }
}

async function confirmImport(form, uploadId, results) {
  const caseId=form.dataset.importCase;
  const response=await fetch(`/api/cases/${caseId}/import-confirm`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({upload_id:Number(uploadId),results})});
  const data=await response.json();
  if(!response.ok)return showMessage(form,data.detail||'Could not save reviewed results.',true);
  showMessage(form,`${data.created} reviewed result(s) saved.`);
  setTimeout(()=>location.reload(),800);
}

document.querySelectorAll('form[data-attempt]').forEach(form => {
  form.addEventListener('submit', async event => {
    event.preventDefault();
    const picked = form.querySelector('input[name="answer_index"]:checked');
    if (!picked) return showMessage(form, 'Choose an answer first.', true);
    const response = await fetch(form.dataset.attempt, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({answer_index:Number(picked.value)})});
    const data = await response.json();
    const feedback = form.querySelector('.answer-feedback');
    feedback.textContent = response.ok ? `${data.correct ? 'Correct.' : 'Not quite.'} ${data.explanation || ''} Correct answer: ${data.correct_answer}` : (data.detail || 'Could not submit answer.');
  });
});

const chatForm = document.querySelector('#chat-form');
if (chatForm) {
  chatForm.addEventListener('submit', async event => {
    event.preventDefault();
    const conversationId = chatForm.dataset.conversationId;
    const textarea = chatForm.querySelector('textarea');
    const messages = document.querySelector('#chat-messages');
    const content = textarea.value.trim();
    if (!conversationId || !content) return;
    const userBubble=document.createElement('div');userBubble.className='chat-message user';
    const userLabel=document.createElement('strong');userLabel.textContent='You';
    const userText=document.createElement('span');userText.textContent=content;
    userBubble.append(userLabel,userText);messages.appendChild(userBubble);
    const response = await fetch(`/api/ai/conversations/${conversationId}/messages`, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({content})});
    const data = await response.json();
    if (!response.ok) { userBubble.remove(); return showMessage(chatForm, data.detail || 'AI is unavailable.', true); }
    const bubble = document.createElement('div');
    bubble.className = 'chat-message';
    const label = document.createElement('strong'); label.textContent = 'Assistant';
    const answer = document.createElement('span'); answer.textContent = data.answer;
    bubble.append(label, answer);
    messages.appendChild(bubble);
    if (data.citations?.length) {
      const citations = document.createElement('small');
      citations.textContent = 'Sources: ' + data.citations.map(x => x.label).join(', ');
      bubble.appendChild(citations);
    }
    textarea.value = '';
    showMessage(chatForm, '');
  });
}

document.querySelectorAll('.lab-chat-form').forEach(form=>{
  form.addEventListener('submit',async event=>{
    event.preventDefault();
    const content=form.querySelector('textarea').value.trim();
    const id=form.dataset.conversationId;
    if(!content||!id)return;
    const messages=form.parentElement.querySelector('.chat-messages');
    const userBubble=document.createElement('div');userBubble.className='chat-message user';
    const userLabel=document.createElement('strong');userLabel.textContent='You';
    const userText=document.createElement('span');userText.textContent=content;
    userBubble.append(userLabel,userText);messages.appendChild(userBubble);
    const response=await fetch(`/api/ai/conversations/${id}/messages`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({content})});
    const data=await response.json();
    if(!response.ok){userBubble.remove();return showMessage(form,data.detail||'AI is temporarily unavailable.',true)}
    const bubble=document.createElement('div');bubble.className='chat-message';
    const label=document.createElement('strong');label.textContent='Assistant';
    const answer=document.createElement('span');answer.textContent=data.answer;
    bubble.append(label,answer);messages.appendChild(bubble);
    form.querySelector('textarea').value='';showMessage(form,'');
  });
});
