/** Sleep presentation: duration from simulator state, explicitly labelled demo profiles. */
class SleepController {
  constructor(stateManager) {
    this._state = stateManager;
    this._selected = 6;
    this._tab = 'summary';
    this._hours = [6.8, 7.6, 5.6, 7.8, 6.5, 8.2, 7.2];
    this._days = ['M', 'T', 'W', 'T', 'F', 'S', 'S'];
    this._names = { awake: 'Awake', rem: 'REM', light: 'Light', deep: 'Deep' };
  }

  initialize() {
    document.querySelectorAll('[data-sleep-tab]').forEach(button => {
      button.onclick = () => { this._tab = button.dataset.sleepTab; this._renderTabs(); };
    });
    this._state.subscribe(state => {
      const hours = state.telemetry.physiology.last_cycle_sleep_hours;
      const value = typeof hours === 'number' && Number.isFinite(hours) && hours >= 0 && hours <= 24 ? hours : null;
      if (this._hours[6] === value && this._rendered) return;
      this._hours[6] = value;
      this.render();
    });
    this._renderTabs();
    window.addEventListener('resize', () => this.render());
  }

  static format(minutes) {
    return `${Math.floor(minutes / 60)} h ${String(minutes % 60).padStart(2, '0')} min`;
  }

  static clockTime(minutes) {
    const day = ((minutes % 1440) + 1440) % 1440;
    return `${String(Math.floor(day / 60)).padStart(2, '0')}:${String(day % 60).padStart(2, '0')}`;
  }

  /** Construct a demo night whose phase totals exactly match the selected duration. */
  static profile(hours) {
    const asleep = Math.round(hours * 60);
    const totals = { deep: Math.round(asleep * .24), rem: Math.round(asleep * .24) };
    totals.light = asleep - totals.deep - totals.rem;
    totals.awake = asleep ? 24 : 0;
    const sequence = ['light', 'deep', 'light', 'rem', 'awake', 'light', 'deep', 'light', 'rem', 'light', 'awake', 'deep', 'light', 'rem', 'light', 'awake', 'deep', 'light', 'rem'];
    const counts = Object.fromEntries(Object.keys(totals).map(type => [type, sequence.filter(s => s === type).length]));
    const remaining = { ...totals };
    const segments = sequence.map(type => {
      const duration = Math.round(remaining[type] / counts[type]);
      remaining[type] -= duration;
      counts[type]--;
      return { type, duration };
    }).filter(segment => segment.duration > 0);
    return { asleep, totals, segments, inBed: asleep + totals.awake, start: 1390 };
  }

  _text(id, value) { document.getElementById(id).textContent = value; }

  render() {
    this._rendered = true;
    const hours = this._hours[this._selected];
    const missing = hours === null;
    const profile = SleepController.profile(hours || 0);
    const score = Math.min(100, Math.round((hours || 0) / 8 * 100));
    this._text('sleepScore', missing ? '—' : `${score}%`);
    document.getElementById('sleepGaugeArc').style.strokeDasharray = `${score} 100`;
    this._text('sleepSource', this._selected === 6 ? 'CURRENT CYCLE · SIMULATOR' : 'HISTORICAL CYCLE · DEMONSTRATION');
    this._text('sleepCycleLabel', this._selected === 6 ? 'LAST CYCLE' : `CYCLE ${this._selected + 1} · DEMO HISTORY`);
    this._text('sleepTotalHeadline', missing ? 'No data' : SleepController.format(profile.asleep));
    this._text('sleepTotal', missing ? '—' : SleepController.format(profile.asleep));
    this._text('sleepInBed', missing ? '—' : SleepController.format(profile.inBed));
    this._text('sleepStart', profile.asleep ? SleepController.clockTime(profile.start) : '—');
    this._text('sleepEnd', profile.asleep ? SleepController.clockTime(profile.start + profile.inBed) : '—');
    const deficit = Math.max(0, 480 - profile.asleep);
    this._text('sleepGoalStatus', missing ? 'Waiting for the cycle duration' : (deficit ? `${deficit < 60 ? `${deficit} min` : SleepController.format(deficit)} to the goal` : 'Duration goal met'));
    const previous = this._hours[this._selected - 1];
    const delta = previous == null || missing ? null : profile.asleep - Math.round(previous * 60);
    this._text('sleepTrend', delta === null ? 'Start of the demonstration history' : `${delta > 0 ? '+' : delta < 0 ? '−' : ''}${SleepController.format(Math.abs(delta))} against the previous cycle · demo`);
    this._renderPhases(profile);
    this._renderHistory();
  }

