/** Four viewport-sized workspaces. Smaller displays page through whole panels. */
class ViewportController {
  constructor() {
    this._view = 'biomedical';
    this._pages = {};
    this._rules = [];
    this._ruleIndex = 0;
    this._ruleSection = 0;
    this._chatIndex = 0;
    this._ids = { biomedical: 'viewBiomedical', environmental: 'viewEnvironmental', matrix: 'viewMatrix', support: 'viewSupport', surgeon: 'viewSurgeon' };
  }

  initialize() {
    document.querySelectorAll('.viewport-view').forEach(view => {
      const key = Object.keys(this._ids).find(k => this._ids[k] === view.id);
      view.querySelector('.page-prev').onclick = () => this._move(key, -1);
      view.querySelector('.page-next').onclick = () => this._move(key, 1);
    });
    document.getElementById('rulePrev').onclick = () => this._moveRule(-1);
    document.getElementById('ruleNext').onclick = () => this._moveRule(1);
    document.getElementById('ruleDetailPrev').onclick = () => this._moveDetail(-1);
    document.getElementById('ruleDetailNext').onclick = () => this._moveDetail(1);
    document.getElementById('chatPrev').onclick = () => this._moveChat(-1);
    document.getElementById('chatNext').onclick = () => this._moveChat(1);
    const chat = document.getElementById('assistantChatBox');
    new MutationObserver(() => {
      this._chatIndex = Math.max(0, chat.children.length - 1);
      this._renderChat();
    }).observe(chat, { childList: true });
    new ResizeObserver(() => this.updateView(this._view)).observe(document.querySelector('.main-viewport'));
    window.addEventListener('resize', () => this.updateView(this._view));
    this.updateView(this._view);
    this._renderChat();
    this._renderRule();
  }

  _groups(key) {
    const narrow = window.innerWidth < 900;
    const compact = document.querySelector('.main-viewport').clientHeight < 590;
    const panels = {
      biomedical: ['anatomy', 'vitals', 'ecg'],
      environmental: ['habitat', 'environment', 'synergy', 'actions'],
      matrix: ['sleep', 'tasks', 'games', 'hydration'],
      support: ['assistant', 'exams', 'mail', 'rules'],
      surgeon: ['surgeon_dashboard']
    };
    if (narrow) return (key === 'support' ? ['assistant', 'protocol', 'exams', 'mail', 'rules'] : (key === 'surgeon' ? ['surgeon_dashboard'] : panels[key])).map(p => [p]);
    const compactWellness = key === 'matrix' && (window.innerWidth < 1200 || document.querySelector('.main-viewport').clientHeight < 620);
    if (compact || compactWellness || (key === 'environmental' && window.innerWidth < 1100)) return {
      biomedical: [['anatomy', 'vitals'], ['ecg']],
      environmental: [['habitat', 'environment'], ['synergy', 'actions']],
      matrix: [['sleep', 'tasks'], ['games', 'hydration']],
      support: [['assistant'], ['exams', 'mail'], ['rules']],
      surgeon: [['surgeon_dashboard']]
    }[key];
    return key === 'support' ? [['assistant', 'exams', 'mail'], ['rules']] : (key === 'surgeon' ? [['surgeon_dashboard']] : [panels[key]]);
  }

  updateView(key) {
    if (!this._ids[key]) return;
    this._view = key;
    const main = document.querySelector('.main-viewport');
    const signature = `${key}:${this._pages[key] || 0}:${window.innerWidth}:${main.clientHeight}`;
    if (signature === this._layoutSignature) return;
    this._layoutSignature = signature;
    const narrow = window.innerWidth < 900;
    if (narrow !== this._narrowAssistant) {
      this._narrowAssistant = narrow;
      const container = document.querySelector('.protocol-content');
      [['.psych-readouts', 'psychReadoutsAnchor'], ['.assistant-protocol', 'psychProtocolAnchor']].forEach(([selector, anchor]) => {
        const element = document.querySelector(selector);
        if (narrow) container.appendChild(element);
        else document.getElementById(anchor).after(element);
      });
      this._renderRule();
    }
    const view = document.getElementById(this._ids[key]);
    const groups = this._groups(key);
    const index = Math.min(this._pages[key] || 0, groups.length - 1);
    this._pages[key] = index;
    view.dataset.layout = groups[index].length === 1 ? 'single' : (groups[index].length === 2 ? 'pair' : 'full');
    view.querySelectorAll('.screen-panel').forEach(panel => {
      panel.hidden = !groups[index].includes(panel.dataset.panel);
    });
    view.querySelector('.page-label').textContent = `${index + 1} / ${groups.length}`;
    view.querySelector('.page-prev').disabled = index === 0;
    view.querySelector('.page-next').disabled = index === groups.length - 1;
    view.querySelector('.pager-controls').hidden = groups.length === 1;
    requestAnimationFrame(() => window.dispatchEvent(new Event('helios:layout')));
  }

