import { useEffect, useRef, useState } from 'react';
import { Activity, ArrowUp, BookOpen, FileText, FolderOpen, LoaderCircle, Plus, Search, ShieldCheck, Sparkles, Trash2, UploadCloud, X } from 'lucide-react';
const API = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

export default function App() {
  const [documents, setDocuments] = useState([]);
  const [file, setFile] = useState(null);
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState([]);
  const [busy, setBusy] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [status, setStatus] = useState('Connecting');
  const fileRef = useRef(null);
  const bottomRef = useRef(null);

  async function refreshDocuments() {
    try {
      const r = await fetch(`${API}/documents`);
      if (!r.ok) throw new Error();
      setDocuments((await r.json()).documents || []);
      setStatus('Connected');
    } catch { setStatus('API offline'); }
  }
  useEffect(() => { refreshDocuments(); }, []);
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  async function uploadFile(e) {
    e.preventDefault();
    if (!file) return;
    setUploading(true); setError('');
    try {
      const form = new FormData(); form.append('file', file);
      const r = await fetch(`${API}/documents/upload`, { method: 'POST', body: form });
      const data = await r.json();
      if (!r.ok) throw new Error(data.detail || 'Upload failed');
      setMessages(p => [...p, { role: 'assistant', content: `Indexed “${data.filename}” successfully. I created ${data.chunks} searchable chunks. Ask a question grounded in this document.`, citations: [] }]);
      setFile(null); if (fileRef.current) fileRef.current.value = '';
      await refreshDocuments();
    } catch (err) { setError(err.message || 'Could not upload the document.'); }
    finally { setUploading(false); }
  }

  async function sendQuestion(e) {
    e?.preventDefault();
    const q = question.trim();
    if (!q || busy) return;
    setQuestion(''); setError('');
    setMessages(p => [...p, { role: 'user', content: q }]);
    setBusy(true);
    try {
      const r = await fetch(`${API}/chat`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question: q, top_k: 4 }) });
      const data = await r.json();
      if (!r.ok) throw new Error(data.detail || 'Question failed');
      setMessages(p => [...p, { role: 'assistant', content: data.answer, citations: data.citations || [] }]);
    } catch (err) { setMessages(p => [...p, { role: 'assistant', content: `I couldn't complete that request: ${err.message}`, citations: [] }]); }
    finally { setBusy(false); }
  }

  async function deleteDocument(doc) {
    if (!confirm(`Delete ${doc.filename} and its indexed chunks?`)) return;
    try {
      const r = await fetch(`${API}/documents/${doc.document_id}`, { method: 'DELETE' });
      const data = await r.json();
      if (!r.ok) throw new Error(data.detail || 'Delete failed');
      await refreshDocuments();
    } catch (err) { setError(err.message); }
  }

  const suggestions = ['Summarize the main policies in my documents.', 'What are the key requirements and deadlines?', 'What do the documents say about information security?'];
  return <div className="app-shell">
    <aside className="sidebar">
      <div className="brand"><div className="brand-mark"><Sparkles size={20}/></div><div><strong>Knowledge</strong><span>INTELLIGENCE PLATFORM</span></div></div>
      <button className="new-chat" onClick={() => setMessages([])}><Plus size={17}/> New conversation</button>
      <div className="side-label"><FolderOpen size={15}/> KNOWLEDGE BASE <span>{documents.length}</span></div>
      <form className="upload-card" onSubmit={uploadFile}>
        <input ref={fileRef} type="file" accept=".pdf,.docx,.txt,.md" onChange={e => setFile(e.target.files?.[0] || null)}/>
        <UploadCloud size={23}/><strong>Add a document</strong><p>PDF, DOCX, TXT or Markdown · 15 MB max</p>
        {file && <div className="selected-file"><FileText size={14}/>{file.name}</div>}
        <button type="submit" className="upload-button" disabled={!file || uploading}>{uploading ? <><LoaderCircle className="spin" size={15}/> Indexing…</> : 'Upload & index'}</button>
      </form>
      <div className="document-list">{documents.map(doc => <div className="document-row" key={doc.document_id}>
        <div className="doc-icon"><FileText size={16}/></div><div className="doc-meta"><strong title={doc.filename}>{doc.filename}</strong><span>{doc.chunks} chunks</span></div>
        <button className="icon-button delete-button" title="Delete document" onClick={() => deleteDocument(doc)}><Trash2 size={15}/></button>
      </div>)}{!documents.length && <p className="empty-docs">Your knowledge base is empty. Upload a document to begin.</p>}</div>
      <div className="sidebar-bottom"><div className="privacy-note"><ShieldCheck size={17}/><span><strong>Local-first prototype</strong><small>Your files stay on this machine.</small></span></div><div className="profile"><div className="avatar">KI</div><div><strong>Knowledge Workspace</strong><small>Developer preview</small></div><Activity size={16} className="profile-activity"/></div></div>
    </aside>
    <main className="main-panel">
      <header className="topbar"><div><span className="eyebrow">WORKSPACE / KNOWLEDGE ASSISTANT</span><h1>Ask your knowledge base</h1></div><div className={`connection-pill ${status === 'Connected' ? 'online' : 'offline'}`}><span className="status-dot"/>{status}</div></header>
      <section className="chat-area">
        {!messages.length ? <div className="welcome"><div className="welcome-icon"><BookOpen size={27}/></div><span className="eyebrow">YOUR DOCUMENTS, UNDERSTOOD</span><h2>Good knowledge starts<br/>with a better question.</h2><p>Ask questions across your uploaded files. Answers are generated from retrieved passages and include source evidence so you can verify them.</p>
          <div className="suggestion-grid">{suggestions.map((s,i) => <button key={s} onClick={() => setQuestion(s)}><span>0{i+1}</span>{s}<ArrowUp size={15} className="suggestion-arrow"/></button>)}</div>
          <div className="welcome-foot"><ShieldCheck size={15}/> Grounded answers <span/><Search size={15}/> Semantic retrieval <span/><FileText size={15}/> Source citations</div>
        </div> : <div className="messages">{messages.map((m,i) => <article className={`message ${m.role}`} key={`${i}-${m.role}`}>
          <div className={`message-avatar ${m.role}`}>{m.role === 'assistant' ? <Sparkles size={17}/> : 'You'}</div><div className="message-body"><div className="message-author">{m.role === 'assistant' ? 'Knowledge Assistant' : 'You'} <span>{m.role === 'assistant' ? 'AI RESPONSE' : 'QUESTION'}</span></div><p>{m.content}</p>
            {m.citations?.length > 0 && <div className="citations"><div className="citation-heading"><BookOpen size={15}/> SOURCES USED <span>{m.citations.length}</span></div>{m.citations.map((c,j) => <div className="citation" key={`${c.document_id}-${c.chunk_id}-${j}`}><div className="citation-top"><FileText size={14}/><strong>{c.filename}</strong><span>{c.page ? `Page ${c.page}` : `Chunk ${c.chunk_id+1}`}</span><small>score {c.score.toFixed(2)}</small></div><p>{c.excerpt}</p></div>)}</div>}
          </div></article>)}{busy && <div className="thinking"><span className="thinking-dots"><i/><i/><i/></span>Searching sources and preparing an answer…</div>}<div ref={bottomRef}/></div>}
      </section>
      {error && <div className="error-banner"><X size={16}/>{error}<button onClick={() => setError('')}><X size={14}/></button></div>}
      <div className="composer-wrap"><form className="composer" onSubmit={sendQuestion}><textarea value={question} onChange={e => setQuestion(e.target.value)} placeholder="Ask a question about your documents…" rows={1} onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendQuestion(); } }}/><button type="submit" disabled={!question.trim() || busy} title="Send question">{busy ? <LoaderCircle className="spin" size={18}/> : <ArrowUp size={19}/>}</button></form><div className="composer-hint">AI-generated responses can be wrong. Verify important details against the cited source. <kbd>Enter</kbd> to send · <kbd>Shift + Enter</kbd> for a new line</div></div>
    </main>
  </div>;
}
