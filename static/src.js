import data from './trade_links.json' assert { type: 'json' };
const formatter = new Intl.RelativeTimeFormat('en', { 
    numeric: 'auto',
    style: 'long',
    localeMatcher: 'best fit'
});
const last_update = new Date(data["time_since_last_update"] + " UTC");
const currentDate = new Date();
const diff = formatter.format(Math.round((last_update - currentDate) / 60000), 'minute');

document.getElementById('generic_link').href = data["generic_link"];
document.getElementById('mana_link').href = data["mana_link"];
document.getElementById('last_update').innerHTML = diff;
document.getElementById('counter').innerHTML = data["calls"];
