const api = '/api/social/';
const token = () => localStorage.getItem('chirp-token');
const authHeaders = () => token() ? { 'Content-Type': 'application/json', Authorization: `Token ${token()}` } : {};
const escapeHtml = value => String(value).replace(/[&<>'"]/g, character => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' })[character]);

function formatTime(isoString) {
  const date = new Date(isoString);
  const now = new Date();
  const seconds = Math.floor((now - date) / 1000);
  if (seconds < 60) return 'agora';
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d`;
  return date.toLocaleDateString('pt-BR');
}

async function request(path, options = {}) {
  const response = await fetch(api + path, options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || Object.values(data).flat().join(' ') || 'Não foi possível concluir a ação.');
  return data;
}

function setMessage(message) {
  const target = document.querySelector('.form-message') || document.querySelector('#timeline-title');
  if (target) target.textContent = message;
}

function setPostMessage(message) {
  const target = document.querySelector('#post-message');
  if (target) target.textContent = message;
}

function avatarMarkup(username, avatarUrl, className = '') {
  const classes = `avatar ${className}`.trim();
  if (avatarUrl) return `<img class="${classes} avatar-image" src="${escapeHtml(avatarUrl)}" alt="">`;
  return `<div class="${classes}">${escapeHtml(username.charAt(0).toUpperCase())}</div>`;
}

function showAuth(open) { document.querySelector('#auth-layer').hidden = !open; }

function updateNavigation(profile = null) {
  const page = document.body.dataset.page === 'profile' ? 'settings' : document.body.dataset.page;
  document.querySelectorAll('[data-nav]').forEach(link => link.classList.toggle('is-active', link.dataset.nav === page));
  const account = document.querySelector('.account-summary');
  if (!account) return;
  account.hidden = !profile;
  if (!profile) return;
  const profileUrl = `/api/social/profile/${encodeURIComponent(profile.username)}/`;
  account.href = profileUrl;
  document.querySelectorAll('[data-nav="settings"]').forEach(link => { link.href = profileUrl; });
  account.querySelector('.account-avatar').textContent = profile.username.charAt(0).toUpperCase();
  account.querySelector('.account-name').textContent = profile.first_name || profile.username;
  account.querySelector('.account-handle').textContent = `@${profile.username}`;
  account.querySelector('.account-avatar').style.backgroundImage = profile.avatar_url ? `url("${profile.avatar_url}")` : '';
  account.querySelector('.account-avatar').classList.toggle('avatar-has-image', Boolean(profile.avatar_url));
}

function renderComments(comments) {
  if (!comments.length) return '';
  return `<div class="post-comments">${comments.map(comment => `<div class="comment">${avatarMarkup(comment.author, comment.author_avatar_url, 'comment-avatar')}<div><div class="comment-meta"><a href="/api/social/profile/${encodeURIComponent(comment.author)}/">${escapeHtml(comment.author)}</a><span>${formatTime(comment.created_at)}</span></div><p class="comment-content">${escapeHtml(comment.content)}</p></div></div>`).join('')}</div>`;
}

function postCard(post) {
  const timestamp = `<span title="${new Date(post.created_at).toLocaleString('pt-BR')}">${formatTime(post.created_at)}</span>`;
  const likeLabel = post.is_liked ? 'Curtido' : 'Curtir';
  const actions = token() ? `<div class="post-actions"><button data-like="${post.id}" data-liked="${post.is_liked}">${likeLabel} ${post.likes_count}</button><button data-toggle-comment="${post.id}">Comentar ${post.comments.length}</button></div>` : '';
  const comments = renderComments(post.comments);
  return `<article class="post">${avatarMarkup(post.author, post.author_avatar_url, 'post-avatar')}<div><div class="post-meta"><a href="/api/social/profile/${encodeURIComponent(post.author)}/">${escapeHtml(post.author)}</a><span>@${escapeHtml(post.author)}</span>${timestamp}</div><p class="post-content">${escapeHtml(post.content)}</p>${comments}${actions}</div><form class="comment-form" data-comment="${post.id}" hidden><input name="content" maxlength="280" placeholder="Escreva uma resposta" required><button>Responder</button></form></article>`;
}

async function loadTimeline() {
  const container = document.querySelector('#feed');
  if (!container) return;
  try {
    const path = token() ? 'posts/feed/' : 'posts/';
    const data = await request(path, { headers: authHeaders() });
    const emptyState = token()
      ? '<p class="empty">Seu feed está vazio. <a href="/api/social/explore/">Encontre pessoas para seguir.</a></p>'
      : '<p class="empty">Ainda não há postagens para mostrar.</p>';
    container.innerHTML = data.results.length ? data.results.map(postCard).join('') : emptyState;
    const title = document.querySelector('#timeline-title');
    if (title) title.textContent = token() ? 'Seu feed' : 'Timeline pública';
  } catch (error) { container.innerHTML = `<p class="empty">${escapeHtml(error.message)}</p>`; }
}

async function getProfiles() {
  let path = 'profiles/'; const profiles = [];
  while (path) { const data = await request(path, { headers: authHeaders() }); profiles.push(...data.results); path = data.next ? data.next.replace(location.origin + api, '') : null; }
  return profiles;
}

function profileRow(profile) {
  const follow = token() ? `<button data-follow="${profile.id}" data-following="${profile.is_following}">${profile.is_following ? 'Deixar de seguir' : 'Seguir'}</button>` : '';
  return `<article class="profile-row">${avatarMarkup(profile.username, profile.avatar_url || profile.avatar)}<div class="profile-copy"><a href="/api/social/profile/${encodeURIComponent(profile.username)}/">${escapeHtml(profile.username)}</a><p>${profile.followers_count} seguidores · ${profile.following_count} seguindo</p></div>${follow}</article>`;
}

async function loadExplore() {
  const container = document.querySelector('#profile-results');
  if (!container) return;
  const profiles = await getProfiles();
  const currentProfile = token() ? await request('profiles/me/', { headers: authHeaders() }) : null;
  const search = document.querySelector('#profile-search');
  search.value = new URLSearchParams(location.search).get('q') || '';
  const render = () => { const query = search.value.trim().toLowerCase(); const matches = profiles.filter(profile => profile.id !== currentProfile?.id && profile.username.toLowerCase().includes(query)); container.innerHTML = matches.length ? matches.map(profileRow).join('') : '<p class="empty">Nenhum perfil encontrado.</p>'; };
  search.addEventListener('input', render); render();
}

async function loadProfilePage() {
  const hero = document.querySelector('.profile-hero');
  if (!hero) return;
  const username = hero.dataset.username;
  const profile = await request(`profiles/by-username/${encodeURIComponent(username)}/`, { headers: authHeaders() });
  document.querySelector('#profile-name').textContent = profile.first_name || profile.username;
  document.querySelector('#profile-handle').textContent = `@${profile.username}`;
  const avatar = document.querySelector('#profile-avatar');
  avatar.textContent = profile.username.charAt(0).toUpperCase();
  avatar.style.backgroundImage = profile.avatar_url ? `url("${profile.avatar_url}")` : '';
  avatar.classList.toggle('avatar-has-image', Boolean(profile.avatar_url));
  document.querySelector('#profile-stats').innerHTML = `<button data-connections="following"><strong>${profile.following_count}</strong> seguindo</button><button data-connections="followers"><strong>${profile.followers_count}</strong> seguidores</button>`;
  if (token()) {
    const currentProfile = await request('profiles/me/', { headers: authHeaders() });
    updateNavigation(currentProfile);
    document.querySelector('#profile-actions').innerHTML = currentProfile.id === profile.id
      ? '<a class="profile-edit" href="/api/social/settings/">Editar perfil</a>'
      : `<button data-follow="${profile.id}" data-following="${profile.is_following}">${profile.is_following ? 'Deixar de seguir' : 'Seguir'}</button>`;
  }
  
  const posts = await request(`posts/?author=${encodeURIComponent(username)}`, { headers: authHeaders() });
  document.querySelector('#profile-posts').innerHTML = posts.results.length ? posts.results.map(postCard).join('') : '<p class="empty">Nenhuma postagem ainda.</p>';
  
  // Load followers and following from API
  let followers_list = [];
  let following_list = [];
  if (token()) {
    try {
      followers_list = await request(`profiles/${profile.id}/followers/`, { headers: authHeaders() });
      following_list = await request(`profiles/${profile.id}/following/`, { headers: authHeaders() });
    } catch (e) {}
  }
  
  // Render followers list
  const followersHTML = followers_list.length ? followers_list.map(p => profileRow(p)).join('') : '<p class="empty">Nenhum seguidor ainda.</p>';
  document.querySelector('#profile-followers').innerHTML = followersHTML;
  
  // Render following list
  const followingHTML = following_list.length ? following_list.map(p => profileRow(p)).join('') : '<p class="empty">Não está seguindo ninguém.</p>';
  document.querySelector('#profile-following').innerHTML = followingHTML;
  
  // Tab switching
  document.querySelectorAll('.profile-tabs .tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.profile-tabs .tab').forEach(t => t.classList.remove('is-active'));
      document.querySelectorAll('.tab-content').forEach(c => c.hidden = true);
      tab.classList.add('is-active');
      const tabName = tab.dataset.tab;
      document.querySelector(`#profile-${tabName}`).hidden = false;
    });
  });
  document.querySelectorAll('[data-connections]').forEach(button => {
    button.addEventListener('click', () => {
      document.querySelector(`[data-tab="${button.dataset.connections}"]`).click();
    });
  });
}