  _renderPhases(profile) {
    const legend = document.getElementById('sleepPhaseLegend');
    legend.replaceChildren();
    ['awake', 'rem', 'light', 'deep'].forEach(type => {
      const item = document.createElement('span');
      item.className = `sleep-phase-key phase-${type}`;
      const percent = profile.inBed ? Math.round(profile.totals[type] / profile.inBed * 100) : 0;
      item.textContent = `${this._names[type]} · ${profile.totals[type]} min · ${percent}%`;
      legend.appendChild(item);
    });
    const chart = document.getElementById('sleepHypnogram');
    chart.replaceChildren();
    const compact = window.innerWidth < 900;
    const startX = compact ? 60 : 68;
    const plotWidth = compact ? 290 : 540;
    chart.setAttribute('viewBox', compact ? '0 0 360 146' : '0 0 620 146');
    const svg = (tag, attrs, text) => {
      const element = document.createElementNS('http://www.w3.org/2000/svg', tag);
      Object.entries(attrs).forEach(([name, value]) => element.setAttribute(name, value));
      if (text) element.textContent = text;
      chart.appendChild(element);
      return element;
    };
    const rows = { awake: 14, rem: 40, light: 66, deep: 92 };
    Object.entries(rows).forEach(([type, y]) => {
      svg('text', { x: 0, y: y + 12, class: 'sleep-axis' }, this._names[type]);
      svg('line', { x1: startX, y1: y + 18, x2: startX + plotWidth, y2: y + 18, class: 'sleep-chart-grid' });
    });
    let offset = 0;
    profile.segments.forEach((segment, index) => {
      const x = startX + offset / profile.inBed * plotWidth;
      const width = segment.duration / profile.inBed * plotWidth;
      const label = `${SleepController.clockTime(profile.start + offset)}–${SleepController.clockTime(profile.start + offset + segment.duration)} · ${this._names[segment.type]} · ${segment.duration} min · demonstration`;
      const rect = svg('rect', { x, y: rows[segment.type], width: Math.max(.5, width - 1), height: 19, rx: Math.min(4, width / 3), class: `sleep-phase-block phase-${segment.type}`, tabindex: 0, role: 'button', 'aria-label': label });
      const select = () => {
        chart.querySelectorAll('[aria-pressed]').forEach(el => el.setAttribute('aria-pressed', 'false'));
        rect.setAttribute('aria-pressed', 'true');
        this._text('sleepPhaseDetail', label);
      };
      rect.setAttribute('aria-pressed', 'false');
      rect.onclick = select;
      rect.onfocus = select;
      rect.onkeydown = event => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); select(); } };
      if (index < profile.segments.length - 1) svg('line', { x1: x + width, x2: x + width, y1: rows[segment.type] + 9, y2: rows[profile.segments[index + 1].type] + 9, class: 'sleep-phase-connector' });
      offset += segment.duration;
    });
    if (profile.inBed) [0, .25, .5, .75, 1].forEach(part => svg('text', { x: startX + part * plotWidth, y: 136, 'text-anchor': part === 0 ? 'start' : part === 1 ? 'end' : 'middle', class: 'sleep-axis' }, SleepController.clockTime(profile.start + Math.round(profile.inBed * part))));
    this._text('sleepPhaseDetail', profile.asleep ? 'Select a segment to check its schedule · demonstration phases.' : 'No duration available to represent the phases.');
  }

  _renderHistory() {
    const history = document.getElementById('sleepHistoryDays');
    history.replaceChildren();
    this._hours.forEach((hours, index) => {
      const button = document.createElement('button');
      const minutes = hours === null ? null : Math.round(hours * 60);
      button.type = 'button';
      button.className = 'sleep-day-button';
      button.setAttribute('aria-pressed', String(index === this._selected));
      button.setAttribute('aria-label', `Cycle ${index + 1}, ${minutes === null ? 'no data' : SleepController.format(minutes)}, ${index === 6 ? 'simulator' : 'demonstration'}`);
      button.style.setProperty('--sleep-day-progress', `${Math.min(100, (hours || 0) / 8 * 100)}%`);
      const day = document.createElement('span'); day.textContent = this._days[index];
      const ring = document.createElement('strong'); ring.className = 'sleep-day-ring'; ring.textContent = hours === null ? '—' : `${hours.toFixed(1)}h`;
      button.append(day, ring);
      button.onclick = () => { this._selected = index; this._tab = 'summary'; this._renderTabs(); this.render(); };
      history.appendChild(button);
    });
    const available = this._hours.filter(hours => hours !== null);
    const average = available.length ? Math.round(available.reduce((sum, hours) => sum + hours * 60, 0) / available.length) : 0;
    this._text('sleepWeekAverage', `Demo average: ${SleepController.format(average)}`);
  }

  _renderTabs() {
    const panel = document.querySelector('[data-panel="sleep"]');
    panel.dataset.sleepTab = this._tab;
    panel.querySelectorAll('[data-sleep-tab]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.sleepTab === this._tab)));
  }
}

window.SleepController = SleepController;
