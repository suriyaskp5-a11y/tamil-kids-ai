import React, { useState, useEffect } from 'react';
import { api } from './services/api';

export default function App() {
  const [token, setToken] = useState(api.getToken());
  const [activeTab, setActiveTab] = useState('dashboard');
  const [summary, setSummary] = useState(null);
  const [health, setHealth] = useState(null);
  const [topics, setTopics] = useState([]);
  const [stories, setStories] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [settings, setSettings] = useState({});
  const [loading, setLoading] = useState(false);
  const [actionMsg, setActionMsg] = useState('');

  // Login form state
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('adminpassword123');
  const [loginError, setLoginError] = useState('');

  useEffect(() => {
    if (token) {
      loadInitialData();
      const interval = setInterval(() => {
        loadSummaryAndJobs();
      }, 5000);
      return () => clearInterval(interval);
    }
  }, [token]);

  const loadInitialData = async () => {
    try {
      const [sumData, hlthData, topData, storData, jbData, settData] = await Promise.all([
        api.getSummary().catch(() => null),
        api.getHealth().catch(() => null),
        api.getTopics().catch(() => []),
        api.getStories().catch(() => []),
        api.getJobs().catch(() => []),
        api.getSettings().catch(() => ({}))
      ]);
      setSummary(sumData);
      setHealth(hlthData);
      setTopics(topData);
      setStories(storData);
      setJobs(jbData);
      setSettings(settData);
    } catch (err) {
      console.error(err);
    }
  };

  const loadSummaryAndJobs = async () => {
    try {
      const [sumData, jbData] = await Promise.all([
        api.getSummary().catch(() => null),
        api.getJobs().catch(() => [])
      ]);
      if (sumData) setSummary(sumData);
      if (jbData) setJobs(jbData);
    } catch (err) {
      console.error(err);
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoginError('');
    try {
      const res = await api.login(username, password);
      setToken(res.access_token);
    } catch (err) {
      setLoginError(err.message || 'Login failed');
    }
  };

  const handleLogout = () => {
    api.clearToken();
    setToken(null);
  };

  const triggerGenerateTopic = async () => {
    setLoading(true);
    setActionMsg('Generating new Tamil topic...');
    try {
      const newTopic = await api.generateTopic();
      setTopics([newTopic, ...topics]);
      setActionMsg(`Created topic: ${newTopic.title_tamil}`);
    } catch (err) {
      setActionMsg(`Failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const triggerFullPipeline = async (topicId = null) => {
    setLoading(true);
    setActionMsg('Triggering automated video production pipeline...');
    try {
      const job = await api.triggerJob(topicId);
      setActionMsg(`Started Job #${job.id}! Rendering in background.`);
      loadSummaryAndJobs();
    } catch (err) {
      setActionMsg(`Trigger failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const toggleSetting = async (key, currentValue) => {
    const newValue = currentValue === 'true' ? 'false' : 'true';
    try {
      await api.updateSetting(key, newValue);
      setSettings({ ...settings, [key]: newValue });
    } catch (err) {
      alert(`Update failed: ${err.message}`);
    }
  };

  if (!token) {
    return (
      <div className="flex items-center justify-center min-h-screen px-4 bg-slate-950">
        <div className="w-full max-w-md p-8 bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl">
          <div className="text-center mb-8">
            <span className="text-5xl">🎬</span>
            <h1 className="mt-4 text-2xl font-bold text-amber-400">Tamil Kids AI</h1>
            <p className="text-sm text-slate-400 mt-1">தானியங்கி யூடியூப் கார்ட்டூன் தளம்</p>
          </div>

          {loginError && (
            <div className="p-3 mb-4 text-sm text-rose-300 bg-rose-950/50 border border-rose-800 rounded-lg">
              {loginError}
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">பயனர் பெயர் (Username)</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-amber-400"
                required
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">கடவுச்சொல் (Password)</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-2.5 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:border-amber-400"
                required
              />
            </div>
            <button
              type="submit"
              className="w-full py-3 px-4 font-semibold text-slate-950 bg-amber-400 hover:bg-amber-300 rounded-lg transition"
            >
              உள்நுழைக (Sign In)
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100">
      {/* Top Navbar */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <span className="text-2xl">🎬</span>
            <div>
              <h1 className="font-bold text-amber-400 leading-tight">Tamil Kids AI</h1>
              <p className="text-xs text-slate-400">YouTube 3D Stories Automation</p>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            {health && (
              <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${
                health.status === 'healthy' ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-rose-950 text-rose-400 border border-rose-800'
              }`}>
                ● {health.status === 'healthy' ? 'System Online' : 'Check System'}
              </span>
            )}
            <button
              onClick={handleLogout}
              className="px-3 py-1.5 text-xs text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-lg border border-slate-700 transition"
            >
              வெளியேறு (Logout)
            </button>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <div className="max-w-7xl mx-auto px-4 py-6 w-full flex-1 flex flex-col md:flex-row gap-6">
        {/* Sidebar Nav */}
        <nav className="w-full md:w-64 space-y-1">
          {[
            { id: 'dashboard', label: 'கட்டுப்பாட்டகம்', sub: 'Dashboard', icon: '📊' },
            { id: 'topics', label: 'தலைப்புகள்', sub: 'Story Topics', icon: '💡' },
            { id: 'stories', label: 'கதைகள் & ஸ்கிரிப்ட்', sub: 'Stories & Scripts', icon: '📜' },
            { id: 'jobs', label: 'தயாரிப்பு பணிகள்', sub: 'Video Jobs', icon: '⚙️' },
            { id: 'settings', label: 'அமைப்புகள் & பாதுகாப்பு', sub: 'Settings & Safety', icon: '🛡️' }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl text-left transition ${
                activeTab === tab.id
                  ? 'bg-amber-400 text-slate-950 font-bold shadow-lg shadow-amber-400/20'
                  : 'text-slate-300 hover:bg-slate-800/80 hover:text-white'
              }`}
            >
              <span className="text-xl">{tab.icon}</span>
              <div>
                <div className="text-sm">{tab.label}</div>
                <div className={`text-xs ${activeTab === tab.id ? 'text-slate-800 font-normal' : 'text-slate-500'}`}>{tab.sub}</div>
              </div>
            </button>
          ))}

          {/* Quick Action Box */}
          <div className="mt-8 p-4 bg-slate-900 border border-slate-800 rounded-2xl">
            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">நேரடி தயாரிப்பு (Quick Action)</h3>
            <button
              onClick={() => triggerFullPipeline()}
              disabled={loading}
              className="w-full py-2.5 px-3 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-400 hover:to-orange-400 text-slate-950 font-bold text-xs rounded-xl shadow-md transition disabled:opacity-50"
            >
              {loading ? 'தயாராகிறது...' : '⚡ புதிய வீடியோவை உருவாக்கு'}
            </button>
            {actionMsg && (
              <p className="mt-2 text-xs text-amber-300 bg-slate-950 p-2 rounded border border-slate-800">
                {actionMsg}
              </p>
            )}
          </div>
        </nav>

        {/* Tab Content Panes */}
        <main className="flex-1 space-y-6">
          {/* TAB 1: DASHBOARD */}
          {activeTab === 'dashboard' && (
            <div className="space-y-6">
              {/* Summary Stats Cards */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                {[
                  { label: 'மொத்த தலைப்புகள்', sub: 'Topics Created', val: summary?.total_topics || 0, icon: '💡', color: 'from-blue-500 to-indigo-600' },
                  { label: 'உருவாக்கப்பட்ட கதைகள்', sub: 'Stories Generated', val: summary?.total_stories || 0, icon: '📖', color: 'from-amber-500 to-orange-600' },
                  { label: 'வெளியிடப்பட்ட வீடியோக்கள்', sub: 'Published on YouTube', val: summary?.published_videos || 0, icon: '▶️', color: 'from-emerald-500 to-teal-600' },
                  { label: 'தயாரிப்பு பணிகள்', sub: 'Total Jobs Run', val: summary?.total_jobs || 0, icon: '⚙️', color: 'from-purple-500 to-pink-600' }
                ].map((card, i) => (
                  <div key={i} className="p-4 bg-slate-900 border border-slate-800 rounded-2xl shadow-sm">
                    <div className="flex items-center justify-between text-2xl mb-2">
                      <span>{card.icon}</span>
                      <span className="text-2xl font-extrabold text-white">{card.val}</span>
                    </div>
                    <div className="text-xs font-semibold text-slate-200">{card.label}</div>
                    <div className="text-[11px] text-slate-500">{card.sub}</div>
                  </div>
                ))}
              </div>

              {/* Active Pipeline Status */}
              <div className="p-6 bg-slate-900 border border-slate-800 rounded-2xl">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h2 className="text-lg font-bold text-white">தானியங்கி தயாரிப்பு நிலை (Current Automation Stage)</h2>
                    <p className="text-xs text-slate-400">அடுத்த தானியங்கி வெளியீடு: {summary?.next_scheduled_run || '09:00 AM Asia/Kolkata'}</p>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                    summary?.current_active_job ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30 animate-pulse' : 'bg-slate-800 text-slate-400'
                  }`}>
                    {summary?.current_active_job ? 'தயாரிப்பில் உள்ளது (Rendering)' : 'தயாராக உள்ளது (Idle)'}
                  </span>
                </div>

                {summary?.current_active_job ? (
                  <div className="space-y-3">
                    <div className="flex justify-between text-xs text-slate-300">
                      <span>படி: <strong className="text-amber-400">{summary.current_active_job.stage}</strong></span>
                      <span>முன்னேற்றம்: <strong>{summary.current_active_job.progress}%</strong></span>
                    </div>
                    <div className="w-full bg-slate-800 rounded-full h-3 overflow-hidden">
                      <div
                        className="bg-gradient-to-r from-amber-400 to-orange-500 h-3 rounded-full transition-all duration-500"
                        style={{ width: `${summary.current_active_job.progress}%` }}
                      ></div>
                    </div>
                  </div>
                ) : (
                  <div className="p-4 bg-slate-950 border border-slate-800/80 rounded-xl text-center text-sm text-slate-400">
                    தற்போது பணிகள் எதுவும் இயங்கவில்லை. தினமும் காலை 09:00 மணிக்கு தானாகவே ஒரு புதிய கதை உருவாக்கப்படும்.
                  </div>
                )}
              </div>

              {/* Safety & Publishing Switches */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-5 bg-slate-900 border border-slate-800 rounded-2xl flex items-center justify-between">
                  <div>
                    <div className="text-sm font-bold text-white">தானியங்கி யூடியூப் வெளியீடு (Auto Publish)</div>
                    <div className="text-xs text-slate-400">வீடியோ முடிந்ததும் தானாகவே யூடியூப்பில் பதிவேற்றவும்</div>
                  </div>
                  <button
                    onClick={() => toggleSetting('auto_publish_enabled', settings.auto_publish_enabled)}
                    className={`w-12 h-6 flex items-center rounded-full p-1 transition ${
                      settings.auto_publish_enabled === 'true' ? 'bg-emerald-500 justify-end' : 'bg-slate-700 justify-start'
                    }`}
                  >
                    <div className="bg-white w-4 h-4 rounded-full shadow-md"></div>
                  </button>
                </div>

                <div className="p-5 bg-slate-900 border border-slate-800 rounded-2xl flex items-center justify-between">
                  <div>
                    <div className="text-sm font-bold text-white">கண்காணிப்பு ஒப்புதல் (Manual Approval Mode)</div>
                    <div className="text-xs text-slate-400">வெளியிடுவதற்கு முன் நிர்வாகி ஒப்புதல் கோரப்படும்</div>
                  </div>
                  <button
                    onClick={() => toggleSetting('require_manual_approval', settings.require_manual_approval)}
                    className={`w-12 h-6 flex items-center rounded-full p-1 transition ${
                      settings.require_manual_approval === 'true' ? 'bg-amber-500 justify-end' : 'bg-slate-700 justify-start'
                    }`}
                  >
                    <div className="bg-white w-4 h-4 rounded-full shadow-md"></div>
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: TOPICS */}
          {activeTab === 'topics' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-bold text-white">தமிழ் சிறார் கதைகளின் தலைப்புகள்</h2>
                  <p className="text-xs text-slate-400">மழலையர் மற்றும் குழந்தைகளுக்கான கல்வி, நற்பண்பு கதைகள்</p>
                </div>
                <button
                  onClick={triggerGenerateTopic}
                  disabled={loading}
                  className="px-4 py-2 bg-amber-400 text-slate-950 font-bold text-xs rounded-xl hover:bg-amber-300 transition"
                >
                  + புதிய தலைப்பை உருவாக்கு
                </button>
              </div>

              <div className="space-y-3">
                {topics.map(t => (
                  <div key={t.id} className="p-4 bg-slate-900 border border-slate-800 rounded-2xl flex items-center justify-between">
                    <div className="space-y-1">
                      <div className="flex items-center space-x-2">
                        <span className="px-2 py-0.5 text-[11px] font-semibold bg-amber-400/20 text-amber-300 rounded border border-amber-400/30">
                          {t.category}
                        </span>
                        <h3 className="font-bold text-white text-base">{t.title_tamil}</h3>
                      </div>
                      <p className="text-xs text-slate-400">{t.synopsis || t.title_english}</p>
                      <div className="text-xs text-emerald-400 font-medium">நீதி: {t.target_moral}</div>
                    </div>
                    <button
                      onClick={() => triggerFullPipeline(t.id)}
                      className="px-3 py-1.5 text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-amber-400 border border-slate-700 rounded-xl transition"
                    >
                      வீடியோ உருவாக்கு ▶
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 3: STORIES */}
          {activeTab === 'stories' && (
            <div className="space-y-4">
              <h2 className="text-xl font-bold text-white">முழுமையான கதைகள் மற்றும் காட்சி அமைப்புகள் (Scripts)</h2>
              <div className="space-y-4">
                {stories.map(s => (
                  <div key={s.id} className="p-5 bg-slate-900 border border-slate-800 rounded-2xl space-y-3">
                    <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                      <div>
                        <h3 className="text-lg font-bold text-amber-400">{s.title_tamil}</h3>
                        <p className="text-xs text-slate-400">நீதி: {s.moral_tamil} • காலம்: ~10 நிமிடங்கள் ({s.word_count} சொற்கள்)</p>
                      </div>
                      <span className="px-2.5 py-1 text-xs bg-emerald-950 text-emerald-400 border border-emerald-800 rounded-full font-medium">
                        {s.status}
                      </span>
                    </div>

                    <div className="p-3 bg-slate-950 rounded-xl text-sm text-slate-300 leading-relaxed max-h-48 overflow-y-auto whitespace-pre-line border border-slate-800/80">
                      {s.full_story_tamil}
                    </div>

                    {s.character_bible && (
                      <div className="space-y-1">
                        <div className="text-xs font-semibold text-slate-400 uppercase">3D கதாபாத்திரங்கள்:</div>
                        <div className="flex flex-wrap gap-2">
                          {s.character_bible.map((ch, idx) => (
                            <span key={idx} className="text-xs px-2.5 py-1 bg-slate-800 border border-slate-700 rounded-lg text-slate-200">
                              🐰 {ch.name_tamil} ({ch.role})
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 4: JOBS */}
          {activeTab === 'jobs' && (
            <div className="space-y-4">
              <h2 className="text-xl font-bold text-white">தயாரிப்பு மற்றும் பதிவேற்ற பணிகள் (Jobs Log)</h2>
              <div className="space-y-3">
                {jobs.map(j => (
                  <div key={j.id} className="p-4 bg-slate-900 border border-slate-800 rounded-2xl flex items-center justify-between">
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="font-bold text-white">பணி #{j.id}</span>
                        <span className="text-xs px-2 py-0.5 bg-slate-800 text-slate-300 rounded border border-slate-700">
                          நிலை: {j.stage}
                        </span>
                      </div>
                      <p className="text-xs text-slate-400 mt-1">கதை அடையாள எண்: #{j.story_id}</p>
                    </div>

                    <div className="flex items-center space-x-4">
                      <div className="text-right">
                        <span className="text-sm font-bold text-amber-400">{j.progress}%</span>
                        <div className="text-[11px] text-slate-500">{j.status}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 5: SETTINGS */}
          {activeTab === 'settings' && (
            <div className="space-y-6">
              <h2 className="text-xl font-bold text-white">அமைப்புகள் & பாதுகாப்பு விதிகள் (Channel Settings)</h2>

              <div className="p-5 bg-slate-900 border border-slate-800 rounded-2xl space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-bold text-white">தினசரி வெளியீட்டு நேரம் (Daily Publish Time)</h3>
                    <p className="text-xs text-slate-400">இந்திய நேரப்படி தானியங்கி வெளியீடு (Asia/Kolkata)</p>
                  </div>
                  <input
                    type="time"
                    defaultValue="09:00"
                    className="px-3 py-1.5 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm"
                  />
                </div>

                <div className="flex items-center justify-between border-t border-slate-800 pt-4">
                  <div>
                    <h3 className="text-sm font-bold text-white">குரல் தேர்வு (Tamil TTS Voice)</h3>
                    <p className="text-xs text-slate-400">Microsoft Edge Neural Tamil Voice</p>
                  </div>
                  <select
                    defaultValue="ta-IN-PallaviNeural"
                    className="px-3 py-1.5 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm"
                  >
                    <option value="ta-IN-PallaviNeural">Pallavi (அன்பான கதை சொல்லும் குரல் - பெண்)</option>
                    <option value="ta-IN-ValluvarNeural">Valluvar (கம்பீர குரல் - ஆண்)</option>
                  </select>
                </div>

                <div className="flex items-center justify-between border-t border-slate-800 pt-4">
                  <div>
                    <h3 className="text-sm font-bold text-white">குழந்தைகளுக்கான பாதுகாப்பு (Made For Kids)</h3>
                    <p className="text-xs text-slate-400">YouTube COPPA விதிமுறைப்படி தானாகவே இயக்கப்பட்டுள்ளது</p>
                  </div>
                  <span className="text-xs px-2.5 py-1 bg-emerald-950 text-emerald-400 border border-emerald-800 rounded-full font-bold">
                    ✓ இயக்கப்பட்டிருக்கிறது (Enabled)
                  </span>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
