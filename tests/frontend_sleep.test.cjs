const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const context = { window: {} };
vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../frontend/js/controllers/sleep_controller.js'), 'utf8'), context);
const Sleep = context.window.SleepController;

test('demo phases conserve total sleep and time in bed for short and long nights', () => {
  for (const hours of [0, .1, 1.25, 5.6, 7.2, 7.6, 8, 8.2, 12, 24]) {
    const profile = Sleep.perfil(hours);
    const total = profile.segments.reduce((sum, phase) => sum + phase.duration, 0);
    const asleep = profile.segments.filter(phase => phase.type !== 'awake').reduce((sum, phase) => sum + phase.duration, 0);
    assert.equal(asleep, Math.round(hours * 60));
    assert.equal(total, profile.inBed);
    assert.equal(profile.inBed - asleep, hours ? 24 : 0);
    assert(profile.segments.every(phase => phase.duration > 0));
  }
});

test('night clock wraps at midnight and minutes remain readable', () => {
  assert.equal(Sleep.horario(1390), '23:10');
  assert.equal(Sleep.horario(1390 + 456), '06:46');
  assert.equal(Sleep.formato(432), '7 h 12 min');
  assert.equal(Sleep.formato(480), '8 h 00 min');
});