  _move(key, step) {
    this._pages[key] = Math.max(0, Math.min(this._groups(key).length - 1, (this._pages[key] || 0) + step));
    this.updateView(key);
  }

  showRules() {
    window.hudController.changeView('support');
    this._pages.support = this._groups('support').findIndex(g => g.includes('rules'));
    this.updateView('support');
  }

  showAssistant() {
    this._pages.support = 0;
    this.updateView('support');
  }

  setRules(rules) {
    this._rules = rules;
    this._ruleIndex = Math.min(this._ruleIndex, Math.max(0, rules.length - 1));
    this._renderRule();
  }

  _moveRule(step) {
    this._ruleIndex = Math.max(0, Math.min(this._rules.length - 1, this._ruleIndex + step));
    this._ruleSection = 0;
    this._renderRule();
  }

  _moveDetail(step) {
    this._ruleSection = Math.max(0, Math.min(2, this._ruleSection + step));
    this._renderRule();
  }

  _renderRule() {
    const target = document.getElementById('ruleDetail');
    target.replaceChildren();
    const rule = this._rules[this._ruleIndex];
    const narrow = window.innerWidth < 900;
    document.querySelector('.rule-detail-navigation').hidden = !narrow || !rule;
    document.getElementById('ruleDetailPosition').textContent = `Detail ${this._ruleSection + 1} / 3`;
    document.getElementById('ruleDetailPrev').disabled = this._ruleSection === 0;
    document.getElementById('ruleDetailNext').disabled = this._ruleSection === 2;
    document.getElementById('rulePosition').textContent = rule ? `${this._ruleIndex + 1} / ${this._rules.length}` : 'No data';
    document.getElementById('rulePrev').disabled = this._ruleIndex === 0;
    document.getElementById('ruleNext').disabled = !rule || this._ruleIndex === this._rules.length - 1;
    if (!rule) {
      target.textContent = 'Catalog unavailable. It will load once the link is restored.';
      return;
    }
    const fields = [
      ['Rule / level', `${rule.rule_id} · ${rule.level}`], ['Domain', rule.domain],
      ['Preliminary assessment', rule.preliminary_assessment],
      ['Prioritized countermeasures', rule.countermeasures.join(' · ')],
      ['Recipients', rule.recipients.join(', ')], ['Evidence base', rule.evidence_base]
    ];
    (narrow ? fields.slice(this._ruleSection * 2, this._ruleSection * 2 + 2) : fields).forEach(([label, value]) => {
      const item = document.createElement('div');
      const title = document.createElement('strong');
      const text = document.createElement('p');
      title.textContent = label;
      text.textContent = value;
      item.append(title, text);
      target.appendChild(item);
    });
  }

  _moveChat(step) {
    const count = document.getElementById('assistantChatBox').children.length;
    this._chatIndex = Math.max(0, Math.min(count - 1, this._chatIndex + step));
    this._renderChat();
  }

  _renderChat() {
    const messages = Array.from(document.getElementById('assistantChatBox').children);
    messages.forEach((message, index) => { message.hidden = index !== this._chatIndex; });
    document.getElementById('chatPosition').textContent = `${messages.length ? this._chatIndex + 1 : 0} / ${messages.length}`;
    document.getElementById('chatPrev').disabled = this._chatIndex === 0;
    document.getElementById('chatNext').disabled = this._chatIndex >= messages.length - 1;
  }
}

window.ViewportController = ViewportController;