async function loadSettings() {
  const form = document.querySelector('#profile-form');
  if (!form || !token()) return;
  document.querySelector('#settings-locked').hidden = true; form.hidden = false;
  const profile = await request('profiles/me/', { headers: authHeaders() });
  updateNavigation(profile);
  for (const [key, value] of Object.entries(profile)) { const field = form.elements.namedItem(key); if (field && typeof value === 'string') field.value = value; }
}

function updateAuthenticatedState() {
  document.querySelectorAll('[data-open-auth]').forEach(button => button.hidden = Boolean(token()));
  const accountCard = document.querySelector('#account-card');
  if (accountCard) accountCard.hidden = Boolean(token());
  const composer = document.querySelector('#post-form'); const locked = document.querySelector('#composer-locked');
  if (composer) composer.hidden = !token(); if (locked) locked.hidden = Boolean(token());
  updateNavigation();
  if (token()) { loadTimeline(); loadSettings(); }
}

document.addEventListener('click', async event => {
  const action = event.target;
  if (action.matches('[data-open-auth]')) showAuth(true);
  if (action.matches('[data-close-auth]')) showAuth(false);
  if (action.dataset.authTab) { document.querySelectorAll('.auth-tabs .tab').forEach(tab => tab.classList.toggle('is-active', tab === action)); document.querySelector('#login-form').hidden = action.dataset.authTab !== 'login'; document.querySelector('#register-form').hidden = action.dataset.authTab !== 'register'; }
  if (action.dataset.follow) { 
    try { 
      const isFollowing = action.dataset.following === 'true';
      const url = `profiles/${action.dataset.follow}/${isFollowing ? 'unfollow' : 'follow'}/`;
      await request(url, { method: 'POST', headers: authHeaders() });
      action.dataset.following = String(!isFollowing);
      action.textContent = isFollowing ? 'Seguir' : 'Deixar de seguir';
    } catch (error) { setMessage(error.message); } 
  }
  if (action.dataset.like) {
    try {
      const isLiked = action.dataset.liked === 'true';
      await request(`posts/${action.dataset.like}/${isLiked ? 'unlike' : 'like'}/`, { method: isLiked ? 'DELETE' : 'POST', headers: authHeaders() });
      loadTimeline();
    } catch (error) { setMessage(error.message); }
  }
  if (action.dataset.toggleComment) { const form = document.querySelector(`form[data-comment="${action.dataset.toggleComment}"]`); form.hidden = !form.hidden; }
});

