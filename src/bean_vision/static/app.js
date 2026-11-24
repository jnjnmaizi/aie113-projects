const $ = (id) => document.getElementById(id);
const labels = { healthy: 'ورقة سليمة', bean_rust: 'صدأ الفاصوليا', angular_leaf_spot: 'التبقّع الزاوي' };
const messages = { not_ready: 'النموذج غير جاهز الآن. حاول مجددًا بعد قليل.', busy: 'النموذج مشغول. حاول مجددًا بعد قليل.', file_too_large: 'حجم الملف يتجاوز 5 ميجابايت.', image_too_large: 'أبعاد الصورة كبيرة جدًا. استخدم صورة أقل من 16 مليون بكسل.', unsupported_type: 'اختر صورة JPEG أو PNG.', invalid_image: 'تعذر قراءة الصورة. اختر ملف JPEG أو PNG صالحًا.' };
let file = null, previewURL = null, heatmapURL = null, busy = false;
const percent = (value) => new Intl.NumberFormat('ar', { style: 'percent', maximumFractionDigits: 1 }).format(value);
function showError(message) { $('error').textContent = message; $('error').hidden = !message; }
function selectFile(next) {
  if (busy) return;
  showError('');
  if (next && !['image/jpeg', 'image/png'].includes(next.type)) return showError(messages.unsupported_type);
  if (next && next.size > 5 * 1024 * 1024) return showError(messages.file_too_large);
  file = next;
  if (previewURL) URL.revokeObjectURL(previewURL);
  if (heatmapURL) URL.revokeObjectURL(heatmapURL);
  previewURL = next ? URL.createObjectURL(next) : null;
  $('preview').hidden = !next;
  if (next) $('preview').src = previewURL; else $('preview').removeAttribute('src');
  $('upload-prompt').hidden = !!next;
  $('filename').textContent = next ? next.name : 'لم تُختر صورة بعد';
  $('reset').hidden = !next;
  $('analyze').disabled = !next;
  $('result').hidden = true; $('empty').hidden = false; $('explanation').hidden = true;
}
function setBusy(value, explaining = false) {
  busy = value; $('file').disabled = value; $('reset').disabled = value;
  $('analyze').disabled = value || !file; $('explain').disabled = value;
  $('analyze').textContent = value && !explaining ? 'جارٍ تحليل الصورة…' : 'تحليل الصورة ←';
  $('explain').textContent = value && explaining ? 'جارٍ إنشاء التفسير… قد يستغرق دقيقة' : 'عرض تفسير بصري';
}
async function request(path, timeout) {
  const controller = new AbortController(); const timer = setTimeout(() => controller.abort(), timeout);
  try {
    const data = new FormData(); data.append('file', file);
    const response = await fetch(path, { method: 'POST', body: data, signal: controller.signal });
    if (!response.ok) { const body = await response.json().catch(() => ({})); throw new Error(messages[body.error?.code] || 'تعذر إتمام الطلب. حاول مجددًا.'); }
    return path.endsWith('explain') ? await response.blob() : await response.json();
  } catch (error) {
    if (error.name === 'AbortError') throw new Error('انتهت مهلة الانتظار. حاول مجددًا بعد قليل.');
    if (error instanceof TypeError) throw new Error('تعذر الاتصال بالخدمة. تحقق من تشغيلها ثم حاول مجددًا.');
    throw error;
  } finally { clearTimeout(timer); }
}
$('file').addEventListener('change', (event) => selectFile(event.target.files[0] || null));
$('reset').addEventListener('click', () => { $('file').value = ''; selectFile(null); });
for (const name of ['dragover', 'dragleave', 'drop']) $('dropzone').addEventListener(name, (event) => {
  event.preventDefault(); $('dropzone').classList.toggle('drag', name === 'dragover');
  if (name === 'drop') selectFile(event.dataTransfer.files[0] || null);
});
$('analyze').addEventListener('click', async () => {
  if (!file || busy) return; showError(''); setBusy(true);
  $('result').hidden = true; $('empty').hidden = false; $('explanation').hidden = true;
  try {
    const data = await request('/v1/predict', 60000);
    $('label').textContent = data.not_sure ? 'غير متأكد' : labels[data.label] || data.label;
    $('decision').textContent = data.not_sure ? `أعلى فئة: ${labels[data.label] || data.label} — الثقة أقل من 80٪.` : 'اقرأ درجات الفئات والتنبيه قبل استخدام النتيجة.';
    $('confidence').textContent = percent(data.confidence); $('scores').replaceChildren();
    for (const [label, value] of Object.entries(data.scores).sort((a, b) => b[1] - a[1])) {
      const row = document.createElement('div'); row.className = 'score';
      const heading = document.createElement('div'); const name = document.createElement('span'); const score = document.createElement('span');
      name.textContent = labels[label] || label; score.textContent = percent(value); heading.append(name, score);
      const bar = document.createElement('progress'); bar.max = 1; bar.value = value; bar.setAttribute('aria-label', labels[label] || label);
      row.append(heading, bar); $('scores').append(row);
    }
    $('empty').hidden = true; $('result').hidden = false;
  } catch (error) { showError(error.message); } finally { setBusy(false); }
});
$('explain').addEventListener('click', async () => {
  if (!file || busy) return; showError(''); setBusy(true, true);
  try {
    const blob = await request('/v1/explain', 180000);
    if (heatmapURL) URL.revokeObjectURL(heatmapURL);
    heatmapURL = URL.createObjectURL(blob); $('heatmap').src = heatmapURL; $('explanation').hidden = false;
  } catch (error) { showError(error.message); } finally { setBusy(false); }
});
async function readiness() {
  try { const response = await fetch('/ready', { signal: AbortSignal.timeout(5000) }); $('status').textContent = response.ok ? '● النموذج جاهز للفحص' : '○ النموذج قيد التحميل أو غير جاهز'; }
  catch { $('status').textContent = '○ تعذر الاتصال بالخدمة'; }
}
readiness(); setInterval(readiness, 30000);
