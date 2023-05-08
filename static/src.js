var request = new XMLHttpRequest();
request.open("GET", "./static/trade_links.json", false);
request.send(null);
var data = JSON.parse(request.responseText);

const formatter = new Intl.RelativeTimeFormat('en', { 
    numeric: 'auto',
    style: 'long',
    localeMatcher: 'best fit'
});
const currentDate = new Date(Date.now());
const last_update = new Date(data["time_since_last_update"] + "Z");
const diff = formatter.format(Math.round((last_update - currentDate) / 60000), 'minute');

document.getElementById('generic_link').href = data["generic_link"];
document.getElementById('mana_link').href = data["mana_link"];
document.getElementById('last_update').innerHTML = diff;