document.addEventListener('submit', async event => {
  const form = event.target; event.preventDefault();
  try {
    if (form.id === 'login-form' || form.id === 'register-form') { const endpoint = form.id === 'login-form' ? 'auth/login/' : 'auth/register/'; const data = await request(endpoint, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(Object.fromEntries(new FormData(form))) }); localStorage.setItem('chirp-token', data.token); showAuth(false); updateAuthenticatedState(); }
    if (form.id === 'post-form') {
      const submitButton = form.querySelector('button[type="submit"], button:not([type])');
      submitButton.disabled = true;
      try {
        await request('posts/', { method: 'POST', headers: authHeaders(), body: JSON.stringify(Object.fromEntries(new FormData(form))) });
        form.reset();
        document.querySelector('#character-count').textContent = '0 / 280';
        setPostMessage('Postagem publicada. Ela aparece no seu perfil.');
        await loadTimeline();
      } finally {
        submitButton.disabled = false;
      }
    }
    if (form.matches('.comment-form')) { await request(`posts/${form.dataset.comment}/comments/`, { method: 'POST', headers: authHeaders(), body: JSON.stringify(Object.fromEntries(new FormData(form))) }); loadTimeline(); }
    if (form.id === 'profile-form') { const data = new FormData(form); if (!data.get('avatar').size) data.delete('avatar'); const response = await fetch(api + 'profiles/me/', {method: 'PATCH', headers: {Authorization: `Token ${token()}`}, body: data}); if (!response.ok) throw new Error('Não foi possível atualizar o perfil.'); document.querySelector('#profile-message').textContent = 'Perfil atualizado.'; }
  } catch (error) { const target = form.querySelector('.form-message') || document.querySelector('#auth-message'); if (target) target.textContent = error.message; }
});

document.querySelector('#refresh-feed')?.addEventListener('click', loadTimeline);
document.querySelector('#post-form textarea')?.addEventListener('input', event => { document.querySelector('#character-count').textContent = `${event.target.value.length} / 280`; });
document.querySelector('#logout-button')?.addEventListener('click', () => { localStorage.removeItem('chirp-token'); location.href = '/api/social/'; });
updateAuthenticatedState();
if (document.body.dataset.page === 'home') loadTimeline();
if (document.body.dataset.page === 'explore') loadExplore().catch(error => setMessage(error.message));
if (document.body.dataset.page === 'profile') loadProfilePage().catch(error => setMessage(error.message));